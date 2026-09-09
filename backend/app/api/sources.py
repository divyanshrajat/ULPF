import re
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.domain import NormalizedEvent, Source

router = APIRouter(prefix="/sources", tags=["Sources"])

def _generate_source_id(db: Session, vendor: str, name: str) -> str:
    raw = vendor.strip() if vendor else name.strip()
    prefix = re.sub(r"[^A-Z0-9]", "", raw.upper())[:5] or "UNK"
    existing = db.query(Source).filter(Source.source_id.like(f"SRC-{prefix}-%")).count()
    seq = existing + 1
    return f"SRC-{prefix}-{seq:03d}"

@router.post("", status_code=201)
def create_source(payload: dict[str, Any], db: Session = Depends(get_db)):
    name = (payload.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Source name is required")

    vendor = payload.get("vendor", "")
    source_id = _generate_source_id(db, vendor, name)

    new_source = Source(
        source_id=source_id,
        name=name,
        vendor=vendor,
        status="active",
        created_at=datetime.utcnow(),
    )
    db.add(new_source)
    db.commit()
    db.refresh(new_source)
    return {"source_id": new_source.source_id, "name": new_source.name}

@router.get("")
def list_sources(db: Session = Depends(get_db)):
    sources = db.query(Source).all()
    return [{"source_id": s.source_id, "name": s.name, "vendor": s.vendor} for s in sources]

@router.get("/{source_id}")
def get_source(source_id: str, db: Session = Depends(get_db)):
    source = db.query(Source).filter(Source.source_id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Not found")
    return {"source_id": source.source_id, "name": source.name}

@router.get("/{source_id}/events")
def list_source_events(source_id: str, page: int = 1, page_size: int = 50, db: Session = Depends(get_db)):
    q = db.query(NormalizedEvent).filter(NormalizedEvent.source_id == source_id)
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return {
        "total": total,
        "items": [
            {
                "event_id": e.event_id,
                "trace_id": e.trace_id,
                "schema_version": e.schema_version,
                "payload": e.normalized_payload
            } for e in items
        ]
    }
