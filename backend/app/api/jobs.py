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
from app.core.auth import get_current_user, require_authenticated
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
    from app.services.ingestion.gateway import process_ingestion

    try:
        lines = content.decode('utf-8', errors='ignore').splitlines()
        job = db.query(IngestionJob).filter(IngestionJob.id == job_id).first()
        if job:
            job.total_events = len([l for l in lines if l.strip()])
            db.commit()

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            payload = line.encode('utf-8')
            
            await process_ingestion(
                db=db,
                source_id=source_id,
                payload=payload,
                transport="batch_api",
                job_id=job_id
            )
            
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
    actor: dict = Depends(require_authenticated)
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
