"""
traces.py — Trace and Event Explorer API.

Trace IDs are generated on the backend (ULID).
The Trace Explorer frontend is powered entirely by these APIs.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.domain import (
    RawIndex, Provenance, NormalizedEvent, ProcessingStageRun,
    Trace, DeadLetter
)
from app.services.preservation.vault import vault
from app.core.time import to_ist_iso
import hashlib

router = APIRouter(tags=["Traces"])


@router.get("/traces")
def list_traces(
    source_id: str = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
):
    q = db.query(RawIndex)
    if source_id:
        q = q.filter(RawIndex.source_id == source_id)
    total = q.count()
    items = q.order_by(RawIndex.received_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [_raw_dict(r) for r in items],
    }


@router.get("/traces/{trace_id}")
def get_trace(trace_id: str, db: Session = Depends(get_db)):
    raw = db.query(RawIndex).filter(RawIndex.trace_id == trace_id).first()
    if not raw:
        raise HTTPException(status_code=404, detail={"code": "TRACE_NOT_FOUND", "message": f"Trace '{trace_id}' not found", "stage": "trace_lookup", "trace_id": trace_id, "details": {}})

    normalized = db.query(NormalizedEvent).filter(NormalizedEvent.trace_id == trace_id).first()
    dead = db.query(DeadLetter).filter(DeadLetter.trace_id == trace_id).first()

    return {
        "trace_id": trace_id,
        "source_id": raw.source_id,
        "received_at": to_ist_iso(raw.received_at),
        "transport": raw.transport,
        "byte_length": raw.byte_length,
        "sha256": raw.digest,
        "storage_uri": raw.storage_uri,
        "status": "dead_letter" if dead else ("normalized" if normalized else "pending"),
        "processing_path": normalized.processing_path if normalized else None,
        "mapping_version": normalized.mapping_version if normalized else None,
        "schema_version": normalized.schema_version if normalized else None,
    }


@router.get("/traces/{trace_id}/timeline")
def get_trace_timeline(trace_id: str, db: Session = Depends(get_db)):
    stages = (
        db.query(ProcessingStageRun)
        .filter(ProcessingStageRun.trace_id == trace_id)
        .order_by(ProcessingStageRun.started_at)
        .all()
    )
    return {
        "trace_id": trace_id,
        "stages": [
            {
                "stage": s.stage,
                "status": s.status,
                "started_at": to_ist_iso(s.started_at),
                "completed_at": to_ist_iso(s.completed_at),
                "duration_ms": s.duration_ms,
                "input_reference": s.input_reference,
                "output_reference": s.output_reference,
                "error_code": s.error_code,
                "error_message": s.error_message,
            }
            for s in stages
        ],
    }


@router.get("/traces/{trace_id}/raw")
async def get_trace_raw(trace_id: str, db: Session = Depends(get_db)):
    """Retrieve original raw bytes from vault with integrity check."""
    raw_idx = db.query(RawIndex).filter(RawIndex.trace_id == trace_id).first()
    if not raw_idx:
        raise HTTPException(status_code=404, detail={"code": "TRACE_NOT_FOUND", "message": f"Trace '{trace_id}' not found", "stage": "raw_retrieval", "trace_id": trace_id, "details": {}})

    try:
        payload = await vault.read_event(raw_idx.source_id, raw_idx.received_at, trace_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail={"code": "VAULT_READ_FAILED", "message": str(e), "stage": "raw_retrieval", "trace_id": trace_id, "details": {}})

    retrieved_digest = "sha256:" + hashlib.sha256(payload).hexdigest()
    verified = vault.verify_digest(payload, raw_idx.digest)

    return {
        "trace_id": trace_id,
        "payload": payload.decode("utf-8", errors="replace"),
        "byte_length": len(payload),
        "stored_digest": raw_idx.digest,
        "retrieved_digest": retrieved_digest,
        "verified": verified,
        "storage_uri": raw_idx.storage_uri,
    }


@router.get("/traces/{trace_id}/normalized")
def get_trace_normalized(trace_id: str, db: Session = Depends(get_db)):
    event = db.query(NormalizedEvent).filter(NormalizedEvent.trace_id == trace_id).first()
    if not event:
        dead = db.query(DeadLetter).filter(DeadLetter.trace_id == trace_id).first()
        if dead:
            raise HTTPException(status_code=422, detail={"code": "DEAD_LETTER", "message": "Event ended in dead letter", "stage": dead.stage, "trace_id": trace_id, "details": {"error_class": dead.error_class, "diagnostic": dead.diagnostic}})
        raise HTTPException(status_code=404, detail={"code": "NOT_NORMALIZED", "message": "Event not yet normalized", "stage": "normalization", "trace_id": trace_id, "details": {}})

    return {
        "event_id": event.event_id,
        "trace_id": trace_id,
        "source_id": event.source_id,
        "schema_version": event.schema_version,
        "mapping_id": event.mapping_id,
        "mapping_version": event.mapping_version,
        "processing_path": event.processing_path,
        "normalized_payload": event.normalized_payload,
        "created_at": event.created_at.isoformat() if event.created_at else None,
    }


@router.get("/traces/{trace_id}/provenance")
def get_trace_provenance(trace_id: str, db: Session = Depends(get_db)):
    provs = db.query(Provenance).filter(Provenance.trace_id == trace_id).all()
    return [_prov_dict(p) for p in provs]


@router.get("/traces/{trace_id}/integrity")
async def verify_trace_integrity(trace_id: str, db: Session = Depends(get_db)):
    """SHA-256 integrity verification for a trace."""
    raw_idx = db.query(RawIndex).filter(RawIndex.trace_id == trace_id).first()
    if not raw_idx:
        raise HTTPException(status_code=404, detail={"code": "TRACE_NOT_FOUND", "message": "Trace not found", "stage": "integrity_check", "trace_id": trace_id, "details": {}})

    try:
        payload = await vault.read_event(raw_idx.source_id, raw_idx.received_at, trace_id)
        retrieved_digest = "sha256:" + hashlib.sha256(payload).hexdigest()
        verified = vault.verify_digest(payload, raw_idx.digest)
    except Exception as e:
        return {
            "trace_id": trace_id,
            "stored_digest": raw_idx.digest,
            "retrieved_digest": None,
            "verified": False,
            "error": str(e),
        }

    return {
        "trace_id": trace_id,
        "stored_digest": raw_idx.digest,
        "retrieved_digest": retrieved_digest,
        "verified": verified,
        "verdict": "SHA-256 VERIFIED" if verified else "INTEGRITY FAILURE",
    }


# ─── Events endpoints ─────────────────────────────────────────────────────────

events_router = APIRouter(tags=["Events"])


@events_router.get("/events")
def list_events(
    source_id: str = None,
    trace_id: str = None,
    processing_path: str = None,
    from_ts: str = None,
    to_ts: str = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
):
    q = db.query(NormalizedEvent)
    if source_id:
        q = q.filter(NormalizedEvent.source_id == source_id)
    if trace_id:
        q = q.filter(NormalizedEvent.trace_id == trace_id)
    if processing_path:
        q = q.filter(NormalizedEvent.processing_path == processing_path)

    # Try OpenSearch for search, fall back to PG
    total = q.count()
    items = q.order_by(NormalizedEvent.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "search_backend": "postgresql",
        "items": [
            {
                "event_id": e.event_id,
                "trace_id": e.trace_id,
                "source_id": e.source_id,
                "processing_path": e.processing_path,
                "mapping_version": e.mapping_version,
                "schema_version": e.schema_version,
                "created_at": to_ist_iso(e.created_at),
            }
            for e in items
        ],
    }


@events_router.get("/events/{trace_id}/integrity")
async def event_integrity(trace_id: str, db: Session = Depends(get_db)):
    return await verify_trace_integrity(trace_id, db)


@events_router.get("/events/{trace_id}/provenance")
def event_provenance(trace_id: str, field_path: str = None, db: Session = Depends(get_db)):
    q = db.query(Provenance).filter(Provenance.trace_id == trace_id)
    if field_path:
        q = q.filter(Provenance.target_field == field_path)
    return [_prov_dict(p) for p in q.all()]


# ─── Provenance search ────────────────────────────────────────────────────────

provenance_router = APIRouter(tags=["Provenance"])


@provenance_router.get("/provenance/search")
def search_provenance(
    normalized_field: str = None,
    source_field: str = None,
    source_id: str = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
):
    q = db.query(Provenance)
    if normalized_field:
        q = q.filter(Provenance.target_field == normalized_field)
    if source_field:
        q = q.filter(Provenance.source_field == source_field)

    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [_prov_dict(p) for p in items],
    }


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _raw_dict(r: RawIndex) -> dict:
    return {
        "trace_id": r.trace_id,
        "source_id": r.source_id,
        "received_at": to_ist_iso(r.received_at),
        "transport": r.transport,
        "byte_length": r.byte_length,
        "sha256": r.digest,
    }


def _prov_dict(p: Provenance) -> dict:
    return {
        "trace_id": p.trace_id,
        "normalized_field": p.target_field,
        "source_field": p.source_field,
        "original_value": p.source_value,
        "normalized_value": None,  # can be computed from NormalizedEvent if needed
        "transformation": p.transformation,
        "mapping_id": p.mapping_id,
        "mapping_version": p.mapping_version,
        "schema_version": p.schema_version,
        "confidence": p.confidence,
        "decision": p.decision,
    }
