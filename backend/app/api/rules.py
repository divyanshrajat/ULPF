from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.domain import Rule, RuleVersion
from app.services.rules.registry import update_rule_version_status

router = APIRouter(prefix="/rules", tags=["Rules"])

@router.get("")
def list_rules(db: Session = Depends(get_db)):
    rules = db.query(Rule).all()
    return rules

@router.get("/{rule_id}")
def get_rule(rule_id: str, db: Session = Depends(get_db)):
    rule = db.query(Rule).filter(Rule.rule_id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    versions = db.query(RuleVersion).filter(RuleVersion.rule_id == rule_id).order_by(RuleVersion.version.desc()).all()
    return {
        "rule": rule,
        "versions": versions
    }

@router.post("/{rule_id}/versions/{version_id}/approve")
def approve_rule_version(rule_id: str, version_id: str, db: Session = Depends(get_db)):
    # Note: Using version_id (UUID) instead of version number for exact match, or we could query by rule_id + version
    # Since the prompt said {version}, it could be the integer version, but usually we use version_id. We'll use version_id.
    # Let's check by rule_id and version (int) or id (str). The schema says id is String.
    # We will assume version_id here is the ID.
    version = db.query(RuleVersion).filter(RuleVersion.id == version_id, RuleVersion.rule_id == rule_id).first()
    if not version:
        # fallback, try if version_id is actually integer version
        try:
            v_int = int(version_id)
            version = db.query(RuleVersion).filter(RuleVersion.version == v_int, RuleVersion.rule_id == rule_id).first()
        except ValueError:
            pass
            
    if not version:
        raise HTTPException(status_code=404, detail="Rule version not found")
        
    if version.status != "PENDING_REVIEW":
        raise HTTPException(status_code=400, detail=f"Cannot approve rule in status {version.status}")
        
    update_rule_version_status(db, version.id, "ACTIVE", actor="system")
    
    return {"status": "ACTIVE", "rule_id": rule_id, "version": version.version}

@router.post("/{rule_id}/versions/{version_id}/reject")
def reject_rule_version(rule_id: str, version_id: str, db: Session = Depends(get_db)):
    version = db.query(RuleVersion).filter(RuleVersion.id == version_id, RuleVersion.rule_id == rule_id).first()
    if not version:
        try:
            v_int = int(version_id)
            version = db.query(RuleVersion).filter(RuleVersion.version == v_int, RuleVersion.rule_id == rule_id).first()
        except ValueError:
            pass
            
    if not version:
        raise HTTPException(status_code=404, detail="Rule version not found")
        
    if version.status != "PENDING_REVIEW":
        raise HTTPException(status_code=400, detail=f"Cannot reject rule in status {version.status}")
        
    update_rule_version_status(db, version.id, "REJECTED", actor="system")
    
    return {"status": "REJECTED", "rule_id": rule_id, "version": version.version}

