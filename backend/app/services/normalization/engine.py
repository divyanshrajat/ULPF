from typing import Dict, Any, Tuple, List
from app.schemas.domain import NormalizedEvent, ProvenanceRecord
from app.models.domain import RuleVersion
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
        
        # Get Source namespace
        from app.models.domain import Source
        source = db.query(Source).filter(Source.source_id == source_id).first()
        namespace = source.namespace or source.vendor or "vendor" if source else "vendor"
        
        event = NormalizedEvent()
        event.metadata["trace_id"] = trace_id
        event.metadata["schema_version"] = "ulpf-core-1.0"
        event.raw_ref = raw_ref
        
        # We need a generic way to handle unmapped fields since the mappings are now handled BEFORE this in the parser.
        # Wait, the parser already output canonical names (e.g. event.time).
        # Any field that doesn't have a dot or isn't a known OCSF/ECS field is "unmapped".
        
        provenance_records = []
        
        for src_key, src_val in parsed_data.items():
            if "." not in src_key:
                # Unmapped field
                if "unmapped_fields" not in event.extensions:
                    event.extensions["unmapped_fields"] = {}
                if namespace not in event.extensions["unmapped_fields"]:
                    event.extensions["unmapped_fields"][namespace] = {}
                    
                event.extensions["unmapped_fields"][namespace][src_key] = src_val
                
                provenance_records.append(ProvenanceRecord(
                    trace_id=trace_id,
                    target_field=f"unmapped_fields.{namespace}.{src_key}",
                    source_field=src_key,
                    source_value=str(src_val),
                    transformation="preserve",
                    decision="unmapped"
                ))
            else:
                # Mapped field
                group, field = src_key.split(".", 1)
                
                transformed_val = src_val
                transformation = "direct"
                
                if src_key == "event.time" or src_key == "time.event_time_utc":
                    transformed_val = normalize_timestamp(str(src_val))
                    transformation = "tz_normalize"
                elif src_key == "event.action":
                    transformed_val = normalize_action(str(src_val))
                    transformation = "action_vocab"
                    
                target_dict = getattr(event, group, None)
                if target_dict is not None:
                    target_dict[field] = transformed_val
                else:
                    # Generic fallback if group doesn't exist on NormalizedEvent
                    if group not in event.extensions:
                        event.extensions[group] = {}
                    event.extensions[group][field] = transformed_val
                
                provenance_records.append(ProvenanceRecord(
                    trace_id=trace_id,
                    target_field=src_key,
                    source_field=src_key, # In V2, the parser outputs the mapped field name
                    source_value=str(src_val),
                    transformation=transformation,
                    decision="deterministic"
                ))
                
        return event, provenance_records

normalization_engine = NormalizationEngine()
