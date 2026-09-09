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
from app.models.domain import IngestionJob, RawIndex, RuleLock, UnresolvedEvent, RuleVersion
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
        
        for line in lines:
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
            
            fingerprint = generate_fingerprint(line)
            is_unresolved = False
            
            if lock.status == "SAMPLING":
                active_rule = find_active_rule_by_fingerprint(db, fingerprint)
                if active_rule:
                    try:
                        parser = ParserFactory.create(active_rule.parser_type, active_rule.parser_definition, active_rule.field_mappings)
                        parsed = parser.parse(line)
                        missing = [f for f in active_rule.required_fields if f not in parsed] if active_rule.required_fields else []
                        if missing:
                            is_unresolved = True
                        else:
                            if not lock.rule_version_id:
                                lock.rule_version_id = active_rule.id
                                lock.fingerprint = fingerprint
                            lock.sample_count_seen += 1
                            if lock.sample_count_seen >= 3:
                                lock.status = "LOCKED"
                    except Exception:
                        is_unresolved = True
                else:
                    is_unresolved = True
            elif lock.status == "LOCKED":
                # Spot check 1 in 50
                if random.randint(1, 50) == 1:
                    active_rule = db.query(RuleVersion).filter(RuleVersion.id == lock.rule_version_id).first()
                    if active_rule:
                        try:
                            parser = ParserFactory.create(active_rule.parser_type, active_rule.parser_definition, active_rule.field_mappings)
                            parsed = parser.parse(line)
                            missing = [f for f in active_rule.required_fields if f not in parsed] if active_rule.required_fields else []
                            if missing:
                                is_unresolved = True
                        except Exception:
                            is_unresolved = True
                    else:
                        is_unresolved = True
                        
                    if is_unresolved:
                        lock.mismatch_count += 1
                        if lock.mismatch_count >= 5:
                            lock.status = "SAMPLING"
                            lock.sample_count_seen = 0
            
            if is_unresolved:
                unres = UnresolvedEvent(id=str(uuid.uuid4()), trace_id=trace_id, fingerprint=fingerprint, job_id=job_id)
                db.add(unres)
                if job: job.unresolved_count += 1
            else:
                if job: job.normalized_count += 1
                record = EventRecord(
                    trace_id=trace_id,
                    source_id=source_id,
                    payload=payload,
                    byte_length=len(payload)
                )
                await event_queue.publish(record)
                
            if job: job.processed_events += 1
            db.commit()
            
        if job:
            job.status = "COMPLETED"
            job.completed_at = datetime.utcnow()
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
    db: Session = Depends(get_db)
):
    query = db.query(IngestionJob)
    if source_id:
        query = query.filter(IngestionJob.source_id == source_id)
        
    total = query.count()
    jobs = query.order_by(desc(IngestionJob.started_at)).offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "items": jobs,
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get("/{job_id}")
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(IngestionJob).filter(IngestionJob.id == job_id).first()
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

@router.post("")
async def create_job(
    source_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
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
