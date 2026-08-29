"""
review.py — Review workflow API.

Every review action creates an audit event.
Human corrections are persisted (old/new targets preserved).
Approval atomically creates a Mapping version.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_user, require_approver
from app.models.domain import ReviewItem, Mapping, Audit, Source
from app.services.mapping.registry import mapping_registry
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.get("")
def list_reviews(
    source_id: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    q = db.query(ReviewItem)
    if source_id:
        q = q.filter(ReviewItem.source_id == source_id)
    if status:
        q = q.filter(ReviewItem.status == status)
    else:
        q = q.filter(ReviewItem.status == "PENDING")

    total = q.count()
    items = q.order_by(ReviewItem.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [_review_dict(r) for r in items],
    }


@router.get("/{review_id}")
def get_review(review_id: str, db: Session = Depends(get_db)):
    item = _get_or_404(db, review_id)
    return _review_dict(item)


@router.post("/{review_id}/approve")
def approve_review(
    review_id: str,
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    user: dict = Depends(require_approver),
):
    """
    Atomically:
    1. Update review status to APPROVED.
    2. Create/increment Mapping version.
    3. Emit audit event.
    """
    item = _get_or_404(db, review_id)
    _assert_pending(item)

    actor = user.get("username", "unknown")
    field_bindings = payload.get("field_bindings", {})
    confidence_summary = payload.get("confidence_summary", {})

    # Build field_bindings from proposals if not provided
    if not field_bindings and item.proposals:
        for prop in item.proposals:
            if prop.get("decision") != "extension_only":
                field_bindings[prop["source_field"]] = prop["proposed_target"]

    # Atomically create mapping version and mark review done
    mapping = mapping_registry.approve_mapping(
        db=db,
        source_id=item.source_id,
        template_id=item.template_id,
        field_bindings=field_bindings,
        confidence_summary=confidence_summary,
        actor=actor,
    )

    item.status = "APPROVED"
    item.reviewed_at = datetime.utcnow()
    item.assigned_to = actor

    # Update source active mapping version
    source = db.query(Source).filter(Source.source_id == item.source_id).first()
    if source:
        source.active_mapping_version = mapping.version
        source.updated_at = datetime.utcnow()

    db.add(Audit(
        audit_id=str(uuid.uuid4()),
        actor=actor,
        action="mapping_approved",
        subject_type="review_item",
        subject_id=review_id,
        before={"status": "PENDING"},
        after={"status": "APPROVED", "mapping_id": mapping.mapping_id, "mapping_version": mapping.version},
        occurred_at=datetime.utcnow(),
    ))
    db.commit()

    return {
        "status": "approved",
        "review_id": review_id,
        "mapping_id": mapping.mapping_id,
        "mapping_version": mapping.version,
        "actor": actor,
    }


@router.post("/{review_id}/reassign")
def reassign_review(
    review_id: str,
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    user: dict = Depends(require_approver),
):
    """
    Human correction: change a proposed target to a different one.
    old_target, new_target, reason are preserved in audit.
    The review item is updated with corrected proposals (does NOT auto-approve).
    """
    item = _get_or_404(db, review_id)
    _assert_pending(item)

    actor = user.get("username", "unknown")
    old_target = payload.get("old_target")
    new_target = payload.get("new_target")
    source_field = payload.get("source_field")
    reason = payload.get("reason", "")

    if not old_target or not new_target or not source_field:
        raise HTTPException(status_code=400, detail={"code": "MISSING_FIELDS", "message": "source_field, old_target, new_target required", "stage": "review_reassign", "trace_id": None, "details": {}})

    # Update the specific proposal in the JSONB list
    updated_proposals = []
    for prop in (item.proposals or []):
        if prop.get("source_field") == source_field and prop.get("proposed_target") == old_target:
            prop = dict(prop)
            prop["proposed_target"] = new_target
            prop["decision"] = "human_corrected"
            prop["reassigned_from"] = old_target
            prop["reassigned_by"] = actor
            prop["reassignment_reason"] = reason
        updated_proposals.append(prop)

    item.proposals = updated_proposals
    item.status = "IN_REVIEW"

    db.add(Audit(
        audit_id=str(uuid.uuid4()),
        actor=actor,
        action="mapping_reassigned",
        subject_type="review_item",
        subject_id=review_id,
        before={"proposed_target": old_target},
        after={"proposed_target": new_target, "reason": reason},
        occurred_at=datetime.utcnow(),
    ))
    db.commit()

    return {
        "status": "reassigned",
        "review_id": review_id,
        "source_field": source_field,
        "old_target": old_target,
        "new_target": new_target,
        "reason": reason,
        "actor": actor,
    }


@router.post("/{review_id}/extension")
def mark_extension_only(
    review_id: str,
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    user: dict = Depends(require_approver),
):
    """Mark a field as extension-only (no canonical mapping)."""
    item = _get_or_404(db, review_id)
    _assert_pending(item)

    actor = user.get("username", "unknown")
    source_field = payload.get("source_field")

    updated_proposals = []
    for prop in (item.proposals or []):
        if prop.get("source_field") == source_field:
            prop = dict(prop)
            prop["decision"] = "extension_only"
        updated_proposals.append(prop)

    item.proposals = updated_proposals
    item.status = "EXTENSION_ONLY"
    item.reviewed_at = datetime.utcnow()
    item.assigned_to = actor

    db.add(Audit(
        audit_id=str(uuid.uuid4()),
        actor=actor,
        action="mapping_extension_only",
        subject_type="review_item",
        subject_id=review_id,
        before={},
        after={"source_field": source_field, "decision": "extension_only"},
        occurred_at=datetime.utcnow(),
    ))
    db.commit()
    return {"status": "extension_only", "review_id": review_id}


@router.post("/{review_id}/reject")
def reject_review(
    review_id: str,
    payload: Dict[str, Any] = None,
    db: Session = Depends(get_db),
    user: dict = Depends(require_approver),
):
    item = _get_or_404(db, review_id)
    _assert_pending(item)

    actor = user.get("username", "unknown")
    item.status = "REJECTED"
    item.reviewed_at = datetime.utcnow()
    item.assigned_to = actor

    db.add(Audit(
        audit_id=str(uuid.uuid4()),
        actor=actor,
        action="mapping_rejected",
        subject_type="review_item",
        subject_id=review_id,
        before={"status": "PENDING"},
        after={"status": "REJECTED"},
        occurred_at=datetime.utcnow(),
    ))
    db.commit()
    return {"status": "rejected", "review_id": review_id}


def _get_or_404(db: Session, review_id: str) -> ReviewItem:
    item = db.query(ReviewItem).filter(ReviewItem.review_id == review_id).first()
    if not item:
        raise HTTPException(
            status_code=404,
            detail={"code": "REVIEW_NOT_FOUND", "message": f"Review item '{review_id}' not found", "stage": "review_lookup", "trace_id": None, "details": {}},
        )
    return item


def _assert_pending(item: ReviewItem):
    if item.status not in ("PENDING", "IN_REVIEW"):
        raise HTTPException(
            status_code=400,
            detail={"code": "REVIEW_ALREADY_PROCESSED", "message": f"Review item is already '{item.status}'", "stage": "review_mutation", "trace_id": None, "details": {}},
        )


def _review_dict(r: ReviewItem) -> dict:
    return {
        "review_id": r.review_id,
        "source_id": r.source_id,
        "template_id": r.template_id,
        "field_id": r.field_id,
        "pattern": r.pattern,
        "proposals": r.proposals,
        "confidence": r.confidence,
        "confidence_components": r.confidence_components,
        "reason": r.reason,
        "priority": r.priority,
        "status": r.status,
        "assigned_to": r.assigned_to,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
    }
