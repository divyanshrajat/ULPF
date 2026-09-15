import logging
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.authoring.agent import generate_rule_from_samples
from app.core.auth import get_current_user, require_authenticated
from app.core.database import get_db
from app.models.domain import OnboardingSession, RuleVersion
from app.services.rules.fingerprint import generate_fingerprint
from app.services.rules.parsers.base import ParserError
from app.services.rules.parsers.factory import ParserFactory
from app.services.rules.registry import (
    add_fingerprint_to_rule,
    create_rule,
    create_rule_version,
    find_active_rule_by_fingerprint,
    update_rule_version_status,
)
from app.services.normalization.engine import normalization_engine
from app.authoring.agent import USE_MOCK

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])
logger = logging.getLogger(__name__)

from app.models.domain import Source

def _get_session(db: Session, session_id: str, tenant_id: str) -> OnboardingSession:
    s = db.query(OnboardingSession).join(Source, OnboardingSession.source_id == Source.source_id)\
        .filter(Source.tenant_id == tenant_id, OnboardingSession.id == session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    return s

@router.post("", status_code=201)
def create_session(payload: dict[str, Any], db: Session = Depends(get_db), user: dict = Depends(require_authenticated)):
    tenant_id = user.get("tenant_id", "default")
    source_id = payload.get("source_id")
    if not source_id:
        raise HTTPException(status_code=400, detail="source_id is required")
        
    source = db.query(Source).filter(Source.tenant_id == tenant_id, Source.source_id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail=f"Source '{source_id}' does not exist. Create it first via POST /sources.")
        
    session_id = str(uuid.uuid4())
    session = OnboardingSession(
        id=session_id,
        source_id=source_id,
        status="STARTED",
    )
    db.add(session)
    db.commit()
    return {"session_id": session.id, "status": session.status}

@router.post("/{session_id}/samples")
def upload_samples(session_id: str, samples: list[str], target_schema: str = None, db: Session = Depends(get_db), user: dict = Depends(require_authenticated)):
    tenant_id = user.get("tenant_id", "default")
    session = _get_session(db, session_id, tenant_id)
    if not samples or len(samples) < 1 or len(samples) > 5:
        raise HTTPException(status_code=400, detail="Between 1 and 5 samples are required")
        
    fingerprint = generate_fingerprint(samples[0], vendor_token=session.source_id)
    session.fingerprint = fingerprint
    
    active_rule = find_active_rule_by_fingerprint(db, fingerprint)
    
    if active_rule and target_schema and active_rule.target_schema != target_schema:
        active_rule = None
    
    session.status = "SAMPLES_RECEIVED"
    db.commit()
    
    return {
        "fingerprint": fingerprint,
        "active_rule_found": active_rule is not None,
        "active_rule_id": active_rule.rule_id if active_rule else None
    }

@router.post("/{session_id}/draft")
def generate_draft_rule(session_id: str, samples: list[str], target_schema: str = "ocsf", db: Session = Depends(get_db), user: dict = Depends(require_authenticated)):
    tenant_id = user.get("tenant_id", "default")
    session = _get_session(db, session_id, tenant_id)
    if not samples or len(samples) < 1 or len(samples) > 5:
        raise HTTPException(status_code=400, detail="Between 1 and 5 samples are required")

    if not session.fingerprint:
        session.fingerprint = generate_fingerprint(samples[0], vendor_token=session.source_id)
        
    import json
    from app.models.domain import RuleLLMGeneration
    
    MAX_ATTEMPTS = 3
    attempt = 0
    previous_errors = None
    previous_json = None
    rule_json = None
    
    successful_llm_gen = None
    
    while attempt < MAX_ATTEMPTS:
        attempt += 1
        prompt = ""
        raw_response = ""
        try:
            rule_json, prompt, raw_response = generate_rule_from_samples(
                samples, 
                previous_errors=previous_errors, 
                previous_json=previous_json
            )
            
            # Ensure the requested target schema is respected
            rule_json["target_schema"] = target_schema
            
            # Fast-path validation
            parser_type = rule_json.get("parser", {}).get("type", "regex")
            parser_def = rule_json.get("parser", {})
            mappings = rule_json.get("field_mappings", {})
            req_fields = rule_json.get("required_fields", [])
            type_constraints = rule_json.get("type_constraints", {})
            
            from app.services.rules.validator import RuleValidator, ValidationError
            
            parser = ParserFactory.create(parser_type, parser_def, mappings)
            validation_errors = []
            for s in samples:
                extracted = parser.parse(s)
                try:
                    RuleValidator.validate_extracted_fields(extracted, req_fields, type_constraints)
                except ValidationError as ve:
                    validation_errors.append(f"Sample validation failed: {ve}")
            
            if validation_errors:
                raise ParserError("; ".join(validation_errors))
                
            from app.services.rules.safety import validate_rule_definition
            import json
            try:
                validate_rule_definition(json.dumps(rule_json))
            except ValueError as e:
                raise ParserError(f"Safety validation failed: {e}")
                
            # If we get here, validation passed!
            successful_llm_gen = RuleLLMGeneration(
                id=str(uuid.uuid4()),
                prompt=prompt,
                response_json=raw_response,
                success=True
            )
            db.add(successful_llm_gen)
            break
            
        except ParserError as pe:
            previous_errors = str(pe)
            previous_json = json.dumps(rule_json, indent=2) if rule_json else "{}"
            llm_gen = RuleLLMGeneration(
                id=str(uuid.uuid4()),
                prompt=prompt,
                response_json=raw_response,
                success=False,
                error_message=str(pe)
            )
            db.add(llm_gen)
            if attempt == MAX_ATTEMPTS:
                db.commit() # Save the failed attempts
                logger.error(f"LLM Generation failed after {MAX_ATTEMPTS} attempts: {pe}")
                raise HTTPException(status_code=500, detail=f"LLM generation failed after {MAX_ATTEMPTS} attempts: {pe}")
                
        except Exception as e:
            logger.error(f"LLM Generation unexpected error: {e}")
            llm_gen = RuleLLMGeneration(
                id=str(uuid.uuid4()),
                prompt=prompt,
                response_json=raw_response,
                success=False,
                error_message=str(e)
            )
            db.add(llm_gen)
            if attempt == MAX_ATTEMPTS:
                db.commit() # Save the failed attempts
                raise HTTPException(status_code=500, detail=f"LLM generation failed: {e}")
            previous_errors = str(e)
            previous_json = "{}"
        
    # Create rule and version
    rule_name = f"AutoRule-{session.source_id}-{datetime.utcnow().strftime('%Y%m%d')}"
    rule = create_rule(db, rule_name, "Generated by Local LLM")
    
    version = create_rule_version(
        db=db,
        rule_id=rule.rule_id,
        parser_type=rule_json.get("parser", {}).get("type", "regex"),
        parser_definition=rule_json.get("parser", {}),
        field_mappings=rule_json.get("field_mappings", {}),
        required_fields=rule_json.get("required_fields", []),
        type_constraints=rule_json.get("type_constraints", {}),
        target_schema=rule_json.get("target_schema", "ocsf"),
        schema_version=rule_json.get("schema_version", "1.0"),
    )
    
    if successful_llm_gen:
        successful_llm_gen.rule_version_id = version.id
        
    add_fingerprint_to_rule(db, rule.rule_id, session.fingerprint)
    
    session.rule_id = rule.rule_id
    session.status = "DRAFT_CREATED"
    db.commit()
    
    return {
        "rule_id": rule.rule_id,
        "version": version.id,
        "rule_json": rule_json,
        "llm_mode": "mock" if USE_MOCK else "local_llm"
    }

@router.post("/{session_id}/validate")
async def validate_rule(session_id: str, payload: dict[str, Any], db: Session = Depends(get_db), user: dict = Depends(require_authenticated)):
    """Validates the rule against the samples to ensure it extracts fields correctly and deterministically"""
    tenant_id = user.get("tenant_id", "default")
    session = _get_session(db, session_id, tenant_id)
    rule_version_id = payload.get("rule_version_id")
    samples = payload.get("samples", [])
    
    version = db.query(RuleVersion).filter(RuleVersion.id == rule_version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Rule version not found")
        
    if "field_mappings" in payload:
        version.field_mappings = payload["field_mappings"]
        db.commit()
        db.refresh(version)
        
    if not session.rule_id:
        session.rule_id = version.rule_id
        db.commit()
        
    results = []
    passed = True
    
    try:
        parser = ParserFactory.create(version.parser_type, version.parser_definition, version.field_mappings)
        from app.services.rules.validator import RuleValidator, ValidationError
        
        for s in samples:
            import uuid
            from datetime import datetime
            from app.models.domain import RawIndex, UnresolvedEvent, Trace, NormalizedEvent, Provenance
            from app.services.preservation.vault import vault
            
            trace_id = "test-" + str(uuid.uuid4())
            received_at = datetime.utcnow()
            payload = s.encode('utf-8')
            
            try:
                extracted = parser.parse(s)
                try:
                    RuleValidator.validate_extracted_fields(extracted, version.required_fields, version.type_constraints)
                except ValidationError as ve:
                    passed = False
                    results.append({"sample": s, "extracted": extracted, "error": str(ve)})
                else:
                    normalized_dict, provenance_records = normalization_engine.normalize(
                        db=db,
                        parsed_data=extracted,
                        source_id=session.source_id,
                        template_id=rule_version_id,
                        trace_id=trace_id,
                        raw_ref={}
                    )
                    
                    # Persist to database so they appear in Log Review
                    raw_idx = RawIndex(
                        trace_id=trace_id,
                        source_id=session.source_id,
                        transport="studio",
                        byte_length=len(payload),
                        digest="sha256:studio",
                        storage_uri=f"vault://studio/{trace_id}"
                    )
                    db.add(raw_idx)
                    
                    trace_record = Trace(
                        trace_id=trace_id,
                        source_id=session.source_id,
                        rule_id=version.rule_id,
                        rule_version=version.version,
                        rule_hash=version.rule_hash,
                        schema_version=version.schema_version
                    )
                    db.add(trace_record)
                    db.flush() # Force insert of Trace before NormalizedEvent references it
                    
                    ne = NormalizedEvent(
                        event_id=str(uuid.uuid4()),
                        trace_id=trace_id,
                        source_id=session.source_id,
                        schema_version=version.schema_version,
                        rule_id=version.rule_id,
                        rule_version=version.version,
                        processing_path="onboarding",
                        normalized_payload=normalized_dict,
                        created_at=datetime.utcnow()
                    )
                    db.add(ne)
                    
                    for pr in provenance_records:
                        p = Provenance(
                            trace_id=pr.trace_id,
                            target_field=pr.target_field,
                            source_field=pr.source_field,
                            source_value=pr.source_value,
                            transformation=pr.transformation,
                            decision=pr.decision,
                            created_at=datetime.utcnow()
                        )
                        db.add(p)
                        
                    try:
                        from app.core.opensearch import get_opensearch_client, index_event
                        from app.core.time import to_ist_iso
                        os_client = get_opensearch_client()
                        event_dict_os = normalized_dict.copy()
                        event_dict_os["trace_id"] = trace_id
                        event_dict_os["source_id"] = session.source_id
                        event_dict_os["processing_path"] = "onboarding"
                        event_dict_os["@timestamp"] = to_ist_iso()
                        index_event(os_client, event_dict_os)
                    except Exception as e:
                        logger.error(f"Failed to index studio log to opensearch: {e}")
                    
                    results.append({
                        "sample": s, 
                        "extracted": extracted, 
                        "normalized_payload": normalized_dict, 
                        "provenance": [pr.dict() for pr in provenance_records],
                        "status": "ok"
                    })
            except ParserError as e:
                passed = False
                results.append({"sample": s, "error": str(e)})
    except Exception as e:
        passed = False
        results.append({"error": str(e)})
        
    if passed:
        update_rule_version_status(db, version.id, "PENDING_REVIEW", "system_validator")
        session.status = "VALIDATION_PASSED"
        
        from app.models.domain import RuleTestCase
        for res in results:
            if "sample" in res and "extracted" in res:
                test_case = RuleTestCase(
                    id=str(uuid.uuid4()),
                    rule_version_id=version.id,
                    raw_sample=res["sample"],
                    expected_output=res["extracted"]
                )
                db.add(test_case)
    else:
        session.status = "VALIDATION_FAILED"
        
    db.commit()
    return {"passed": passed, "results": results, "status": session.status}

from fastapi import BackgroundTasks

from app.core.auth import get_current_user, require_approver

@router.post("/{session_id}/approve")
async def approve_rule(session_id: str, payload: dict[str, Any], background_tasks: BackgroundTasks, db: Session = Depends(get_db), user: dict = Depends(require_approver)):
    tenant_id = user.get("tenant_id", "default")
    session = _get_session(db, session_id, tenant_id)
    rule_version_id = payload.get("rule_version_id")
    
    if session.status != "VALIDATION_PASSED":
        raise HTTPException(status_code=400, detail="Cannot approve rule before validation passes")
        
    version = db.query(RuleVersion).filter(RuleVersion.id == rule_version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Rule version not found")
        
    if version.status != "PENDING_REVIEW":
        raise HTTPException(status_code=400, detail=f"Cannot approve rule in status: {version.status}")
        
    from app.services.rules.safety import validate_rule_definition
    import json
    try:
        rule_def_json = json.dumps(version.parser_definition)
        validate_rule_definition(rule_def_json)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Rule safety validation failed: {e}")
        
    update_rule_version_status(db, version.id, "ACTIVE", "human_reviewer")
    
    from app.models.domain import RuleApproval
    approval = RuleApproval(
        id=str(uuid.uuid4()),
        rule_version_id=version.id,
        reviewer="human_reviewer",
        decision="APPROVED",
        comments=payload.get("comments")
    )
    db.add(approval)
    
    session.status = "COMPLETED"
    db.commit()
    
    from app.services.ingestion.reprocessor import republish_unresolved_events
    background_tasks.add_task(republish_unresolved_events, rule_id=version.rule_id, fingerprint=session.fingerprint)
        
    return {"status": "APPROVED", "rule_id": version.rule_id, "version": version.version}

@router.post("/{session_id}/reject")
async def reject_rule(session_id: str, payload: dict[str, Any], db: Session = Depends(get_db), user: dict = Depends(require_approver)):
    tenant_id = user.get("tenant_id", "default")
    session = _get_session(db, session_id, tenant_id)
    rule_version_id = payload.get("rule_version_id")
    
    version = db.query(RuleVersion).filter(RuleVersion.id == rule_version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Rule version not found")
        
    if version.status != "PENDING_REVIEW":
        raise HTTPException(status_code=400, detail=f"Cannot reject rule in status: {version.status}")
        
    update_rule_version_status(db, version.id, "REJECTED", "human_reviewer")
    
    from app.models.domain import RuleApproval
    approval = RuleApproval(
        id=str(uuid.uuid4()),
        rule_version_id=version.id,
        reviewer="human_reviewer",
        decision="REJECTED",
        comments=payload.get("comments")
    )
    db.add(approval)
    
    session.status = "REJECTED"
    db.commit()
    
    return {"status": "REJECTED", "rule_id": version.rule_id, "version": version.version}
