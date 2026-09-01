"""
files.py — File persistence and retrieval API.

Every uploaded file is stored in the Raw Event Vault.
Metadata is persisted in PostgreSQL.
The browser File object is not authoritative — the backend record is.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File as FastAPIFile, Form
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.domain import File, Source, RawIndex, Trace
from app.services.preservation.vault import vault
from app.core.time import to_ist_iso
from datetime import datetime
from typing import Optional
import uuid
import hashlib

router = APIRouter(prefix="/files", tags=["Files"])


@router.post("/upload", status_code=201)
async def upload_file(
    file: UploadFile = FastAPIFile(...),
    source_id: str = Form(...),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """
    Persist a log file:
    1. Validate source exists.
    2. Read raw bytes and compute SHA-256.
    3. Write to vault (write-before-transform).
    4. Create File metadata record.
    5. Return file_id + sha256 for frontend confirmation.
    """
    # Validate source
    source = db.query(Source).filter(Source.source_id == source_id).first()
    if not source:
        raise HTTPException(
            status_code=404,
            detail={"code": "SOURCE_NOT_FOUND", "message": f"Source '{source_id}' not found", "stage": "file_upload", "trace_id": None, "details": {}},
        )

    # Size limit: 50 MB
    contents = await file.read()
    if len(contents) > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail={"code": "FILE_TOO_LARGE", "message": "Maximum file size is 50 MB", "stage": "file_upload", "trace_id": None, "details": {}})

    file_id = str(uuid.uuid4())
    sha256_hash = hashlib.sha256(contents).hexdigest()
    received_at = datetime.utcnow()

    # Write raw bytes to vault
    digest, storage_uri = await vault.write_event(
        trace_id=file_id,  # Use file_id as trace anchor for the file-level raw bytes
        source_id=source_id,
        payload=contents,
        received_at=received_at,
    )

    # Persist file metadata
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
        created_at=received_at,
    )
    db.add(file_record)

    # Update source last_seen
    source.last_seen_at = received_at
    db.commit()

    return {
        "file_id": file_id,
        "source_id": source_id,
        "filename": file_record.filename,
        "size": len(contents),
        "sha256": sha256_hash,
        "storage_uri": storage_uri,
        "status": "received",
        "received_at": to_ist_iso(received_at),
        "message": "File received and preserved in raw vault before transformation.",
    }


@router.get("")
def list_files(
    source_id: Optional[str] = None,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    q = db.query(File)
    if source_id:
        q = q.filter(File.source_id == source_id)
    files = q.order_by(File.received_at.desc()).all()
    return [_file_dict(f) for f in files]


@router.get("/{file_id}")
def get_file(file_id: str, db: Session = Depends(get_db)):
    f = _get_or_404(db, file_id)
    return _file_dict(f)


@router.get("/{file_id}/status")
def get_file_status(file_id: str, db: Session = Depends(get_db)):
    f = _get_or_404(db, file_id)
    return {
        "file_id": file_id,
        "status": f.status,
        "format": f.format,
        "template_id": f.template_id,
        "mapping_id": f.mapping_id,
        "analysis_session_id": f.analysis_session_id,
    }


@router.get("/{file_id}/events")
def list_file_events(
    file_id: str,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
):
    """List normalized events that originated from this file."""
    from app.models.domain import NormalizedEvent
    _get_or_404(db, file_id)
    # Events are linked via traces which link via file_id
    traces = db.query(Trace).filter(Trace.file_id == file_id).all()
    trace_ids = [t.trace_id for t in traces]

    q = db.query(NormalizedEvent).filter(NormalizedEvent.trace_id.in_(trace_ids))
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "event_id": e.event_id,
                "trace_id": e.trace_id,
                "processing_path": e.processing_path,
                "schema_version": e.schema_version,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in items
        ],
    }


def _get_or_404(db: Session, file_id: str) -> File:
    f = db.query(File).filter(File.file_id == file_id).first()
    if not f:
        raise HTTPException(
            status_code=404,
            detail={"code": "FILE_NOT_FOUND", "message": f"File '{file_id}' not found", "stage": "file_lookup", "trace_id": None, "details": {}},
        )
    return f


def _file_dict(f: File) -> dict:
    return {
        "file_id": f.file_id,
        "source_id": f.source_id,
        "filename": f.filename,
        "mime_type": f.mime_type,
        "size": f.size,
        "sha256": f.sha256,
        "storage_uri": f.storage_uri,
        "status": f.status,
        "format": f.format,
        "template_id": f.template_id,
        "mapping_id": f.mapping_id,
        "analysis_session_id": f.analysis_session_id,
        "trace_ids": f.trace_ids,
        "received_at": to_ist_iso(f.received_at),
        "created_at": to_ist_iso(f.created_at),
    }
