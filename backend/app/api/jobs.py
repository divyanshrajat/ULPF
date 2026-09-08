from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.core.database import get_db
from app.models.domain import IngestionJob
from typing import List, Optional
import uuid
from datetime import datetime

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.get("")
def list_jobs(
    source_id: Optional[str] = None,
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
    # Provide dummy progress details since full async tracking might not be completely modeled
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
            "failed": 0
        }
    }

@router.post("")
def create_job(
    source_id: str,
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
    
    # Normally we would dispatch this to a Celery worker or similar async task
    # For now, just return the job info
    return {"id": job.id, "status": job.status}
