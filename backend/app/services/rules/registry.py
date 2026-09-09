import hashlib
import json
import uuid

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.domain import Rule, RuleFingerprint, RuleLifecycleEvent, RuleVersion


def create_rule(db: Session, name: str, description: str = None) -> Rule:
    rule_id = str(uuid.uuid4())
    rule = Rule(rule_id=rule_id, name=name, description=description, status="DRAFT")
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule

def get_rule(db: Session, rule_id: str) -> Rule:
    return db.query(Rule).filter(Rule.rule_id == rule_id).first()

def get_active_rule_version(db: Session, rule_id: str) -> RuleVersion:
    return db.query(RuleVersion).filter(
        RuleVersion.rule_id == rule_id,
        RuleVersion.status == "ACTIVE"
    ).order_by(RuleVersion.version.desc()).first()

def _calculate_rule_hash(parser_type: str, parser_def: dict, mappings: dict, req_fields: list, type_constraints: dict, masking: dict, target_schema: str, schema_version: str) -> str:
    canonical_repr = json.dumps({
        "parser_type": parser_type,
        "parser_definition": parser_def,
        "field_mappings": mappings,
        "required_fields": req_fields or [],
        "type_constraints": type_constraints or {},
        "masking_policy": masking or {},
        "target_schema": target_schema,
        "schema_version": schema_version
    }, sort_keys=True)
    return hashlib.sha256(canonical_repr.encode()).hexdigest()

def create_rule_version(db: Session, rule_id: str, parser_type: str, parser_definition: dict, field_mappings: dict, required_fields: list = None, type_constraints: dict = None, masking_policy: dict = None, target_schema: str = "ocsf", schema_version: str = "1.0", created_by: str = "system") -> RuleVersion:
    rule = get_rule(db, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
        
    latest_version = db.query(RuleVersion).filter(RuleVersion.rule_id == rule_id).order_by(RuleVersion.version.desc()).first()
    next_version_num = latest_version.version + 1 if latest_version else 1
    
    rule_hash = _calculate_rule_hash(parser_type, parser_definition, field_mappings, required_fields, type_constraints, masking_policy, target_schema, schema_version)
    
    version_id = str(uuid.uuid4())
    rule_version = RuleVersion(
        id=version_id,
        rule_id=rule_id,
        version=next_version_num,
        parser_type=parser_type,
        parser_definition=parser_definition,
        field_mappings=field_mappings,
        required_fields=required_fields,
        type_constraints=type_constraints,
        masking_policy=masking_policy,
        target_schema=target_schema,
        schema_version=schema_version,
        rule_hash=rule_hash,
        status="DRAFT",
        created_by=created_by
    )
    db.add(rule_version)
    
    # Audit log
    event = RuleLifecycleEvent(id=str(uuid.uuid4()), rule_id=rule_id, rule_version_id=version_id, event_type="VERSION_CREATED", actor=created_by)
    db.add(event)
    
    db.commit()
    db.refresh(rule_version)
    return rule_version

def update_rule_version_status(db: Session, version_id: str, new_status: str, actor: str) -> RuleVersion:
    """Transitions a rule version through lifecycle: DRAFT -> PENDING_REVIEW -> ACTIVE/REJECTED.
       Only one ACTIVE version is allowed per rule.
    """
    version = db.query(RuleVersion).filter(RuleVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Rule version not found")
        
    rule = db.query(Rule).filter(Rule.rule_id == version.rule_id).first()
    
    if new_status == "ACTIVE":
        # Deactivate current active versions
        active_versions = db.query(RuleVersion).filter(RuleVersion.rule_id == version.rule_id, RuleVersion.status == "ACTIVE").all()
        for av in active_versions:
            av.status = "DEPRECATED"
            db.add(RuleLifecycleEvent(id=str(uuid.uuid4()), rule_id=rule.rule_id, rule_version_id=av.id, event_type="DEPRECATED", actor=actor))
            
        rule.status = "ACTIVE"
        
    version.status = new_status
    
    # Audit
    db.add(RuleLifecycleEvent(id=str(uuid.uuid4()), rule_id=rule.rule_id, rule_version_id=version.id, event_type=f"STATUS_CHANGED_TO_{new_status}", actor=actor))
    
    db.commit()
    db.refresh(version)
    return version

def add_fingerprint_to_rule(db: Session, rule_id: str, fingerprint: str):
    exists = db.query(RuleFingerprint).filter(RuleFingerprint.rule_id == rule_id, RuleFingerprint.fingerprint == fingerprint).first()
    if not exists:
        fp = RuleFingerprint(id=str(uuid.uuid4()), rule_id=rule_id, fingerprint=fingerprint)
        db.add(fp)
        db.commit()

def find_active_rule_by_fingerprint(db: Session, fingerprint: str) -> RuleVersion:
    # Get all rules matching the fingerprint
    fps = db.query(RuleFingerprint).filter(RuleFingerprint.fingerprint == fingerprint).all()
    for fp in fps:
        # Check if the rule is active
        rule = get_rule(db, fp.rule_id)
        if rule and rule.status == "ACTIVE":
            # return the active version
            active_version = get_active_rule_version(db, fp.rule_id)
            if active_version:
                return active_version
    return None
