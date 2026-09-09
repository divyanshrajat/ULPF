
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.domain import NormalizedEvent, RawIndex, Trace, UnresolvedEvent

import os
import json

router = APIRouter(prefix="/events", tags=["Events"])

def get_raw_payload(storage_uri: str):
    if not storage_uri:
        return None
    try:
        if os.path.exists(storage_uri):
            with open(storage_uri, "r", encoding="utf-8") as f:
                content = f.read()
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    return content
    except Exception:
        pass
    return None

@router.get("")
def list_events(
    source_id: str | None = None,
    rule_id: str | None = None,
    processing_path: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    results = []
    
    # 1. Fetch Normalized Events
    query_norm = db.query(NormalizedEvent, RawIndex.source_id, RawIndex.storage_uri)\
        .outerjoin(Trace, NormalizedEvent.trace_id == Trace.trace_id)\
        .outerjoin(RawIndex, NormalizedEvent.trace_id == RawIndex.trace_id)
        
    if source_id:
        query_norm = query_norm.filter(NormalizedEvent.source_id == source_id)
    if rule_id:
        query_norm = query_norm.filter(NormalizedEvent.rule_id == rule_id)
    if processing_path:
        query_norm = query_norm.filter(NormalizedEvent.processing_path == processing_path)
        
    for norm, src_id, uri in query_norm.all():
        results.append({
            "id": norm.event_id,
            "created_at": norm.created_at,
            "source_id": norm.source_id or src_id,
            "rule_id": norm.rule_id,
            "processing_path": norm.processing_path,
            "trace_id": norm.trace_id,
            "normalized_payload": norm.normalized_payload,
            "raw_payload": get_raw_payload(uri)
        })

    # 2. Fetch Unresolved Events
    if not rule_id and (not processing_path or processing_path == "unresolved"):
        query_unres = db.query(UnresolvedEvent, RawIndex.source_id, RawIndex.storage_uri)\
            .outerjoin(RawIndex, UnresolvedEvent.trace_id == RawIndex.trace_id)
            
        if source_id:
            query_unres = query_unres.filter(RawIndex.source_id == source_id)
            
        for unres, src_id, uri in query_unres.all():
            results.append({
                "id": unres.id,
                "created_at": unres.created_at,
                "source_id": src_id,
                "rule_id": None,
                "processing_path": "unresolved",
                "trace_id": unres.trace_id,
                "normalized_payload": None,
                "raw_payload": get_raw_payload(uri)
            })
            
    # Sort and paginate manually for MVP
    results.sort(key=lambda x: x["created_at"], reverse=True)
    total = len(results)
    start = (page - 1) * page_size
    end = start + page_size
    
    return {
        "items": results[start:end],
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
