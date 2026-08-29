from sqlalchemy.orm import Session
from app.models.domain import Mapping, Audit, Source
from typing import Dict, Any
import ulid
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MappingRegistry:
    def approve_mapping(
        self,
        db: Session,
        source_id: str,
        template_id: str,
        field_bindings: Dict[str, str],
        confidence_summary: Dict[str, Any],
        actor: str,
    ) -> Mapping:
        """
        Atomically:
        1. Supersede the previous active mapping (if any).
        2. Create a new immutable mapping version.
        3. Update source.active_mapping_version.
        4. Write audit log.
        """
        # Deactivate previous active mapping
        old_mapping = (
            db.query(Mapping)
            .filter(
                Mapping.source_id == source_id,
                Mapping.template_id == template_id,
                Mapping.status == "active",
            )
            .first()
        )

        new_version = 1
        old_bindings = None
        if old_mapping:
            old_bindings = old_mapping.field_bindings
            old_mapping.status = "superseded"
            new_version = (old_mapping.version or 0) + 1

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
            approved_at=datetime.utcnow(),
        )
        db.add(new_mapping)

        if old_mapping:
            old_mapping.superseded_by = new_mapping_id

        # Update source active mapping version
        source = db.query(Source).filter(Source.source_id == source_id).first()
        if source:
            source.active_mapping_version = new_version
            source.updated_at = datetime.utcnow()

        # Audit: mapping_approved
        db.add(Audit(
            audit_id=str(uuid.uuid4()),
            actor=actor,
            action="mapping_approved",
            subject_type="mapping",
            subject_id=new_mapping_id,
            before={"field_bindings": old_bindings, "version": old_mapping.version if old_mapping else None},
            after={"field_bindings": field_bindings, "version": new_version},
            occurred_at=datetime.utcnow(),
        ))

        # Audit: mapping_activated
        db.add(Audit(
            audit_id=str(uuid.uuid4()),
            actor=actor,
            action="mapping_activated",
            subject_type="source",
            subject_id=source_id,
            before={"active_mapping_version": old_mapping.version if old_mapping else None},
            after={"active_mapping_version": new_version, "mapping_id": new_mapping_id},
            occurred_at=datetime.utcnow(),
        ))

        db.commit()
        logger.info(
            f"[MAPPING APPROVED] source={source_id} template={template_id} "
            f"mapping={new_mapping_id} v{new_version} by={actor}"
        )
        return new_mapping


mapping_registry = MappingRegistry()
