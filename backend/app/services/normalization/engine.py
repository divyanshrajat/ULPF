import logging
from typing import Any

from dateutil import parser
from sqlalchemy.orm import Session

from app.schemas.domain import NormalizedEvent, ProvenanceRecord

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
    def normalize(self, db: Session, parsed_data: dict[str, Any], source_id: str, 
                  template_id: str, trace_id: str, raw_ref: dict[str, Any],
                  detection: Any = None) -> tuple[NormalizedEvent, list[ProvenanceRecord]]:
        
        # Get Source namespace
        from app.models.domain import Source
        source = db.query(Source).filter(Source.source_id == source_id).first()
        namespace = source.namespace or source.vendor or "vendor" if source else "vendor"
        
        event = NormalizedEvent()
        event.event_id = trace_id
        event.normalization["schema"] = "ulpf-core-1.0"
        event.raw_reference = raw_ref
        
        provenance_records = []
        
        for src_key, src_val in parsed_data.items():
            if "." not in src_key and src_key not in ["event_id", "event_time", "ingest_time"]:
                # Unmapped field
                if namespace not in event.unmapped_fields:
                    event.unmapped_fields[namespace] = {}
                    
                event.unmapped_fields[namespace][src_key] = src_val
                
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
                transformed_val = src_val
                transformation = "direct"
                target_field = src_key

                if src_key == "event_time":
                    transformed_val = normalize_timestamp(str(src_val))
                    transformation = "tz_normalize"
                    event.event_time = transformed_val
                elif src_key == "ingest_time":
                    event.ingest_time = str(transformed_val)
                elif src_key == "event_id":
                    event.event_id = str(transformed_val)
                else:
                    if "." in src_key:
                        group, field = src_key.split(".", 1)
                    else:
                        group, field = "unmapped_fields", src_key
                        
                    if group == "security" and field == "action":
                        transformed_val = normalize_action(str(src_val))
                        transformation = "action_vocab"
                        
                    target_dict = getattr(event, group, None)
                    if target_dict is not None:
                        target_dict[field] = transformed_val
                    else:
                        # Generic fallback if group doesn't exist on NormalizedEvent
                        if group not in event.unmapped_fields:
                            event.unmapped_fields[group] = {}
                        event.unmapped_fields[group][field] = transformed_val
                
                provenance_records.append(ProvenanceRecord(
                    trace_id=trace_id,
                    target_field=target_field,
                    source_field=src_key, # In V2, the parser outputs the mapped field name
                    source_value=str(src_val),
                    transformation=transformation,
                    decision="deterministic"
                ))
                
        return event, provenance_records

normalization_engine = NormalizationEngine()
