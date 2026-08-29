from typing import List, Optional, Tuple
from app.schemas.domain import CandidateField
from app.services.discovery.drain3_miner import drain3_manager
from app.models.domain import Template, Source
from sqlalchemy.orm import Session
import ulid
from datetime import datetime

def discover_and_extract(db: Session, source_id: str, payload: bytes) -> Tuple[Optional[Template], List[CandidateField]]:
    text = payload.decode('utf-8', errors='ignore').strip()
    
    # Mine
    result = drain3_manager.mine(source_id, text)
    
    # Extract
    template_str, params = drain3_manager.extract(source_id, text)
    
    if not template_str:
        return None, []
        
    # Check if template exists in DB
    # drain3 cluster_id can be used as template_id
    cluster_id = result.get("cluster_id") if isinstance(result, dict) else result.cluster_id
    template_id = f"tpl_{source_id}_{cluster_id}"
    
    template = db.query(Template).filter(Template.template_id == template_id).first()
    if not template:
        # Create
        template = Template(
            template_id=template_id,
            source_id=source_id,
            pattern=template_str,
            variable_positions={}, # Populate if needed
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow(),
            occurrence_count=1
        )
        db.add(template)
        db.commit()
        db.refresh(template)
    else:
        template.occurrence_count += 1
        template.last_seen = datetime.utcnow()
        db.commit()
    
    candidate_fields = []
    if params:
        for i, param in enumerate(params):
            val = param.value if hasattr(param, "value") else param
            cf = CandidateField(
                field_key=f"pos_{i+1}",
                position=str(i+1),
                sample_values=[val]
            )
            candidate_fields.append(cf)
            
    return template, candidate_fields
