"""
ecs_normalizer.py — Elastic Common Schema (ECS v8.11.0) Normalizer.

Transforms ULPFSemanticIR into standard ECS schema-compliant JSON representations.
Supports Web (http, url), Network (source, destination, network), Host,
and Log event structures.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
from app.schemas.semantic_ir import ULPFSemanticIR
import dateutil.parser


class ECSNormalizer:
    """ECS v8.11.0 Canonical Normalizer."""

    VERSION = "8.11.0"

    def normalize(self, ir: ULPFSemanticIR) -> Dict[str, Any]:
        """Convert ULPFSemanticIR into an ECS v8.11 event."""
        timestamp_iso = self._to_utc_iso(ir.event_time_utc)

        ecs_event: Dict[str, Any] = {
            "@timestamp": timestamp_iso,
            "ecs": {
                "version": self.VERSION,
            },
            "metadata": {
                "trace_id": ir.trace_id,
                "schema_version": "ecs-8.11",
                "mapping_version": ir.mapping_version,
                "processing_path": ir.processing_path,
            },
        }

        # Event fields
        categories, types = self._derive_categories_and_types(ir)
        event_dict: Dict[str, Any] = {
            "kind": "event",
            "category": categories,
            "type": types,
        }
        if ir.event.action:
            event_dict["action"] = ir.event.action
        if ir.event.outcome:
            event_dict["outcome"] = self._map_outcome(ir.event.outcome, ir.http.status_code)
        if ir.event.dataset:
            event_dict["dataset"] = ir.event.dataset
        if ir.event.severity or ir.event.severity_id is not None:
            event_dict["severity"] = ir.event.severity_id or ir.event.severity
        if ir.event.message:
            event_dict["original"] = ir.event.message

        ecs_event["event"] = event_dict

        # Source Endpoint
        source_dict: Dict[str, Any] = {}
        if ir.source.ip:
            source_dict["ip"] = ir.source.ip
            source_dict["address"] = ir.source.ip
        if ir.source.port is not None:
            source_dict["port"] = ir.source.port
        if ir.source.hostname:
            source_dict["domain"] = ir.source.hostname
        if ir.source.mac:
            source_dict["mac"] = ir.source.mac
        if ir.source.user:
            source_dict["user"] = {"name": ir.source.user}
        if ir.source.nat_ip:
            source_dict["nat"] = {"ip": ir.source.nat_ip, "port": ir.source.nat_port}
        if source_dict:
            ecs_event["source"] = source_dict

        # Destination Endpoint
        dest_dict: Dict[str, Any] = {}
        if ir.destination.ip:
            dest_dict["ip"] = ir.destination.ip
            dest_dict["address"] = ir.destination.ip
        if ir.destination.port is not None:
            dest_dict["port"] = ir.destination.port
        if ir.destination.hostname:
            dest_dict["domain"] = ir.destination.hostname
        if ir.destination.mac:
            dest_dict["mac"] = ir.destination.mac
        if ir.destination.nat_ip:
            dest_dict["nat"] = {"ip": ir.destination.nat_ip, "port": ir.destination.nat_port}
        if dest_dict:
            ecs_event["destination"] = dest_dict

        # Network Info
        network_dict: Dict[str, Any] = {}
        if ir.network.protocol:
            network_dict["protocol"] = ir.network.protocol.lower()
        if ir.network.transport:
            network_dict["transport"] = ir.network.transport.lower()
        if ir.network.direction:
            network_dict["direction"] = ir.network.direction
        if ir.network.bytes is not None:
            network_dict["bytes"] = ir.network.bytes
        if ir.network.packets is not None:
            network_dict["packets"] = ir.network.packets
        if network_dict:
            ecs_event["network"] = network_dict

        # HTTP Details
        if ir.http.method or ir.http.status_code is not None or ir.http.path or ir.http.url:
            http_dict: Dict[str, Any] = {}
            if ir.http.version:
                http_dict["version"] = ir.http.version

            req_dict: Dict[str, Any] = {}
            if ir.http.method:
                req_dict["method"] = ir.http.method.upper()
            if ir.http.request_bytes is not None:
                req_dict["bytes"] = ir.http.request_bytes
            if req_dict:
                http_dict["request"] = req_dict

            res_dict: Dict[str, Any] = {}
            if ir.http.status_code is not None:
                res_dict["status_code"] = ir.http.status_code
            if ir.http.response_bytes is not None:
                res_dict["bytes"] = ir.http.response_bytes
            if res_dict:
                http_dict["response"] = res_dict

            ecs_event["http"] = http_dict

            # URL Details
            url_dict: Dict[str, Any] = {}
            if ir.http.path:
                url_dict["path"] = ir.http.path
            if ir.http.url:
                url_dict["original"] = ir.http.url
            if ir.http.query:
                url_dict["query"] = ir.http.query
            if url_dict:
                ecs_event["url"] = url_dict

        # Host / Device
        host_dict: Dict[str, Any] = {}
        if ir.device.hostname or ir.observer.hostname:
            host_dict["name"] = ir.device.hostname or ir.observer.hostname
            host_dict["hostname"] = ir.device.hostname or ir.observer.hostname
        if ir.device.ip or ir.observer.ip:
            host_dict["ip"] = ir.device.ip or ir.observer.ip
        if host_dict:
            ecs_event["host"] = host_dict

        # Service / Observer
        if ir.observer.product or ir.observer.vendor or ir.device.product:
            ecs_event["service"] = {
                "type": ir.observer.product or ir.device.product or "web",
                "vendor": ir.observer.vendor or ir.device.vendor or "generic",
            }

        # User
        if ir.user.name:
            ecs_event["user"] = {
                "name": ir.user.name,
                "domain": ir.user.domain,
            }

        # Extensions / Labels (preserve without loss)
        if ir.extensions:
            ecs_event["labels"] = ir.extensions

        # Raw Reference link
        if ir.raw_ref:
            ecs_event["raw_ref"] = ir.raw_ref.to_dict()

        return ecs_event

    def _to_utc_iso(self, timestamp_str: Optional[str]) -> str:
        """Ensure UTC ISO-8601 formatting."""
        if not timestamp_str:
            return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        try:
            dt = dateutil.parser.parse(timestamp_str)
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except Exception:
            return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    def _derive_categories_and_types(self, ir: ULPFSemanticIR):
        categories: List[str] = []
        types: List[str] = []

        if ir.http.method or ir.http.path or ir.http.status_code is not None:
            categories.extend(["web", "network"])
            types.append("access")
        elif ir.network.protocol or ir.source.ip or ir.destination.ip:
            categories.append("network")
            types.append("connection")

        if ir.user.name or ir.event.category == "authentication":
            categories.append("authentication")
            types.append("start")

        if not categories:
            categories.append("host")
            types.append("info")

        return list(dict.fromkeys(categories)), list(dict.fromkeys(types))

    def _map_outcome(self, outcome: Optional[str], http_status: Optional[int]) -> str:
        if http_status is not None:
            return "success" if http_status < 400 else "failure"
        if outcome:
            out_low = outcome.lower()
            if out_low in ("allow", "permit", "accept", "success"):
                return "success"
            if out_low in ("deny", "block", "drop", "reject", "failure", "error"):
                return "failure"
        return "unknown"


ecs_normalizer = ECSNormalizer()
