import hashlib
import hmac
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
                  detection: Any = None) -> tuple[dict[str, Any], list[ProvenanceRecord]]:
        
        # Get Source namespace
        from app.models.domain import Source
        source = db.query(Source).filter(Source.source_id == source_id).first()
        namespace = source.namespace or source.vendor or "vendor" if source else "vendor"
        
        event = NormalizedEvent()
        event.event_id = trace_id
        event.normalization["schema"] = "ulpf-core-1.0"
        event.raw_reference = raw_ref
        
        # Get masking policy and target_schema
        masking_policy = {}
        target_schema = "ulpf-core-1.0"
        if template_id:
            from app.models.domain import RuleVersion
            rule_ver = db.query(RuleVersion).filter(RuleVersion.id == template_id).first()
            if rule_ver:
                target_schema = rule_ver.target_schema
                if rule_ver.masking_policy:
                    masking_policy = rule_ver.masking_policy

        provenance_records = []
        
        import hashlib
        
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
                        
                    if src_key in masking_policy:
                        policy = masking_policy[src_key]
                        if policy == "hash":
                            from app.core.config import settings
                            # HMAC-SHA256 instead of plain SHA-256 (T39)
                            # Plain SHA-256 of low-entropy values (IPs, port numbers, usernames)
                            # is reversible via dictionary attack. HMAC requires the key.
                            mac = hmac.new(
                                settings.MASK_HMAC_KEY.encode(),
                                str(transformed_val).encode(),
                                hashlib.sha256
                            )
                            transformed_val = mac.hexdigest()
                            transformation = "mask_hmac_hash"
                        elif policy == "mask":
                            transformed_val = "***"
                            transformation = "mask_redact"
                        elif policy == "drop":
                            continue
                        
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
                
        event_dict = event.dict()
        
        if target_schema == "ocsf":
            from app.services.normalization.adapters.ocsf import to_ocsf
            event_dict = to_ocsf(event_dict)
            event_dict.setdefault("normalization", {})["schema"] = "ocsf-1.1.0"
        elif target_schema == "ecs":
            from app.services.normalization.adapters.ecs import to_ecs
            event_dict = to_ecs(event_dict)
            event_dict.setdefault("normalization", {})["schema"] = "ecs-8.11.0"
            
        return event_dict, provenance_records

normalization_engine = NormalizationEngine()
