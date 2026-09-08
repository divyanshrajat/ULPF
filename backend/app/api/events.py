from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.core.database import get_db
from app.models.domain import NormalizedEvent, Trace, RawIndex
from typing import List, Optional

router = APIRouter(prefix="/events", tags=["Events"])

@router.get("")
def list_events(
    source_id: Optional[str] = None,
    rule_id: Optional[str] = None,
    processing_path: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(NormalizedEvent)
    if source_id:
        query = query.filter(NormalizedEvent.source_id == source_id)
    if rule_id:
        query = query.filter(NormalizedEvent.rule_id == rule_id)
    if processing_path:
        query = query.filter(NormalizedEvent.processing_path == processing_path)
        
    total = query.count()
    events = query.order_by(desc(NormalizedEvent.created_at)).offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "items": events,
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get("/{event_id}")
def get_event(event_id: str, db: Session = Depends(get_db)):
    event = db.query(NormalizedEvent).filter(NormalizedEvent.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@router.get("/{event_id}/raw")
def get_event_raw(event_id: str, db: Session = Depends(get_db)):
    # Trace ID might be same as event ID
    event = db.query(NormalizedEvent).filter(NormalizedEvent.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    raw_index = db.query(RawIndex).filter(RawIndex.trace_id == event.trace_id).first()
    if not raw_index:
        raise HTTPException(status_code=404, detail="Raw evidence not found")
        
    return {
        "trace_id": raw_index.trace_id,
        "source_id": raw_index.source_id,
        "received_at": raw_index.received_at,
        "transport": raw_index.transport,
        "byte_length": raw_index.byte_length,
        "sha256": raw_index.digest,
        "storage_uri": raw_index.storage_uri,
        "raw_payload": "SIMULATED_RAW_BYTES" # Can fetch from storage backend in real implementation
    }

@router.get("/{event_id}/trace")
def get_event_trace(event_id: str, db: Session = Depends(get_db)):
    event = db.query(NormalizedEvent).filter(NormalizedEvent.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    trace = db.query(Trace).filter(Trace.trace_id == event.trace_id).first()
    if not trace:
        raise HTTPException(status_code=404, detail="Traceability record not found")
        
    raw_index = db.query(RawIndex).filter(RawIndex.trace_id == event.trace_id).first()
    
    return {
        "event_id": event.event_id,
        "raw": {
            "sha256": raw_index.digest if raw_index else None,
            "reference": raw_index.storage_uri if raw_index else None
        },
        "rule": {
            "id": trace.rule_id,
            "version": trace.rule_version,
            "hash": trace.rule_hash
        },
        "schema_version": trace.schema_version,
        "processing_mode": event.processing_path
    }
