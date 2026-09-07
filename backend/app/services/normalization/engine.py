from typing import Dict, Any, Tuple, List
from datetime import datetime
from app.schemas.domain import NormalizedEvent, ProvenanceRecord
from app.models.domain import Mapping
from sqlalchemy.orm import Session
from dateutil import parser
import logging

logger = logging.getLogger(__name__)

ACTIONS_VOCAB = {"permit": "allow", "pass": "allow", "accept": "allow", 
                 "drop": "deny", "block": "deny", "reject": "deny"}

def normalize_timestamp(val: str) -> str:
    try:
        dt = parser.parse(val)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return val

def normalize_action(val: str) -> str:
    v = val.lower()
    return ACTIONS_VOCAB.get(v, v)

class NormalizationEngine:
    def normalize(self, db: Session, parsed_data: Dict[str, Any], source_id: str, 
                  template_id: str, trace_id: str, raw_ref: Dict[str, Any],
                  detection: Any = None) -> Tuple[NormalizedEvent, List[ProvenanceRecord]]:
        # Retrieve active mapping and source
        mapping = None
        if template_id:
            mapping = (
                db.query(Mapping)
                .filter(
                    Mapping.source_id == source_id, 
                    Mapping.template_id == template_id,
                    Mapping.status == "active"
                )
                .order_by(Mapping.version.desc())
                .first()
            )
        if not mapping:
            mapping = (
                db.query(Mapping)
                .filter(
                    Mapping.source_id == source_id, 
                    Mapping.status == "active"
                )
                .order_by(Mapping.version.desc())
                .first()
            )
            
        from app.models.domain import Source
        source = db.query(Source).filter(Source.source_id == source_id).first()
        source_namespace = source.namespace or source.vendor or "vendor" if source else "vendor"
            
        bindings = mapping.field_bindings if mapping else {}
        mapping_id = mapping.mapping_id if mapping else None
        mapping_version = mapping.version if mapping else None
        confidence_summary = mapping.confidence_summary if mapping and mapping.confidence_summary else {}
        
        event = NormalizedEvent()
        event.metadata["trace_id"] = trace_id
        event.metadata["schema_version"] = "ulpf-core-1.0"
        event.metadata["mapping_version"] = mapping_version
        event.raw_ref = raw_ref
        
        provenance_records = []
        
        for src_key, src_val in parsed_data.items():
            target_field = bindings.get(src_key)
            
            if not target_field or target_field == "extension_only":
                # Put in extension using dynamic namespace
                namespace = source_namespace
                if namespace not in event.extensions:
                    event.extensions[namespace] = {}
                event.extensions[namespace][src_key] = src_val
                
                provenance_records.append(ProvenanceRecord(
                    trace_id=trace_id,
                    target_field=f"extensions.{namespace}.{src_key}",
                    source_field=src_key,
                    source_value=str(src_val),
                    transformation="preserve",
                    mapping_id=mapping_id,
                    mapping_version=mapping_version,
                    schema_version="ulpf-core-1.0",
                    decision="extension_only"
                ))
            else:
                # Map to core
                group, field = target_field.split(".", 1)
                
                transformed_val = src_val
                transformation = "direct"
                
                if target_field == "time.event_time_utc":
                    transformed_val = normalize_timestamp(src_val)
                    transformation = "tz_normalize"
                elif target_field == "event.action":
                    transformed_val = normalize_action(src_val)
                    transformation = "action_vocab"
                    
                target_dict = getattr(event, group, None)
                if target_dict is not None:
                    target_dict[field] = transformed_val
                
                
                field_confidence = None
                decision = "fallback"
                
                if mapping:
                    field_conf_data = confidence_summary.get(src_key)
                    if isinstance(field_conf_data, dict):
                        field_confidence = field_conf_data.get("confidence")
                        decision = field_conf_data.get("decision", "auto_accepted")
                    elif isinstance(field_conf_data, (float, int)):
                        field_confidence = float(field_conf_data)
                        decision = "auto_accepted"
                    else:
                        decision = "human_approved" if mapping.approved_by else "auto_accepted"
                elif detection and detection.confidence and detection.confidence >= 0.90:
                    field_confidence = detection.confidence
                    decision = "deterministic"
                
                provenance_records.append(ProvenanceRecord(
                    trace_id=trace_id,
                    target_field=target_field,
                    source_field=src_key,
                    source_value=str(src_val),
                    transformation=transformation,
                    mapping_id=mapping_id,
                    mapping_version=mapping_version,
                    schema_version="ulpf-core-1.0",
                    confidence=field_confidence,
                    decision=decision
                ))
                
        return event, provenance_records

normalization_engine = NormalizationEngine()
