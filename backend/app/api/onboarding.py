"""
onboarding.py — Onboarding session API.

Manages the full lifecycle of source onboarding:
  SOURCE_SELECTION → SOURCE_CREATED → SAMPLE_RECEIVED → RAW_PRESERVED
  → FORMAT_DETECTED → DISCOVERY_RUNNING → DISCOVERY_COMPLETE
  → FIELDS_EXTRACTED → TYPES_INFERRED → MAPPING_RUNNING
  → REVIEW_REQUIRED → MAPPING_APPROVED → READY → PROCESSING
  → NORMALIZED → TRACEABLE | FAILED

Every stage transition is persisted to onboarding_sessions.
The frontend reads this record — it never manufactures status.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File as FastAPIFile, Form, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db, SessionLocal
from app.core.auth import get_current_user
from app.models.domain import (
    OnboardingSession, Source, File, Template, ReviewItem,
    ProcessingStageRun, Trace, RawIndex, Mapping
)
from app.services.preservation.vault import vault
from app.services.detection.classifier import classify_format
from app.services.discovery.extraction_service import discover_and_extract
from app.services.typing.inference import infer_value_type
from app.services.mapping.semantic import semantic_mapper
from app.core.config import settings
from datetime import datetime
from typing import Optional, Dict, Any
import uuid
import hashlib
import asyncio
import logging

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])
logger = logging.getLogger(__name__)

ONBOARDING_STAGES = [
    "SOURCE_SELECTION", "SOURCE_CREATED", "SAMPLE_RECEIVED", "RAW_PRESERVED",
    "FORMAT_DETECTED", "DISCOVERY_RUNNING", "DISCOVERY_COMPLETE",
    "FIELDS_EXTRACTED", "TYPES_INFERRED", "MAPPING_RUNNING",
    "REVIEW_REQUIRED", "MAPPING_APPROVED", "READY",
    "PROCESSING", "NORMALIZED", "TRACEABLE", "FAILED",
]


def _update_stage(db: Session, session: OnboardingSession, stage: str, status: str = "STARTED", error: str = None):
    session.current_stage = stage
    session.status = status
    session.updated_at = datetime.utcnow()
    if error:
        session.error_code = "STAGE_FAILED"
        session.error_message = error
    if stage in ("TRACEABLE", "NORMALIZED"):
        session.completed_at = datetime.utcnow()
    db.commit()


@router.post("", status_code=201)
def create_session(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Create a new onboarding session for a source. file_id is optional at creation."""
    source_id = payload.get("source_id")
    if not source_id:
        raise HTTPException(status_code=400, detail={"code": "MISSING_SOURCE_ID", "message": "source_id is required", "stage": "onboarding_create", "trace_id": None, "details": {}})

    source = db.query(Source).filter(Source.source_id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail={"code": "SOURCE_NOT_FOUND", "message": f"Source '{source_id}' not found", "stage": "onboarding_create", "trace_id": None, "details": {}})

    session_id = str(uuid.uuid4())
    session = OnboardingSession(
        id=session_id,
        source_id=source_id,
        file_id=payload.get("file_id", ""),
        current_stage="SOURCE_CREATED",
        status="STARTED",
        started_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(session)
    db.commit()
    return _session_dict(session)


@router.get("")
def list_sessions(
    source_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(OnboardingSession)
    if source_id:
        q = q.filter(OnboardingSession.source_id == source_id)
    sessions = q.order_by(OnboardingSession.started_at.desc()).all()
    return [_session_dict(s) for s in sessions]


@router.get("/{session_id}")
def get_session(session_id: str, db: Session = Depends(get_db)):
    session = _get_or_404(db, session_id)
    return _session_dict(session)


@router.post("/{session_id}/sample")
async def upload_sample(
    session_id: str,
    file: UploadFile = FastAPIFile(...),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Upload a sample log for analysis (lightweight, no full persistence)."""
    session = _get_or_404(db, session_id)
    source_id = session.source_id

    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail={"code": "SAMPLE_TOO_LARGE", "message": "Sample max 10 MB", "stage": "sample_upload", "trace_id": None, "details": {}})

    _update_stage(db, session, "SAMPLE_RECEIVED")

    # Preserve raw sample in vault
    received_at = datetime.utcnow()
    digest, storage_uri = await vault.write_event(
        trace_id=f"sample-{session_id}",
        source_id=source_id,
        payload=contents,
        received_at=received_at,
    )
    _update_stage(db, session, "RAW_PRESERVED")

    # Format detection
    detection = classify_format(contents)
    _update_stage(db, session, "FORMAT_DETECTED")

    # Discovery
    _update_stage(db, session, "DISCOVERY_RUNNING")
    try:
        first_line = _first_meaningful_line(contents)
        template, candidates = discover_and_extract(db, source_id, first_line)
    except Exception as e:
        _update_stage(db, session, "FAILED", "FAILED", str(e))
        raise HTTPException(status_code=422, detail={"code": "DISCOVERY_FAILED", "message": str(e), "stage": "discovery", "trace_id": None, "details": {}})

    if not template:
        _update_stage(db, session, "FAILED", "FAILED", "No structure discovered")
        raise HTTPException(status_code=422, detail={"code": "NO_TEMPLATE", "message": "Could not discover log structure", "stage": "discovery", "trace_id": None, "details": {}})

    _update_stage(db, session, "DISCOVERY_COMPLETE")
    _update_stage(db, session, "FIELDS_EXTRACTED")

    # Type inference
    proposals = []
    for cand in candidates:
        cand.inferred_type = infer_value_type(cand.sample_values)
        props = semantic_mapper.propose_mappings(db, source_id, template.template_id, cand, template.pattern)
        if props:
            top = props[0]
            proposals.append({
                "source_field": cand.field_key,
                "position": cand.position,
                "inferred_type": cand.inferred_type,
                "sample_value": cand.sample_values[0] if cand.sample_values else None,
                "proposed_target": top.target_field,
                "confidence": top.confidence,
                "decision": top.decision,
                "signals": top.signals,
            })

    _update_stage(db, session, "TYPES_INFERRED")
    _update_stage(db, session, "MAPPING_RUNNING")

    # Determine if any field goes to review
    has_review = any(p["decision"] == "review" for p in proposals)
    next_stage = "REVIEW_REQUIRED" if has_review else "READY"
    _update_stage(db, session, next_stage)

    return {
        "session_id": session_id,
        "template_id": template.template_id,
        "pattern": template.pattern,
        "format": detection.format_name,
        "format_confidence": detection.confidence,
        "processing_path": detection.processing_path,
        "sha256": hashlib.sha256(contents).hexdigest(),
        "proposals": proposals,
        "stage": next_stage,
    }


@router.post("/{session_id}/upload")
async def upload_file_for_session(
    session_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = FastAPIFile(...),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """
    Full file upload for an onboarding session.
    Persists file, preserves raw bytes, runs discovery and creates review items.
    """
    session = _get_or_404(db, session_id)
    source_id = session.source_id

    contents = await file.read()
    if len(contents) > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail={"code": "FILE_TOO_LARGE", "message": "Maximum file size is 50 MB", "stage": "file_upload", "trace_id": None, "details": {}})

    _update_stage(db, session, "SAMPLE_RECEIVED")

    file_id = str(uuid.uuid4())
    sha256_hash = hashlib.sha256(contents).hexdigest()
    received_at = datetime.utcnow()

    # Write raw bytes to vault (write-before-transform)
    digest, storage_uri = await vault.write_event(
        trace_id=file_id,
        source_id=source_id,
        payload=contents,
        received_at=received_at,
    )
    _update_stage(db, session, "RAW_PRESERVED")

    # Format detection
    first_line = _first_meaningful_line(contents)
    detection = classify_format(first_line if first_line else contents)
    _update_stage(db, session, "FORMAT_DETECTED")

    # Persist file record
    file_record = File(
        file_id=file_id,
        source_id=source_id,
        filename=file.filename or "upload.log",
        mime_type=file.content_type,
        size=len(contents),
        sha256=sha256_hash,
        storage_uri=storage_uri,
        received_at=received_at,
        status="received",
        analysis_session_id=session_id,
        format=detection.format_name,
        created_at=received_at,
    )
    db.add(file_record)

    # Link file to session
    session.file_id = file_id
    db.commit()

    # Discovery
    _update_stage(db, session, "DISCOVERY_RUNNING")
    try:
        template, candidates = discover_and_extract(db, source_id, first_line if first_line else contents)
    except Exception as e:
        _update_stage(db, session, "FAILED", "FAILED", str(e))
        raise HTTPException(status_code=422, detail={"code": "DISCOVERY_FAILED", "message": str(e), "stage": "discovery", "trace_id": None, "details": {}})

    if not template:
        _update_stage(db, session, "FAILED", "FAILED", "No structure discovered")
        raise HTTPException(status_code=422, detail={"code": "NO_TEMPLATE", "message": "Could not discover log structure. File is preserved in vault.", "stage": "discovery", "trace_id": None, "details": {"file_id": file_id, "sha256": sha256_hash}})

    _update_stage(db, session, "DISCOVERY_COMPLETE")

    # Update file with template
    file_record.template_id = template.template_id
    db.commit()

    # Field extraction + type inference
    _update_stage(db, session, "FIELDS_EXTRACTED")
    proposals = []
    for cand in candidates:
        cand.inferred_type = infer_value_type(cand.sample_values)
        props = semantic_mapper.propose_mappings(db, source_id, template.template_id, cand, template.pattern)
        if props:
            top = props[0]
            proposals.append({
                "source_field": cand.field_key,
                "position": cand.position,
                "inferred_type": cand.inferred_type,
                "sample_value": cand.sample_values[0] if cand.sample_values else None,
                "proposed_target": top.target_field,
                "confidence": top.confidence,
                "decision": top.decision,
                "signals": top.signals,
            })

    _update_stage(db, session, "TYPES_INFERRED")
    _update_stage(db, session, "MAPPING_RUNNING")

    # Check existing approved mapping (fast path?)
    active_mapping = db.query(Mapping).filter(
        Mapping.source_id == source_id,
        Mapping.template_id == template.template_id,
        Mapping.status == "active",
    ).first()

    needs_review = not active_mapping and any(
        p["decision"] in ("review", "extension_only") for p in proposals
    )

    if needs_review:
        # Create review item if not already pending
        existing_review = db.query(ReviewItem).filter(
            ReviewItem.source_id == source_id,
            ReviewItem.template_id == template.template_id,
            ReviewItem.status == "PENDING",
        ).first()
        if not existing_review:
            high_conf = max((p["confidence"] for p in proposals), default=0.0)
            review = ReviewItem(
                review_id=str(uuid.uuid4()),
                source_id=source_id,
                template_id=template.template_id,
                pattern=template.pattern,
                proposals=proposals,
                confidence=high_conf,
                confidence_components={},
                reason="Semantic mapping requires human review",
                status="PENDING",
                created_at=datetime.utcnow(),
            )
            db.add(review)
            db.commit()

        _update_stage(db, session, "REVIEW_REQUIRED")
    else:
        _update_stage(db, session, "READY")

    return {
        "session_id": session_id,
        "file_id": file_id,
        "source_id": source_id,
        "filename": file.filename,
        "size": len(contents),
        "sha256": sha256_hash,
        "template_id": template.template_id,
        "pattern": template.pattern,
        "format": detection.format_name,
        "format_confidence": detection.confidence,
        "processing_path": "fast" if active_mapping else "adaptive",
        "proposals": proposals,
        "stage": session.current_stage,
        "fast_path_available": active_mapping is not None,
    }


@router.post("/{session_id}/analyze")
async def analyze_session(session_id: str, db: Session = Depends(get_db)):
    """Re-run analysis on the attached file."""
    session = _get_or_404(db, session_id)
    if not session.file_id:
        raise HTTPException(status_code=400, detail={"code": "NO_FILE", "message": "No file attached to this session", "stage": "analyze", "trace_id": None, "details": {}})
    return {"session_id": session_id, "status": session.current_stage, "message": "Analysis already completed during upload. Check session stage."}


@router.post("/{session_id}/process")
async def process_session(
    session_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Trigger full processing of the session's file."""
    from app.core.queue import event_queue
    from app.schemas.domain import IngestRecord
    from app.services.preservation.vault import vault as _vault

    session = _get_or_404(db, session_id)
    if not session.file_id:
        raise HTTPException(status_code=400, detail={"code": "NO_FILE", "message": "No file attached", "stage": "process", "trace_id": None, "details": {}})

    file_rec = db.query(File).filter(File.file_id == session.file_id).first()
    if not file_rec or not file_rec.storage_uri:
        raise HTTPException(status_code=422, detail={"code": "FILE_NOT_PRESERVED", "message": "Raw file not in vault", "stage": "process", "trace_id": None, "details": {}})

    # Read raw bytes from vault
    try:
        raw_bytes = await _vault.read_event(file_rec.source_id, file_rec.received_at, session.file_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail={"code": "VAULT_READ_FAILED", "message": str(e), "stage": "process", "trace_id": None, "details": {}})

    # Process each line as an event
    lines = [l for l in raw_bytes.split(b"\n") if l.strip()]
    if not lines:
        lines = [raw_bytes]

    from app.services.ingestion.gateway import process_ingestion
    trace_ids = []
    for line in lines[:100]:  # Limit to 100 lines for MVP
        tid = await process_ingestion(
            db=db,
            source_id=session.source_id,
            payload=line,
            transport="onboarding_upload",
            peer=None,
            file_id=session.file_id,
        )
        trace_ids.append(tid)

    # Update file trace_ids
    file_rec.trace_ids = trace_ids
    file_rec.status = "processed"
    _update_stage(db, session, "PROCESSING")
    db.commit()

    return {
        "session_id": session_id,
        "trace_ids": trace_ids,
        "count": len(trace_ids),
        "status": "queued_for_processing",
    }


def _get_or_404(db: Session, session_id: str) -> OnboardingSession:
    s = db.query(OnboardingSession).filter(OnboardingSession.id == session_id).first()
    if not s:
        raise HTTPException(
            status_code=404,
            detail={"code": "SESSION_NOT_FOUND", "message": f"Onboarding session '{session_id}' not found", "stage": "session_lookup", "trace_id": None, "details": {}},
        )
    return s


def _first_meaningful_line(contents: bytes) -> bytes:
    for line in contents.split(b"\n"):
        stripped = line.strip()
        if stripped:
            return stripped
    return contents[:4096]


def _session_dict(s: OnboardingSession) -> dict:
    return {
        "id": s.id,
        "source_id": s.source_id,
        "file_id": s.file_id,
        "current_stage": s.current_stage,
        "status": s.status,
        "started_at": s.started_at.isoformat() if s.started_at else None,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
        "completed_at": s.completed_at.isoformat() if s.completed_at else None,
        "error_code": s.error_code,
        "error_message": s.error_message,
        "trace_id": s.trace_id,
    }
