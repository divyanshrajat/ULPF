from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import require_approver, require_admin, get_current_user
from app.core.database import get_db
from app.models.domain import Rule, RuleVersion
from app.services.rules.registry import update_rule_version_status

router = APIRouter(prefix="/rules", tags=["Rules"])

@router.get("")
def list_rules(db: Session = Depends(get_db), actor: dict = Depends(get_current_user)):
    tenant_id = actor.get("tenant_id", "default")
    rules = db.query(Rule).filter(Rule.tenant_id == tenant_id).all()
    out = []
    for r in rules:
        # Get the latest version for schema and version number
        v = db.query(RuleVersion).filter(RuleVersion.rule_id == r.rule_id).order_by(RuleVersion.version.desc()).first()
        out.append({
            "id": r.rule_id,
            "name": r.name,
            "status": r.status,
            "updated_at": r.updated_at,
            "version": v.version if v else 1,
            "target_schema": v.target_schema if v else "unknown"
        })
    return out

@router.get("/{rule_id}")
def get_rule(rule_id: str, db: Session = Depends(get_db), actor: dict = Depends(get_current_user)):
    tenant_id = actor.get("tenant_id", "default")
    rule = db.query(Rule).filter(Rule.tenant_id == tenant_id, Rule.rule_id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    versions = db.query(RuleVersion).filter(RuleVersion.tenant_id == tenant_id, RuleVersion.rule_id == rule_id).order_by(RuleVersion.version.desc()).all()
    return {
        "rule": rule,
        "versions": versions
    }

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
import sys
import os



@router.post("/{rule_id}/versions/{version_id}/approve")
def approve_rule_version(
    rule_id: str,
    version_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    actor: dict = Depends(require_approver)
):
    # Note: Using version_id (UUID) instead of version number for exact match, or we could query by rule_id + version
    # Since the prompt said {version}, it could be the integer version, but usually we use version_id. We'll use version_id.
    # We will assume version_id here is the ID.
    tenant_id = actor.get("tenant_id", "default")
    version = db.query(RuleVersion).filter(RuleVersion.tenant_id == tenant_id, RuleVersion.id == version_id, RuleVersion.rule_id == rule_id).first()
    if not version:
        try:
            v_int = int(version_id)
            version = db.query(RuleVersion).filter(RuleVersion.tenant_id == tenant_id, RuleVersion.version == v_int, RuleVersion.rule_id == rule_id).first()
        except ValueError:
            pass
            
    if not version:
        raise HTTPException(status_code=404, detail="Rule version not found")
        
    if version.status != "PENDING_REVIEW":
        raise HTTPException(status_code=400, detail=f"Cannot approve rule in status {version.status}")

    actor_name = actor.get("username", "unknown")
    update_rule_version_status(db, version.id, "ACTIVE", actor=actor_name)
    
    from app.models.domain import RuleApproval
    import uuid
    approval = RuleApproval(
        id=str(uuid.uuid4()),
        rule_version_id=version.id,
        reviewer=actor_name,
        decision="APPROVED",
        comments="Approved via /rules API"
    )
    db.add(approval)
    db.commit()
    
    # Automatically trigger reprocessing of unresolved events for this tenant/source
    from app.services.ingestion.reprocessor import republish_unresolved_events
    background_tasks.add_task(republish_unresolved_events, rule_id=rule_id)
    
    return {"status": "ACTIVE", "rule_id": rule_id, "version": version.version}

@router.post("/{rule_id}/versions/{version_id}/reject")
def reject_rule_version(
    rule_id: str,
    version_id: str,
    db: Session = Depends(get_db),
    actor: dict = Depends(require_approver)
):
    tenant_id = actor.get("tenant_id", "default")
    version = db.query(RuleVersion).filter(RuleVersion.tenant_id == tenant_id, RuleVersion.id == version_id, RuleVersion.rule_id == rule_id).first()
    if not version:
        try:
            v_int = int(version_id)
            version = db.query(RuleVersion).filter(RuleVersion.tenant_id == tenant_id, RuleVersion.version == v_int, RuleVersion.rule_id == rule_id).first()
        except ValueError:
            pass
            
    if not version:
        raise HTTPException(status_code=404, detail="Rule version not found")
        
    if version.status != "PENDING_REVIEW":
        raise HTTPException(status_code=400, detail=f"Cannot reject rule in status {version.status}")

    actor_name = actor.get("username", "unknown")
    update_rule_version_status(db, version.id, "REJECTED", actor=actor_name)
    
    from app.models.domain import RuleApproval
    import uuid
    approval = RuleApproval(
        id=str(uuid.uuid4()),
        rule_version_id=version.id,
        reviewer=actor_name,
        decision="REJECTED",
        comments="Rejected via /rules API"
    )
    db.add(approval)
    db.commit()
    
    return {"status": "REJECTED", "rule_id": rule_id, "version": version.version}

@router.post("/{rule_id}/disable")
def disable_rule(
    rule_id: str,
    db: Session = Depends(get_db),
    actor: dict = Depends(require_admin)
):
    tenant_id = actor.get("tenant_id", "default")
    rule = db.query(Rule).filter(Rule.tenant_id == tenant_id, Rule.rule_id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    actor_name = actor.get("username", "unknown")
    rule.status = "DISABLED"
    
    # Disable all active versions
    versions = db.query(RuleVersion).filter(RuleVersion.tenant_id == tenant_id, RuleVersion.rule_id == rule_id, RuleVersion.status == "ACTIVE").all()
    for v in versions:
        update_rule_version_status(db, v.id, "DISABLED", actor=actor_name)
        
    db.commit()
    return {"status": "DISABLED", "rule_id": rule_id}

@router.post("/{rule_id}/archive")
def archive_rule(
    rule_id: str,
    db: Session = Depends(get_db),
    actor: dict = Depends(require_admin)
):
    tenant_id = actor.get("tenant_id", "default")
    rule = db.query(Rule).filter(Rule.tenant_id == tenant_id, Rule.rule_id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    actor_name = actor.get("username", "unknown")
    rule.status = "ARCHIVED"
    
    # Archive all active/disabled versions
    versions = db.query(RuleVersion).filter(RuleVersion.tenant_id == tenant_id, RuleVersion.rule_id == rule_id, RuleVersion.status.in_(["ACTIVE", "DISABLED"])).all()
    for v in versions:
        update_rule_version_status(db, v.id, "ARCHIVED", actor=actor_name)
        
    db.commit()
    return {"status": "ARCHIVED", "rule_id": rule_id}

