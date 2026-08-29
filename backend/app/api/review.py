from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.domain import ReviewItem
from app.services.mapping.registry import mapping_registry
from typing import Dict, Any

router = APIRouter()

@router.get("/review/queue")
async def get_review_queue(db: Session = Depends(get_db)):
    items = db.query(ReviewItem).filter(ReviewItem.status == "pending").all()
    return items

@router.post("/review/{review_id}/approve")
async def approve_review_item(
    review_id: str,
    payload: Dict[str, Any],
    db: Session = Depends(get_db)
):
    item = db.query(ReviewItem).filter(ReviewItem.review_id == review_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Review item not found")
        
    if item.status != "pending":
        raise HTTPException(status_code=400, detail="Item already processed")
        
    actor = "admin" # Mock auth
    field_bindings = payload.get("field_bindings", {})
    confidence_summary = payload.get("confidence_summary", {})
    
    mapping = mapping_registry.approve_mapping(
        db=db,
        source_id=item.source_id,
        template_id=item.template_id,
        field_bindings=field_bindings,
        confidence_summary=confidence_summary,
        actor=actor
    )
    
    item.status = "approved"
    db.commit()
    
    return {"status": "approved", "mapping_id": mapping.mapping_id, "version": mapping.version}

@router.post("/review/{review_id}/reject")
async def reject_review_item(
    review_id: str,
    db: Session = Depends(get_db)
):
    item = db.query(ReviewItem).filter(ReviewItem.review_id == review_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Review item not found")
        
    if item.status != "pending":
        raise HTTPException(status_code=400, detail="Item already processed")
        
    item.status = "rejected"
    db.commit()
    
    return {"status": "rejected"}
