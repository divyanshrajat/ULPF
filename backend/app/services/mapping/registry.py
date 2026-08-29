from sqlalchemy.orm import Session
from app.models.domain import Mapping, Audit
from typing import Dict, Any, List
import ulid
from datetime import datetime

class MappingRegistry:
    def approve_mapping(self, db: Session, source_id: str, template_id: str, 
                        field_bindings: Dict[str, str], confidence_summary: Dict[str, Any], actor: str):
        
        # Deactivate old mapping
        old_mapping = db.query(Mapping).filter(
            Mapping.source_id == source_id,
            Mapping.template_id == template_id,
            Mapping.status == "active"
        ).first()
        
        new_version = 1
        if old_mapping:
            old_mapping.status = "superseded"
            new_version = old_mapping.version + 1
            
        new_mapping_id = str(ulid.new())
        
        new_mapping = Mapping(
            mapping_id=new_mapping_id,
            source_id=source_id,
            template_id=template_id,
            version=new_version,
            field_bindings=field_bindings,
            status="active",
            confidence_summary=confidence_summary,
            approved_by=actor,
            approved_at=datetime.utcnow()
        )
        db.add(new_mapping)
        
        if old_mapping:
            old_mapping.superseded_by = new_mapping_id
            
        # Write Audit log
        audit = Audit(
            audit_id=str(ulid.new()),
            actor=actor,
            action="approve_mapping",
            subject_type="mapping",
            subject_id=new_mapping_id,
            before=old_mapping.field_bindings if old_mapping else None,
            after=field_bindings,
            occurred_at=datetime.utcnow()
        )
        db.add(audit)
        
        db.commit()
        return new_mapping

mapping_registry = MappingRegistry()
