"""
ocsf_normalizer.py — Open Cybersecurity Schema Framework (OCSF v1.1.0) Normalizer.

Transforms ULPFSemanticIR into strict OCSF schema-compliant JSON representations.
Supports HTTP Activity (4002), Network Activity (4001), Security Finding (2001),
Authentication (3002), and System Activity (1001) event classes.
"""
from typing import Dict, Any, Optional
from datetime import datetime
from app.schemas.semantic_ir import ULPFSemanticIR
import dateutil.parser


class OCSFNormalizer:
    """OCSF v1.1.0 Canonical Normalizer."""

    VERSION = "1.1.0"

    def normalize(self, ir: ULPFSemanticIR) -> Dict[str, Any]:
        """Convert ULPFSemanticIR into an OCSF v1.1.0 event."""
        # Determine appropriate OCSF Class
        class_uid, class_name, category_uid, category_name = self._classify_event(ir)

        # Parse epoch time in milliseconds
        event_time_ms = self._to_epoch_ms(ir.event_time_utc)

        # Map action_id and status_id
        action_id, action_str = self._map_action(ir.event.action, ir.event.outcome)
        status_id, status_str = self._map_status(ir.event.outcome, ir.http.status_code)
        severity_id, severity_str = self._map_severity(ir.event.severity, ir.event.severity_id)

        ocsf_event: Dict[str, Any] = {
            "metadata": {
                "version": self.VERSION,
                "schema_version": "ocsf-1.1.0",
                "product": {
                    "vendor_name": ir.observer.vendor or ir.device.vendor or "ULPF",
                    "name": ir.observer.product or ir.device.product or "Generic Logger",
                    "version": ir.observer.version or "1.0",
                },
                "profiles": ["cloud", "host", "security_control"],
                "trace_id": ir.trace_id,
                "mapping_version": ir.mapping_version,
                "processing_path": ir.processing_path,
            },
            "class_uid": class_uid,
            "class_name": class_name,
            "category_uid": category_uid,
            "category_name": category_name,
            "activity_id": 1,
            "activity_name": ir.event.action or class_name,
            "time": event_time_ms,
            "severity_id": severity_id,
            "severity": severity_str,
            "status_id": status_id,
            "status": status_str,
        }

        if action_id is not None:
            ocsf_event["action_id"] = action_id
            ocsf_event["action"] = action_str

        # Endpoints
        src_ep = self._build_endpoint(ir.source.ip, ir.source.port, ir.source.hostname, ir.source.mac, ir.source.domain)
        if src_ep:
            ocsf_event["src_endpoint"] = src_ep

        dst_ep = self._build_endpoint(ir.destination.ip, ir.destination.port, ir.destination.hostname, ir.destination.mac, ir.destination.domain, ir.destination.service_name)
        if dst_ep:
            ocsf_event["dst_endpoint"] = dst_ep

        # HTTP specific structures
        if ir.http.method or ir.http.path or ir.http.url or ir.http.status_code is not None:
            http_req: Dict[str, Any] = {}
            if ir.http.method:
                http_req["http_method"] = ir.http.method.upper()
            if ir.http.url or ir.http.path:
                http_req["url"] = {
                    "url_string": ir.http.url or ir.http.path,
                    "path": ir.http.path or ir.http.url,
                }
            if ir.http.version:
                http_req["version"] = ir.http.version
            if ir.http.user_agent:
                http_req["user_agent"] = ir.http.user_agent
            if ir.http.request_bytes is not None:
                http_req["length"] = ir.http.request_bytes

            if http_req:
                ocsf_event["http_request"] = http_req

            http_res: Dict[str, Any] = {}
            if ir.http.status_code is not None:
                http_res["status_code"] = ir.http.status_code
            if ir.http.response_bytes is not None:
                http_res["length"] = ir.http.response_bytes
            if http_res:
                ocsf_event["http_response"] = http_res

        # Network Activity details
        if ir.network.protocol or ir.network.bytes or ir.network.packets:
            net_conn: Dict[str, Any] = {}
            if ir.network.protocol:
                net_conn["protocol_name"] = ir.network.protocol.upper()
            if ir.network.direction:
                net_conn["direction"] = ir.network.direction
            if ir.network.bytes is not None:
                net_conn["bytes"] = ir.network.bytes
            if ir.network.packets is not None:
                net_conn["packets"] = ir.network.packets
            if net_conn:
                ocsf_event["connection_info"] = net_conn

        # Device / Host
        if ir.device.hostname or ir.device.ip:
            dev: Dict[str, Any] = {}
            if ir.device.hostname:
                dev["hostname"] = ir.device.hostname
            if ir.device.ip:
                dev["ip"] = ir.device.ip
            if ir.device.type:
                dev["type"] = ir.device.type
            ocsf_event["device"] = dev

        # Actor / User
        if ir.user.name:
            ocsf_event["actor"] = {
                "user": {
                    "name": ir.user.name,
                    "domain": ir.user.domain,
                }
            }

        # Message
        if ir.event.message:
            ocsf_event["message"] = ir.event.message

        # Unmapped / Extensions (preserve all unknown or vendor fields without loss)
        if ir.extensions:
            ocsf_event["unmapped"] = ir.extensions

        # Raw Reference link
        if ir.raw_ref:
            ocsf_event["raw_ref"] = ir.raw_ref.to_dict()

        return ocsf_event

    def _classify_event(self, ir: ULPFSemanticIR):
        """Classify event into primary OCSF class."""
        if ir.http.method or ir.http.path or ir.http.status_code is not None:
            return 4002, "HTTP Activity", 4, "Network Activity"
        if ir.user.name and ir.event.category == "authentication":
            return 3002, "Authentication", 3, "Identity & Access Management"
        if ir.event.severity_id and ir.event.severity_id >= 4:
            return 2001, "Security Finding", 2, "Findings"
        if ir.network.protocol or ir.source.ip or ir.destination.ip:
            return 4001, "Network Activity", 4, "Network Activity"
        return 1001, "System Activity", 1, "System Activity"

    def _to_epoch_ms(self, timestamp_str: Optional[str]) -> int:
        """Convert ISO timestamp string to epoch milliseconds."""
        if not timestamp_str:
            return int(datetime.utcnow().timestamp() * 1000)
        try:
            dt = dateutil.parser.parse(timestamp_str)
            return int(dt.timestamp() * 1000)
        except Exception:
            return int(datetime.utcnow().timestamp() * 1000)

    def _map_action(self, action_str: Optional[str], outcome_str: Optional[str]):
        """Map action to OCSF action_id."""
        val = (action_str or outcome_str or "").lower()
        if val in ("allow", "permit", "accept", "pass"):
            return 1, "Allowed"
        if val in ("deny", "block", "drop", "reject", "prevent"):
            return 2, "Denied"
        return 0, "Unknown"

    def _map_status(self, outcome: Optional[str], http_status: Optional[int]):
        """Map outcome or HTTP code to OCSF status."""
        if http_status is not None:
            if 200 <= http_status < 400:
                return 1, "Success"
            elif http_status >= 400:
                return 2, "Failure"
        if outcome:
            out_low = outcome.lower()
            if out_low in ("success", "allow", "permit", "accept"):
                return 1, "Success"
            if out_low in ("failure", "deny", "block", "error"):
                return 2, "Failure"
        return 99, "Other"

    def _map_severity(self, severity_str: Optional[str], severity_id: Optional[int]):
        """Map severity to OCSF standard severity."""
        if severity_id in (1, 2, 3, 4, 5):
            labels = {1: "Informational", 2: "Low", 3: "Medium", 4: "High", 5: "Critical"}
            return severity_id, labels[severity_id]
        if severity_str:
            s_low = severity_str.lower()
            if s_low in ("critical", "emergency", "alert"):
                return 5, "Critical"
            if s_low in ("high", "error"):
                return 4, "High"
            if s_low in ("medium", "warning", "warn"):
                return 3, "Medium"
            if s_low in ("low", "notice"):
                return 2, "Low"
            if s_low in ("informational", "info", "debug"):
                return 1, "Informational"
        return 1, "Informational"

    def _build_endpoint(self, ip=None, port=None, hostname=None, mac=None, domain=None, svc_name=None) -> Optional[Dict[str, Any]]:
        ep: Dict[str, Any] = {}
        if ip:
            ep["ip"] = ip
        if port is not None:
            ep["port"] = port
        if hostname:
            ep["hostname"] = hostname
        if mac:
            ep["mac"] = mac
        if domain:
            ep["domain"] = domain
        if svc_name:
            ep["svc_name"] = svc_name
        return ep if ep else None


ocsf_normalizer = OCSFNormalizer()
