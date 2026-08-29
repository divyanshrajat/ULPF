"""
sources.py — Full CRUD for Source lifecycle management.

Source IDs are backend-generated: SRC-{VENDOR_PREFIX}-{SEQUENCE}
Sources are never hard-deleted; they move through lifecycle states.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.core.auth import get_current_user, require_admin
from app.models.domain import Source, Audit, File, Template, Mapping, ReviewItem
from typing import Optional, List, Dict, Any
from datetime import datetime
import re
import uuid

router = APIRouter(prefix="/sources", tags=["Sources"])


def _generate_source_id(db: Session, vendor: str, name: str) -> str:
    """
    Generate collision-safe deterministic source ID.
    Format: SRC-{NORMALIZED_PREFIX}-{SEQUENCE:03d}
    """
    raw = vendor.strip() if vendor else name.strip()
    # Keep only alphanumeric
    prefix = re.sub(r"[^A-Z0-9]", "", raw.upper())[:5] or "UNK"

    # Find the highest existing sequence for this prefix
    existing = (
        db.query(Source)
        .filter(Source.source_id.like(f"SRC-{prefix}-%"))
        .count()
    )
    seq = existing + 1
    return f"SRC-{prefix}-{seq:03d}"


@router.post("", status_code=201)
def create_source(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    name = (payload.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail={"code": "INVALID_INPUT", "message": "Source name is required", "stage": "source_creation", "trace_id": None, "details": {}})

    vendor = payload.get("vendor", "")
    product = payload.get("product", "")
    transport = payload.get("transport", "http")

    source_id = _generate_source_id(db, vendor, name)

    # Uniqueness double-check
    if db.query(Source).filter(Source.source_id == source_id).first():
        source_id = f"SRC-{re.sub(r'[^A-Z0-9]', '', (vendor or name).upper())[:4]}-{uuid.uuid4().hex[:4].upper()}"

    new_source = Source(
        source_id=source_id,
        name=name,
        vendor=vendor,
        product=product,
        transport=transport,
        format_hint=payload.get("format_hint"),
        namespace=payload.get("namespace"),
        status="active",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(new_source)

    audit = Audit(
        audit_id=str(uuid.uuid4()),
        actor=user.get("username", "anonymous"),
        action="source_created",
        subject_type="source",
        subject_id=source_id,
        before=None,
        after={"name": name, "vendor": vendor, "product": product, "transport": transport},
        occurred_at=datetime.utcnow(),
    )
    db.add(audit)
    db.commit()
    db.refresh(new_source)

    return {
        "source_id": new_source.source_id,
        "name": new_source.name,
        "vendor": new_source.vendor,
        "product": new_source.product,
        "transport": new_source.transport,
        "status": new_source.status,
        "created_at": new_source.created_at.isoformat(),
    }


@router.get("")
def list_sources(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    q = db.query(Source)
    if status:
        q = q.filter(Source.status == status)
    sources = q.all()
    return [_source_dict(s) for s in sources]


@router.get("/{source_id}")
def get_source(
    source_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    source = _get_or_404(db, source_id)
    return _source_dict(source)


@router.patch("/{source_id}")
def update_source(
    source_id: str,
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    source = _get_or_404(db, source_id)
    before = _source_dict(source)

    for field in ("name", "vendor", "product", "transport", "format_hint", "namespace", "status"):
        if field in payload:
            setattr(source, field, payload[field])
    source.updated_at = datetime.utcnow()

    db.add(Audit(
        audit_id=str(uuid.uuid4()),
        actor=user.get("username"),
        action="source_updated",
        subject_type="source",
        subject_id=source_id,
        before=before,
        after=payload,
        occurred_at=datetime.utcnow(),
    ))
    db.commit()
    db.refresh(source)
    return _source_dict(source)


@router.delete("/{source_id}", status_code=200)
def archive_source(
    source_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(require_admin),
):
    """Soft-delete: move source to ARCHIVED state, never destroy evidence."""
    source = _get_or_404(db, source_id)
    before = _source_dict(source)
    source.status = "archived"
    source.updated_at = datetime.utcnow()

    db.add(Audit(
        audit_id=str(uuid.uuid4()),
        actor=user.get("username"),
        action="source_archived",
        subject_type="source",
        subject_id=source_id,
        before=before,
        after={"status": "archived"},
        occurred_at=datetime.utcnow(),
    ))
    db.commit()
    return {"status": "archived", "source_id": source_id}


@router.get("/{source_id}/files")
def list_source_files(source_id: str, db: Session = Depends(get_db)):
    _get_or_404(db, source_id)
    files = db.query(File).filter(File.source_id == source_id).all()
    return [_file_dict(f) for f in files]


@router.get("/{source_id}/templates")
def list_source_templates(source_id: str, db: Session = Depends(get_db)):
    _get_or_404(db, source_id)
    templates = db.query(Template).filter(Template.source_id == source_id).all()
    return [
        {
            "template_id": t.template_id,
            "pattern": t.pattern,
            "occurrence_count": t.occurrence_count,
            "status": t.status,
            "first_seen": t.first_seen.isoformat() if t.first_seen else None,
        }
        for t in templates
    ]


@router.get("/{source_id}/mappings")
def list_source_mappings(source_id: str, db: Session = Depends(get_db)):
    _get_or_404(db, source_id)
    mappings = db.query(Mapping).filter(Mapping.source_id == source_id).all()
    return [_mapping_dict(m) for m in mappings]


@router.get("/{source_id}/events")
def list_source_events(
    source_id: str,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
):
    from app.models.domain import NormalizedEvent
    _get_or_404(db, source_id)
    q = db.query(NormalizedEvent).filter(NormalizedEvent.source_id == source_id)
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [_event_dict(e) for e in items],
    }


@router.get("/{source_id}/drift")
def get_source_drift(source_id: str, db: Session = Depends(get_db)):
    _get_or_404(db, source_id)
    drift_items = (
        db.query(ReviewItem)
        .filter(ReviewItem.source_id == source_id, ReviewItem.pattern.like("DRIFT:%"))
        .all()
    )
    return [_review_dict(r) for r in drift_items]


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _get_or_404(db: Session, source_id: str) -> Source:
    source = db.query(Source).filter(Source.source_id == source_id).first()
    if not source:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "SOURCE_NOT_FOUND",
                "message": f"Source '{source_id}' not found",
                "stage": "source_lookup",
                "trace_id": None,
                "details": {},
            },
        )
    return source


def _source_dict(s: Source) -> dict:
    return {
        "source_id": s.source_id,
        "name": s.name,
        "vendor": s.vendor,
        "product": s.product,
        "transport": s.transport,
        "format_hint": s.format_hint,
        "namespace": s.namespace,
        "status": s.status,
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
        "last_seen_at": s.last_seen_at.isoformat() if s.last_seen_at else None,
        "active_mapping_version": s.active_mapping_version,
        "active_schema_version": s.active_schema_version,
    }


def _file_dict(f: File) -> dict:
    return {
        "file_id": f.file_id,
        "source_id": f.source_id,
        "filename": f.filename,
        "size": f.size,
        "sha256": f.sha256,
        "format": f.format,
        "status": f.status,
        "received_at": f.received_at.isoformat() if f.received_at else None,
    }


def _mapping_dict(m: Mapping) -> dict:
    return {
        "mapping_id": m.mapping_id,
        "source_id": m.source_id,
        "template_id": m.template_id,
        "version": m.version,
        "status": m.status,
        "confidence_summary": m.confidence_summary,
        "approved_by": m.approved_by,
        "approved_at": m.approved_at.isoformat() if m.approved_at else None,
    }


def _review_dict(r: ReviewItem) -> dict:
    return {
        "review_id": r.review_id,
        "source_id": r.source_id,
        "template_id": r.template_id,
        "pattern": r.pattern,
        "status": r.status,
        "confidence": r.confidence,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


def _event_dict(e) -> dict:
    return {
        "event_id": e.event_id,
        "trace_id": e.trace_id,
        "source_id": e.source_id,
        "processing_path": e.processing_path,
        "mapping_version": e.mapping_version,
        "schema_version": e.schema_version,
        "created_at": e.created_at.isoformat() if e.created_at else None,
        "normalized_payload": e.normalized_payload,
    }
