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
from app.core.queue import event_queue
from app.models.domain import IngestionJob, RawIndex

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@dataclass
class EventRecord:
    trace_id: str
    source_id: str
    payload: bytes
    byte_length: int

async def process_job_file(job_id: str, source_id: str, content: bytes):
    db = SessionLocal()
    try:
        lines = content.decode('utf-8', errors='ignore').splitlines()
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            trace_id = str(uuid.uuid4())
            payload = line.encode('utf-8')
            digest = hashlib.sha256(payload).hexdigest()
            
            # Mock vault: save raw payload to local disk
            vault_dir = os.path.join("vault", source_id, "batch", job_id)
            os.makedirs(vault_dir, exist_ok=True)
            vault_path = os.path.join(vault_dir, f"{trace_id}.raw")
            with open(vault_path, "wb") as f:
                f.write(payload)

            # Create RawIndex for traceability
            raw_idx = RawIndex(
                trace_id=trace_id,
                source_id=source_id,
                transport="batch_api",
                byte_length=len(payload),
                digest="sha256:" + digest,
                storage_uri=vault_path,
                received_at=datetime.utcnow()
            )
            db.add(raw_idx)
            db.commit()
            
            record = EventRecord(
                trace_id=trace_id,
                source_id=source_id,
                payload=payload,
                byte_length=len(payload)
            )
            await event_queue.publish(record)
            
        job = db.query(IngestionJob).filter(IngestionJob.id == job_id).first()
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
            "total": 100,
            "processed": 50 if job.status == "STARTED" else 100,
            "normalized": 45 if job.status == "STARTED" else 90,
            "unresolved": 5 if job.status == "STARTED" else 10,
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
