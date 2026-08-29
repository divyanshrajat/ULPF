from sqlalchemy.orm import Session
from app.models.domain import Provenance
from typing import List
from app.schemas.domain import ProvenanceRecord
import logging

logger = logging.getLogger(__name__)

def save_provenance(db: Session, records: List[ProvenanceRecord]):
    try:
        for r in records:
            prov = Provenance(
                trace_id=r.trace_id,
                target_field=r.target_field,
                source_field=r.source_field,
                source_value=r.source_value,
                transformation=r.transformation,
                mapping_id=r.mapping_id,
                mapping_version=r.mapping_version,
                schema_version=r.schema_version,
                confidence=r.confidence,
                decision=r.decision
            )
            db.merge(prov) # Use merge to handle potential updates/re-runs if trace_id and target_field match
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save provenance: {e}")

def get_provenance(db: Session, trace_id: str) -> List[Provenance]:
    return db.query(Provenance).filter(Provenance.trace_id == trace_id).all()
