"""
queries.py — Legacy query endpoints (kept for backward compatibility).

Most functionality has been moved to dedicated API modules.
These endpoints delegate to the new implementations.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db
from app.models.domain import Mapping, RawIndex, Provenance, DeadLetter, Source, ReviewItem, SchemaVersion, File
from app.core.opensearch import get_opensearch_client
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/mappings")
async def list_mappings(db: Session = Depends(get_db)):
    mappings = db.query(Mapping).all()
    return [
        {
            "mapping_id": m.mapping_id,
            "source_id": m.source_id,
            "template_id": m.template_id,
            "version": m.version,
            "status": m.status,
            "field_bindings": m.field_bindings,
            "confidence_summary": m.confidence_summary,
            "approved_by": m.approved_by,
            "approved_at": m.approved_at.isoformat() if m.approved_at else None,
            "superseded_by": m.superseded_by,
        }
        for m in mappings
    ]


@router.get("/deadletters")
async def list_deadletters(db: Session = Depends(get_db)):
    dl = db.query(DeadLetter).all()
    return [
        {
            "trace_id": d.trace_id,
            "source_id": d.source_id,
            "stage": d.stage,
            "error_class": d.error_class,
            "diagnostic": d.diagnostic,
            "raw_reference": d.raw_reference,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in dl
    ]


@router.get("/schemas")
async def list_schemas(db: Session = Depends(get_db)):
    schemas = db.query(SchemaVersion).all()
    return [
        {
            "schema_version": s.schema_version,
            "published_at": s.published_at.isoformat() if s.published_at else None,
            "compatibility_class": s.compatibility_class,
            "checksum": s.checksum,
            "field_count": len(s.field_definitions) if s.field_definitions else 0,
        }
        for s in schemas
    ]


@router.get("/schemas/{version}")
async def get_schema(version: str, db: Session = Depends(get_db)):
    schema = db.query(SchemaVersion).filter(SchemaVersion.schema_version == version).first()
    if not schema:
        raise HTTPException(status_code=404, detail={"code": "SCHEMA_NOT_FOUND", "message": f"Schema '{version}' not found", "stage": "schema_lookup", "trace_id": None, "details": {}})
    return {
        "schema_version": schema.schema_version,
        "published_at": schema.published_at.isoformat() if schema.published_at else None,
        "compatibility_class": schema.compatibility_class,
        "checksum": schema.checksum,
        "field_definitions": schema.field_definitions,
    }


@router.get("/schemas/{version}/fields")
async def get_schema_fields(version: str, db: Session = Depends(get_db)):
    schema = db.query(SchemaVersion).filter(SchemaVersion.schema_version == version).first()
    if not schema:
        raise HTTPException(status_code=404, detail={"code": "SCHEMA_NOT_FOUND", "message": f"Schema '{version}' not found", "stage": "schema_lookup", "trace_id": None, "details": {}})
    return schema.field_definitions or []


# ─── Review queue (legacy alias) ──────────────────────────────────────────────

@router.get("/review/queue")
async def get_review_queue(db: Session = Depends(get_db)):
    """Legacy endpoint — use /api/v1/reviews instead."""
    items = db.query(ReviewItem).filter(ReviewItem.status == "PENDING").all()
    return [
        {
            "review_id": r.review_id,
            "source_id": r.source_id,
            "template_id": r.template_id,
            "pattern": r.pattern,
            "proposals": r.proposals,
            "confidence": r.confidence,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in items
    ]
