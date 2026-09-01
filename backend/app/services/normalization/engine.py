"""
engine.py — Universal Log Normalization Engine with Multi-Schema Target Support.

Converts parsed event data into ULPFSemanticIR, applies schema-specific
normalizers (OCSF v1.1.0, ECS v8.11, ULPF Core v1.0), and generates
field-level machine-readable provenance records.
"""
from typing import Dict, Any, Tuple, List, Optional
from datetime import datetime
from app.schemas.domain import NormalizedEvent as LegacyEventSchema, ProvenanceRecord
from app.schemas.semantic_ir import (
    ULPFSemanticIR, SourceEndpoint, DestinationEndpoint, NetworkInfo,
    HttpInfo, EventInfo, DeviceInfo, ObserverInfo, UserInfo, RawReference
)
from app.services.normalization.ocsf_normalizer import ocsf_normalizer
from app.services.normalization.ecs_normalizer import ecs_normalizer
from app.models.domain import Mapping, Source
from sqlalchemy.orm import Session
from dateutil import parser
import logging

logger = logging.getLogger(__name__)

ACTIONS_VOCAB = {
    "permit": "allow", "pass": "allow", "accept": "allow", "built": "allow",
    "drop": "deny", "block": "deny", "reject": "deny", "teardown": "deny",
}


def normalize_timestamp(val: Any) -> str:
    """Normalize any timestamp string to UTC ISO-8601."""
    if not val:
        return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        dt = parser.parse(str(val))
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_action(val: Any) -> str:
    """Normalize action string to standard vocabulary."""
    v = str(val).strip().lower()
    return ACTIONS_VOCAB.get(v, v)


class NormalizationEngine:
    """Multi-Schema Normalization Engine."""

    def build_semantic_ir(
        self,
        db: Session,
        parsed_data: Dict[str, Any],
        source_id: str,
        template_id: str,
        trace_id: str,
        raw_ref: Dict[str, Any],
        mapping_version: Optional[int] = None,
        processing_path: str = "adaptive",
    ) -> Tuple[ULPFSemanticIR, List[ProvenanceRecord]]:
        """Construct schema-agnostic ULPFSemanticIR and record field provenance."""
        # Retrieve active mapping
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

        source = db.query(Source).filter(Source.source_id == source_id).first()
        source_namespace = source.namespace or source.vendor or "Generic" if source else "Generic"
        bindings = mapping.field_bindings if mapping else {}
        mapping_id = mapping.mapping_id if mapping else None
        m_version = mapping.version if mapping else mapping_version

        # Initialize Semantic IR
        raw_reference = RawReference(
            trace_id=raw_ref.get("trace_id", trace_id),
            digest=raw_ref.get("digest", "sha256:unknown"),
            byte_length=raw_ref.get("byte_length", 0),
        )

        ir = ULPFSemanticIR(
            trace_id=trace_id,
            mapping_version=m_version,
            processing_path=processing_path,
            raw_ref=raw_reference,
            event_time_utc=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

        if source:
            ir.observer.source_id = source_id
            ir.observer.vendor = source.vendor
            ir.observer.product = source.product
            ir.observer.transport = source.transport

        provenance_records: List[ProvenanceRecord] = []

        # Auto-mapping rules if bindings are not yet populated
        auto_bindings = dict(bindings)
        if not auto_bindings:
            auto_bindings = self._infer_default_bindings(parsed_data)

        # Iterate over all parsed keys
        for src_key, src_val in parsed_data.items():
            if src_val is None:
                continue

            target_field = auto_bindings.get(src_key)

            if not target_field or target_field == "extension_only":
                # Preserve in namespaced extensions
                if source_namespace not in ir.extensions:
                    ir.extensions[source_namespace] = {}
                ir.extensions[source_namespace][src_key] = src_val

                provenance_records.append(ProvenanceRecord(
                    trace_id=trace_id,
                    target_field=f"extensions.{source_namespace}.{src_key}",
                    source_field=src_key,
                    source_value=str(src_val),
                    transformation="preserve",
                    mapping_id=mapping_id,
                    mapping_version=m_version,
                    schema_version="ulpf-core-1.0",
                    decision="extension_only",
                ))
            else:
                transformation = "direct"
                confidence = 0.95

                # Route into ULPFSemanticIR components
                if target_field == "source.ip" or target_field == "src_endpoint.ip":
                    ir.source.ip = str(src_val)
                    transformation = "ip_validate"
                elif target_field == "source.port" or target_field == "src_endpoint.port":
                    try:
                        ir.source.port = int(src_val)
                        transformation = "int_cast"
                    except ValueError:
                        pass
                elif target_field == "source.hostname" or target_field == "src_endpoint.hostname":
                    ir.source.hostname = str(src_val)
                elif target_field == "destination.ip" or target_field == "dst_endpoint.ip":
                    ir.destination.ip = str(src_val)
                    transformation = "ip_validate"
                elif target_field == "destination.port" or target_field == "dst_endpoint.port":
                    try:
                        ir.destination.port = int(src_val)
                        transformation = "int_cast"
                    except ValueError:
                        pass
                elif target_field == "http.method" or target_field == "http_request.http_method":
                    ir.http.method = str(src_val).upper()
                    ir.event.action = str(src_val).upper()
                elif target_field == "http.path" or target_field == "url.path":
                    ir.http.path = str(src_val)
                    ir.http.url = str(src_val)
                elif target_field == "http.version":
                    ir.http.version = str(src_val)
                elif target_field == "http.status_code" or target_field == "http_response.status_code":
                    try:
                        code = int(src_val)
                        ir.http.status_code = code
                        ir.event.outcome = "success" if code < 400 else "failure"
                        transformation = "int_cast"
                    except ValueError:
                        pass
                elif target_field == "http.response_bytes" or target_field == "http_response.length":
                    try:
                        ir.http.response_bytes = int(src_val)
                        ir.network.bytes = int(src_val)
                        transformation = "int_cast"
                    except ValueError:
                        pass
                elif target_field == "network.protocol":
                    ir.network.protocol = str(src_val).upper()
                elif target_field == "network.direction":
                    ir.network.direction = str(src_val)
                elif target_field == "network.bytes":
                    try:
                        ir.network.bytes = int(src_val)
                    except ValueError:
                        pass
                elif target_field == "event.action":
                    ir.event.action = normalize_action(src_val)
                    transformation = "action_vocab"
                elif target_field == "device.hostname" or target_field == "host.name":
                    ir.device.hostname = str(src_val)
                    ir.observer.hostname = str(src_val)
                elif target_field == "time.event_time_utc" or target_field == "@timestamp":
                    ir.event_time_utc = normalize_timestamp(src_val)
                    transformation = "tz_normalize"
                elif target_field == "time.event_time_original":
                    ir.event_time_original = str(src_val)
                    ir.event_time_utc = normalize_timestamp(src_val)
                    transformation = "tz_normalize"
                else:
                    # Generic core fallback
                    if source_namespace not in ir.extensions:
                        ir.extensions[source_namespace] = {}
                    ir.extensions[source_namespace][src_key] = src_val

                provenance_records.append(ProvenanceRecord(
                    trace_id=trace_id,
                    target_field=target_field,
                    source_field=src_key,
                    source_value=str(src_val),
                    transformation=transformation,
                    mapping_id=mapping_id,
                    mapping_version=m_version,
                    schema_version="ulpf-core-1.0",
                    decision="auto_accepted",
                ))

        return ir, provenance_records

    def normalize(
        self,
        db: Session,
        parsed_data: Dict[str, Any],
        source_id: str,
        template_id: str,
        trace_id: str,
        raw_ref: Dict[str, Any],
        target_schema: str = "ocsf",
        processing_path: str = "adaptive",
    ) -> Tuple[Dict[str, Any], List[ProvenanceRecord]]:
        """
        Normalize event into requested canonical target schema:
        - 'ocsf' or 'ocsf-1.1.0' -> OCSF v1.1.0 JSON
        - 'ecs' or 'ecs-8.11'   -> ECS v8.11 JSON
        - 'core' or 'ulpf-core-1.0' -> ULPF Core JSON
        """
        ir, provenance_records = self.build_semantic_ir(
            db=db,
            parsed_data=parsed_data,
            source_id=source_id,
            template_id=template_id,
            trace_id=trace_id,
            raw_ref=raw_ref,
            processing_path=processing_path,
        )

        s_low = (target_schema or "ocsf").lower()
        if "ecs" in s_low:
            payload = ecs_normalizer.normalize(ir)
        elif "core" in s_low or "ulpf" in s_low:
            payload = ir.to_dict()
        else:
            # Default to OCSF v1.1.0
            payload = ocsf_normalizer.normalize(ir)

        return payload, provenance_records

    def _infer_default_bindings(self, parsed_data: Dict[str, Any]) -> Dict[str, str]:
        """Heuristic semantic bindings when no manual mapping has been approved yet."""
        bindings: Dict[str, str] = {}
        for k in parsed_data.keys():
            k_low = k.lower().replace("-", "_")
            if k_low in ("client_ip", "src", "src_ip", "source_ip", "sourceip"):
                bindings[k] = "source.ip"
            elif k_low in ("spt", "sport", "src_port"):
                bindings[k] = "source.port"
            elif k_low in ("dst", "dst_ip", "dest_ip", "destination_ip"):
                bindings[k] = "destination.ip"
            elif k_low in ("dpt", "dport", "dst_port"):
                bindings[k] = "destination.port"
            elif k_low in ("http_method", "method", "request_method"):
                bindings[k] = "http.method"
            elif k_low in ("url_path", "path", "uri", "request_uri"):
                bindings[k] = "http.path"
            elif k_low in ("http_version", "version") and k != "cef.version":
                bindings[k] = "http.version"
            elif k_low in ("status_code", "status", "http_status"):
                bindings[k] = "http.status_code"
            elif k_low in ("response_bytes", "bytes_sent", "length"):
                bindings[k] = "http.response_bytes"
            elif k_low in ("proto", "protocol", "network_protocol"):
                bindings[k] = "network.protocol"
            elif k_low in ("act", "action", "event_action"):
                bindings[k] = "event.action"
            elif k_low in ("hostname", "syslog.hostname", "host"):
                bindings[k] = "device.hostname"
            elif k_low in ("syslog.timestamp", "http_timestamp"):
                bindings[k] = "time.event_time_original"
            elif k_low in ("syslog.priority",):
                bindings[k] = "event.severity"
        return bindings


normalization_engine = NormalizationEngine()
