"""
semantic.py — Deterministic-first Semantic Mapper with Multi-Signal Confidence Scoring.

Confidence Scoring Formula:
  C = 0.35 * S_name + 0.30 * S_value + 0.20 * S_context + 0.15 * S_history

Threshold Decisions:
  - C >= 0.85       → auto_accepted (deterministic or high confidence canonical mapping)
  - 0.65 <= C < 0.85 → review (ambiguous mapping requiring human approval)
  - C < 0.65        → extension_only (preserved in namespaced extensions)
"""
import logging
import os
import re
import numpy as np
from typing import List, Dict, Any, Optional
from app.schemas.domain import CandidateField, MappingProposal
from app.services.schema_registry.core_schema import CORE_FIELDS, get_schema_fields

logger = logging.getLogger(__name__)

# Common network and web vocabularies
HTTP_METHODS_SET = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "CONNECT", "TRACE"}
NETWORK_PROTO_SET = {"TCP", "UDP", "ICMP", "HTTP", "HTTPS", "DNS", "SSH", "TLS", "IP", "IGMP"}
ACTION_VOCAB_SET = {"ALLOW", "PERMIT", "ACCEPT", "PASS", "DENY", "BLOCK", "DROP", "REJECT", "BUILT", "TEARDOWN"}
IPV4_REGEX = re.compile(r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')


class SemanticMapper:
    """Multi-Signal Deterministic & Semantic Field Mapper."""

    def __init__(self):
        self.model = None
        self.core_embeddings = None
        self.core_names = [f["name"] for f in CORE_FIELDS]
        self.core_types = {f["name"]: f["type"] for f in CORE_FIELDS}
        self._load_failed = False

    def _load_model(self):
        """Lazy-load SentenceTransformer model if available."""
        if self.model is not None or self._load_failed:
            return

        try:
            from sentence_transformers import SentenceTransformer
            from app.core.config import settings

            model_path = settings.ULPF_MODEL_PATH
            if settings.ULPF_MODE == "airgap":
                if not os.path.isabs(model_path) or not os.path.isdir(model_path):
                    logger.info(f"AIR-GAP MODE: Using deterministic semantic mapping rules.")
                    self._load_failed = True
                    return

            self.model = SentenceTransformer(model_path)
            descriptions = [f"{f['name']} : {f['description']}" for f in CORE_FIELDS]
            self.core_embeddings = self.model.encode(descriptions, convert_to_numpy=True)
            logger.info("SentenceTransformer semantic model loaded successfully.")
        except Exception as e:
            logger.info(f"Semantic embedding model unavailable ({e}); falling back to deterministic-first rules.")
            self._load_failed = True

    def compute_similarity(self, candidate_context: str) -> np.ndarray:
        """Return embedding cosine similarities, or zeros if model unavailable."""
        self._load_model()
        if self._load_failed or self.model is None or self.core_embeddings is None:
            return np.zeros(len(self.core_names))

        try:
            cand_emb = self.model.encode([candidate_context], convert_to_numpy=True)
            similarities = np.dot(self.core_embeddings, cand_emb.T).flatten()
            norms = np.linalg.norm(self.core_embeddings, axis=1) * np.linalg.norm(cand_emb)
            return similarities / (norms + 1e-9)
        except Exception:
            return np.zeros(len(self.core_names))

    def evaluate_type_agreement(self, inferred_type: str, sample_val: Any, target_name: str, target_type: str) -> float:
        """Score semantic value agreement (0.0 to 1.0) against canonical expectations."""
        val_str = str(sample_val).strip() if sample_val is not None else ""

        # Specific canonical field semantic validators
        if target_name in ("source.ip", "destination.ip", "device.ip", "src_endpoint.ip", "dst_endpoint.ip"):
            if IPV4_REGEX.match(val_str):
                return 1.0
            return 0.0

        if target_name in ("source.port", "destination.port", "src_endpoint.port", "dst_endpoint.port"):
            try:
                p = int(val_str)
                if 1 <= p <= 65535:
                    return 1.0
            except ValueError:
                pass
            return 0.0

        if target_name in ("http.status_code", "http_response.status_code"):
            try:
                code = int(val_str)
                if 100 <= code <= 599:
                    return 1.0
            except ValueError:
                pass
            return 0.0

        if target_name in ("http.method", "http_request.http_method"):
            if val_str.upper() in HTTP_METHODS_SET:
                return 1.0
            return 0.0

        if target_name in ("http.path", "url.path"):
            if val_str.startswith("/") or val_str.startswith("http"):
                return 1.0

        if target_name in ("network.protocol", "connection_info.protocol_name"):
            if val_str.upper() in NETWORK_PROTO_SET:
                return 1.0

        if target_name in ("event.action", "action"):
            if val_str.upper() in ACTION_VOCAB_SET or val_str.upper() in HTTP_METHODS_SET:
                return 1.0

        if target_type == "numeric":
            return 1.0 if (inferred_type in ("numeric", "integer", "float") or val_str.isdigit()) else 0.2

        if target_type == "timestamp":
            return 1.0 if inferred_type == "timestamp" else 0.4

        if target_type == "ipv4":
            return 1.0 if IPV4_REGEX.match(val_str) else 0.0

        if target_type == "hostname":
            return 0.8 if inferred_type in ("hostname", "text") else 0.4

        return 0.6  # Default neutral for text fields

    def propose_mappings(
        self,
        db,
        source_id: str,
        template_id: str,
        candidate: CandidateField,
        template_pattern: str,
        target_schema: str = "core",
    ) -> List[MappingProposal]:
        """
        Generate ranked mapping proposals with multi-signal confidence scores.
        """
        from app.models.domain import Mapping

        sample_val = candidate.sample_values[0] if candidate.sample_values else None
        context_str = f"field {candidate.field_key} type {candidate.inferred_type} value {sample_val} in {template_pattern}"
        sims = self.compute_similarity(context_str)

        # Historical mapping consensus from database
        history_mappings = db.query(Mapping).filter(Mapping.status == "active").all()
        historical_targets: Dict[str, int] = {}
        for m in history_mappings:
            for k, v in (m.field_bindings or {}).items():
                if k.lower() == candidate.field_key.lower():
                    historical_targets[v] = historical_targets.get(v, 0) + 1

        # Comprehensive deterministic field alias mappings
        alias_map = {
            # Source IP & Ports
            "client_ip": "source.ip",
            "src": "source.ip",
            "src_ip": "source.ip",
            "source": "source.ip",
            "sourceip": "source.ip",
            "spt": "source.port",
            "src_port": "source.port",
            "sport": "source.port",
            # Destination IP & Ports
            "dst": "destination.ip",
            "dst_ip": "destination.ip",
            "dest_ip": "destination.ip",
            "destination": "destination.ip",
            "destip": "destination.ip",
            "dpt": "destination.port",
            "dst_port": "destination.port",
            "dport": "destination.port",
            # Web / HTTP
            "http_method": "http.method",
            "method": "http.method",
            "request_method": "http.method",
            "url_path": "http.path",
            "path": "http.path",
            "uri": "http.path",
            "request_uri": "http.path",
            "http_version": "http.version",
            "version": "http.version",
            "status_code": "http.status_code",
            "status": "http.status_code",
            "response_bytes": "http.response_bytes",
            "bytes": "network.bytes",
            "bytes_sent": "http.response_bytes",
            "length": "http.response_bytes",
            "user_agent": "http.user_agent",
            # Network
            "proto": "network.protocol",
            "protocol": "network.protocol",
            "network_protocol": "network.protocol",
            "direction": "network.direction",
            "network_direction": "network.direction",
            # Event & Action
            "act": "event.action",
            "action": "event.action",
            "event_action": "event.action",
            "decision": "event.outcome",
            "severity": "event.severity",
            # Host & Device
            "host": "device.hostname",
            "hostname": "device.hostname",
            "syslog.hostname": "device.hostname",
            "syslog.priority": "event.severity",
            "syslog.timestamp": "time.event_time_original",
            "http_timestamp": "time.event_time_original",
            "user": "source.user",
            "username": "source.user",
        }

        # Target catalog based on schema
        target_fields = get_schema_fields(target_schema)
        proposals: List[MappingProposal] = []

        for i, target in enumerate(target_fields):
            target_name = target["name"]
            target_type = target.get("type", "text")

            # 1. S_name: Name similarity
            s_name = float(sims[i]) if i < len(sims) else 0.0
            cand_lower = candidate.field_key.lower().replace("-", "_")

            if alias_map.get(cand_lower) == target_name:
                s_name = 0.98
            elif cand_lower == target_name.split(".")[-1]:
                s_name = max(s_name, 0.92)
            elif cand_lower in target_name:
                s_name = max(s_name, 0.82)

            s_name = max(0.0, min(1.0, s_name))

            # 2. S_value: Semantic value agreement
            s_value = self.evaluate_type_agreement(
                candidate.inferred_type,
                sample_val,
                target_name,
                target_type
            )

            # 3. S_context: Sibling and template context
            target_group = target_name.split(".")[0]
            s_context = 0.5
            if target_group in ("http", "source", "destination", "network") and (
                "nginx" in template_pattern.lower() or "http" in template_pattern.lower() or "cef" in template_pattern.lower() or "asa" in template_pattern.lower()
            ):
                s_context = 0.85

            # 4. S_history: Historical mapping count
            hist_count = historical_targets.get(target_name, 0)
            if history_mappings:
                s_history = min(1.0, hist_count * 0.4)
                c = (0.35 * s_name) + (0.30 * s_value) + (0.20 * s_context) + (0.15 * s_history)
            else:
                # Cold start: normalize across active signals
                s_history = 0.0
                c = ((0.35 * s_name) + (0.30 * s_value) + (0.20 * s_context)) / 0.85

            # Deterministic exact alias + valid value boost
            if s_name >= 0.95 and s_value == 1.0:
                c = max(c, 0.95)

            # Value mismatch hard penalty
            if s_value == 0.0 and target_type in ("ipv4", "numeric", "timestamp"):
                c = min(c, 0.40)

            c = round(max(0.0, min(1.0, c)), 3)

            # Decision Thresholds: >= 0.85 Auto-Accept | 0.65-0.85 Review | < 0.65 Extension
            if c >= 0.85:
                decision = "auto_accepted"
            elif c >= 0.65:
                decision = "review"
            else:
                decision = "extension_only"

            proposals.append(MappingProposal(
                source_field=candidate.field_key,
                target_field=target_name,
                confidence=c,
                decision=decision,
                signals={
                    "name": round(s_name, 3),
                    "value": round(s_value, 3),
                    "context": round(s_context, 3),
                    "history": round(s_history, 3),
                }
            ))

        proposals.sort(key=lambda x: x.confidence, reverse=True)
        return proposals


semantic_mapper = SemanticMapper()
