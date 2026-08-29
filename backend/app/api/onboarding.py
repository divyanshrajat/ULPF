from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.mapping.registry import mapping_registry
from app.services.discovery.extraction_service import discover_and_extract
from app.services.typing.inference import infer_value_type
from app.services.mapping.semantic import semantic_mapper
from typing import Dict, Any

from app.api.endpoints import router as base_router # Reuse the existing router if we merge files, but I will just append

@base_router.post("/onboarding/sample")
async def onboard_sample(
    request: Request,
    db: Session = Depends(get_db)
):
    source_id = request.headers.get("X-ULPF-Source-ID")
    body = await request.body()
    
    template, candidates = discover_and_extract(db, source_id, body)
    if not template:
        raise HTTPException(status_code=400, detail="Could not discover structure")
        
    proposals = []
    for cand in candidates:
        cand.inferred_type = infer_value_type(cand.sample_values)
        props = semantic_mapper.propose_mappings(cand, template.pattern)
        if props:
            # Send highest confidence proposal
            proposals.append({
                "source_field": cand.field_key,
                "position": cand.position,
                "inferred_type": cand.inferred_type,
                "sample_value": cand.sample_values[0] if cand.sample_values else None,
                "proposed_target": props[0].target_field,
                "confidence": props[0].confidence,
                "decision": props[0].decision,
                "signals": props[0].signals
            })
            
    return {
        "template_id": template.template_id,
        "pattern": template.pattern,
        "proposals": proposals
    }

@base_router.post("/mappings/{source_id}/{template_id}/approve")
async def approve_mapping(
    source_id: str,
    template_id: str,
    payload: Dict[str, Any],
    db: Session = Depends(get_db)
):
    actor = "admin" # Mock auth
    field_bindings = payload.get("field_bindings", {})
    confidence_summary = payload.get("confidence_summary", {})
    
    mapping = mapping_registry.approve_mapping(
        db=db,
        source_id=source_id,
        template_id=template_id,
        field_bindings=field_bindings,
        confidence_summary=confidence_summary,
        actor=actor
    )
    
    return {"status": "approved", "mapping_id": mapping.mapping_id, "version": mapping.version}
