from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.core.database import get_db
from app.models.domain import IngestionSession, RuleLock
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

router = APIRouter(prefix="/sessions", tags=["Sessions"])

@router.get("")
def list_sessions(
    source_id: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(IngestionSession)
    if source_id:
        query = query.filter(IngestionSession.source_id == source_id)
        
    total = query.count()
    sessions = query.order_by(desc(IngestionSession.started_at)).offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "items": sessions,
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get("/{session_id}")
def get_session(session_id: str, db: Session = Depends(get_db)):
    session = db.query(IngestionSession).filter(IngestionSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    rule_lock = db.query(RuleLock).filter(RuleLock.session_id == session.id).first()
    
    return {
        "id": session.id,
        "source_id": session.source_id,
        "status": session.status,
        "started_at": session.started_at,
        "ended_at": session.ended_at,
        "locked_rule": {
            "rule_version_id": rule_lock.rule_version_id if rule_lock else None,
            "locked_at": rule_lock.created_at if rule_lock else None
        }
    }

@router.post("")
def create_session(payload: Dict[str, Any], db: Session = Depends(get_db)):
    source_id = payload.get("source_id")
    if not source_id:
        raise HTTPException(status_code=400, detail="source_id required")
        
    session_id = str(uuid.uuid4())
    session = IngestionSession(
        id=session_id,
        source_id=source_id,
        status="ACTIVE",
        started_at=datetime.utcnow()
    )
    db.add(session)
    db.commit()
    return {"id": session.id, "status": session.status}

@router.post("/{session_id}/events")
def submit_events(session_id: str, events: List[str], db: Session = Depends(get_db)):
    session = db.query(IngestionSession).filter(IngestionSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    # In a real system, this would push to Kafka/Redpanda.
    # For now, return success mock response.
    return {
        "status": "ACCEPTED",
        "events_count": len(events)
    }
