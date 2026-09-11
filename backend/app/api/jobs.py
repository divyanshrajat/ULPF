import hashlib
import logging
import uuid
import json
import os
from dataclasses import dataclass
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, BackgroundTasks
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.database import get_db, SessionLocal
from app.core.queue import event_queue, EventRecord
from app.models.domain import IngestionJob, RawIndex, RuleLock, UnresolvedEvent, RuleVersion, Source
from app.core.auth import get_current_user
from app.services.preservation.vault import vault
from app.services.rules.fingerprint import generate_fingerprint
from app.services.rules.parsers.factory import ParserFactory
from app.services.rules.parsers.base import ParserError
from app.services.rules.registry import find_active_rule_by_fingerprint
import random

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["Jobs"])


async def process_job_file(job_id: str, source_id: str, content: bytes):
    db = SessionLocal()
    try:
        lines = content.decode('utf-8', errors='ignore').splitlines()
        job = db.query(IngestionJob).filter(IngestionJob.id == job_id).first()
        if job:
            job.total_events = len([l for l in lines if l.strip()])
            db.commit()

        lock = None
        normalized_counter = 0
        unresolved_counter = 0
        processed_counter = 0
        batch_records = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            trace_id = str(uuid.uuid4())
            payload = line.encode('utf-8')
            received_at = datetime.utcnow()
            
            # Use vault for storage
            digest_str, vault_path = await vault.write_event(
                trace_id=trace_id,
                source_id=source_id,
                payload=payload,
                received_at=received_at
            )

            # Create RawIndex for traceability
            raw_idx = RawIndex(
                trace_id=trace_id,
                source_id=source_id,
                transport="batch_api",
                byte_length=len(payload),
                digest=digest_str,
                storage_uri=vault_path,
                received_at=received_at,
                job_id=job_id
            )
            db.add(raw_idx)
            
            # Locking and spot check logic
            if lock is None:
                lock = db.query(RuleLock).filter(RuleLock.job_id == job_id).first()
                if not lock:
                    lock = RuleLock(id=str(uuid.uuid4()), job_id=job_id, status="SAMPLING")
                    db.add(lock)
            
            fingerprint = generate_fingerprint(line, vendor_token=source_id)
            is_unresolved = False
            
            if lock.status == "SAMPLING":
                active_rule = find_active_rule_by_fingerprint(db, fingerprint)
                if active_rule:
                    try:
                        parser = ParserFactory.create(active_rule.parser_type, active_rule.parser_definition, active_rule.field_mappings)
                        from app.services.rules.validator import RuleValidator, ValidationError
                        parsed = parser.parse(line)
                        try:
                            RuleValidator.validate_extracted_fields(parsed, active_rule.required_fields, active_rule.type_constraints)
                            if not lock.rule_version_id:
                                lock.rule_version_id = active_rule.id
                                lock.fingerprint = fingerprint
                            lock.sample_count_seen += 1
                            if lock.sample_count_seen >= 3:
                                lock.status = "LOCKED"
                        except ValidationError:
                            is_unresolved = True
                    except Exception:
                        is_unresolved = True
                else:
                    is_unresolved = True
            elif lock.status == "LOCKED":
                lock.events_since_lock += 1
                # Adaptive spot-check rate table (impl §7):
                #  - Just after lock (< 100 events): 1-in-50
                #  - Stable fast path (>= 100 events, no recent mismatch): 1-in-500
                #  - After a mismatch (events_since_mismatch < 50): 1-in-25
                if lock.mismatch_count > 0 and lock.events_since_mismatch < 50:
                    spot_check_rate = 25
                elif lock.events_since_lock < 100:
                    spot_check_rate = 50
                else:
                    spot_check_rate = 500
                lock.events_since_mismatch += 1

                if random.randint(1, spot_check_rate) == 1:
                    active_rule = db.query(RuleVersion).filter(RuleVersion.id == lock.rule_version_id).first()
                    if active_rule:
                        try:
                            parser = ParserFactory.create(active_rule.parser_type, active_rule.parser_definition, active_rule.field_mappings)
                            from app.services.rules.validator import RuleValidator, ValidationError
                            parsed = parser.parse(line)
                            try:
                                RuleValidator.validate_extracted_fields(parsed, active_rule.required_fields, active_rule.type_constraints)
                            except ValidationError:
                                is_unresolved = True
                        except Exception:
                            is_unresolved = True
                    else:
                        is_unresolved = True
                        
                    if is_unresolved:
                        lock.mismatch_count += 1
                        lock.events_since_mismatch = 0  # reset; rate will tighten to 1-in-25
                        if lock.mismatch_count >= 5:
                            lock.status = "SAMPLING"
                            lock.sample_count_seen = 0
                            lock.events_since_lock = 0
                            lock.events_since_mismatch = 0
            
            if is_unresolved:
                unres = UnresolvedEvent(id=str(uuid.uuid4()), trace_id=trace_id, fingerprint=fingerprint, job_id=job_id)
                db.add(unres)
                unresolved_counter += 1
            else:
                normalized_counter += 1
                record = EventRecord(
                    trace_id=trace_id,
                    source_id=source_id,
                    payload=payload,
                    byte_length=len(payload)
                )
                batch_records.append(record)
                
            processed_counter += 1
            if i % 100 == 0:
                db.commit()
                for r in batch_records:
                    await event_queue.publish(r)
                batch_records.clear()
        db.commit()
        for r in batch_records:
            await event_queue.publish(r)
            
        if job:
            job.status = "COMPLETED"
            job.completed_at = datetime.utcnow()
            job.processed_events += processed_counter
            job.normalized_count += normalized_counter
            job.unresolved_count += unresolved_counter
            db.commit()
            
    except Exception as e:
        logger.error(f"Failed to process job {job_id}: {e}", exc_info=True)
        job = db.query(IngestionJob).filter(IngestionJob.id == job_id).first()
        if job:
            job.status = "FAILED"
            db.commit()
    finally:
        db.close()

@router.get("")
def list_jobs(
    source_id: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    actor: dict = Depends(get_current_user)
):
    tenant_id = actor.get("tenant_id", "default")
    query = db.query(IngestionJob).join(Source, IngestionJob.source_id == Source.source_id).filter(Source.tenant_id == tenant_id)
    if source_id:
        query = query.filter(IngestionJob.source_id == source_id)
        
    total = query.count()
    jobs = query.order_by(desc(IngestionJob.started_at)).offset((page - 1) * page_size).limit(page_size).all()
    
    from app.models.domain import Rule, RuleVersion
    items = []
    for job in jobs:
        lock = db.query(RuleLock).filter(RuleLock.job_id == job.id).first()
        rule_name = None
        if lock and lock.rule_version_id:
            rv = db.query(RuleVersion).filter(RuleVersion.id == lock.rule_version_id).first()
            if rv:
                rule = db.query(Rule).filter(Rule.rule_id == rv.rule_id).first()
                if rule:
                    rule_name = f"{rule.name}@{rv.version}"
        
        job_dict = {
            "id": job.id,
            "source_id": job.source_id,
            "status": job.status,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
            "total_events": job.total_events,
            "processed_events": job.processed_events,
            "normalized_count": job.normalized_count,
            "unresolved_count": job.unresolved_count,
            "lock": {
                "status": lock.status,
                "sample_count_seen": lock.sample_count_seen,
                "mismatch_count": lock.mismatch_count,
                "rule_name": rule_name
            } if lock else None
        }
        items.append(job_dict)
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get("/{job_id}")
def get_job(job_id: str, db: Session = Depends(get_db), actor: dict = Depends(get_current_user)):
    tenant_id = actor.get("tenant_id", "default")
    job = db.query(IngestionJob).join(Source, IngestionJob.source_id == Source.source_id).filter(Source.tenant_id == tenant_id, IngestionJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "id": job.id,
        "source_id": job.source_id,
        "status": job.status,
        "started_at": job.started_at,
        "completed_at": job.completed_at,
        "progress": {
            "total": job.total_events,
            "processed": job.processed_events,
            "normalized": job.normalized_count,
            "unresolved": job.unresolved_count,
            "failed": 0 if job.status != "FAILED" else 100
        }
    }

from app.models.domain import Source

@router.post("")
async def create_job(
    source_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    actor: dict = Depends(get_current_user)
):
    # Verify source belongs to this tenant
    tenant_id = actor.get("tenant_id", "default")
    source = db.query(Source).filter(Source.source_id == source_id, Source.tenant_id == tenant_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    job_id = str(uuid.uuid4())
    job = IngestionJob(
        id=job_id,
        source_id=source_id,
        status="STARTED",
        started_at=datetime.utcnow()
    )
    db.add(job)
    db.commit()
    
    content = await file.read()
    background_tasks.add_task(process_job_file, job.id, source_id, content)
    
    return {"id": job.id, "status": job.status}
