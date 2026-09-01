"""
core_schema.py — Canonical Schema Registry definitions for ULPF.

Provides schema definitions, field metadata, and typing for:
1. ULPF Core Schema (ulpf-core-1.0)
2. OCSF Schema (ocsf-1.1.0)
3. ECS Schema (ecs-8.11)
"""
from typing import List, Dict, Any, Optional

CORE_FIELDS: List[Dict[str, Any]] = [
    # Metadata
    {"name": "metadata.trace_id", "type": "text", "description": "Unique trace identifier (ULID)"},
    {"name": "metadata.schema_version", "type": "text", "description": "Schema version string"},
    {"name": "metadata.mapping_version", "type": "numeric", "description": "Mapping version number"},
    {"name": "metadata.product.vendor", "type": "text", "description": "Vendor name"},
    {"name": "metadata.product.name", "type": "text", "description": "Product name"},

    # Time
    {"name": "time.event_time_utc", "type": "timestamp", "description": "Event timestamp normalized to UTC ISO-8601"},
    {"name": "time.event_time_original", "type": "text", "description": "Original event timestamp string"},
    {"name": "time.timezone", "type": "text", "description": "Detected timezone"},

    # Source
    {"name": "source.ip", "type": "ipv4", "description": "Originating source IP address"},
    {"name": "source.port", "type": "numeric", "description": "Originating source port"},
    {"name": "source.hostname", "type": "hostname", "description": "Originating source hostname"},
    {"name": "source.user", "type": "username", "description": "Originating source username"},
    {"name": "source.mac", "type": "mac", "description": "Originating source MAC address"},

    # Destination
    {"name": "destination.ip", "type": "ipv4", "description": "Target destination IP address"},
    {"name": "destination.port", "type": "numeric", "description": "Target destination port"},
    {"name": "destination.hostname", "type": "hostname", "description": "Target destination hostname"},
    {"name": "destination.service_name", "type": "text", "description": "Target service / application name"},

    # Network
    {"name": "network.protocol", "type": "protocol", "description": "Network protocol name (TCP, UDP, ICMP)"},
    {"name": "network.direction", "type": "text", "description": "Network direction (inbound, outbound)"},
    {"name": "network.bytes", "type": "numeric", "description": "Total network bytes"},
    {"name": "network.packets", "type": "numeric", "description": "Total network packets"},

    # HTTP
    {"name": "http.method", "type": "text", "description": "HTTP request method (GET, POST, etc.)"},
    {"name": "http.path", "type": "text", "description": "HTTP request path"},
    {"name": "http.url", "type": "text", "description": "HTTP full request URL"},
    {"name": "http.status_code", "type": "numeric", "description": "HTTP response status code"},
    {"name": "http.version", "type": "text", "description": "HTTP protocol version"},
    {"name": "http.response_bytes", "type": "numeric", "description": "HTTP response body bytes"},
    {"name": "http.user_agent", "type": "text", "description": "HTTP client User-Agent"},

    # Event
    {"name": "event.category", "type": "text", "description": "Event category (web, network, auth)"},
    {"name": "event.class", "type": "text", "description": "Event class description"},
    {"name": "event.action", "type": "action", "description": "Normalized event action (allow, deny, GET)"},
    {"name": "event.outcome", "type": "text", "description": "Event outcome (success, failure)"},
    {"name": "event.severity", "type": "severity", "description": "Normalized event severity level"},

    # Device
    {"name": "device.hostname", "type": "hostname", "description": "Reporting device hostname"},
    {"name": "device.ip", "type": "ipv4", "description": "Reporting device IP address"},
    {"name": "device.type", "type": "text", "description": "Reporting device type"},

    # Observer
    {"name": "observer.source_id", "type": "text", "description": "Observer source identity"},
    {"name": "observer.transport", "type": "text", "description": "Observer transport mechanism"},
    {"name": "observer.hostname", "type": "hostname", "description": "Observer host name"},
]

OCSF_FIELDS: List[Dict[str, Any]] = [
    {"name": "class_uid", "type": "numeric", "description": "OCSF Class Identifier (e.g. 4002 for HTTP Activity)"},
    {"name": "class_name", "type": "text", "description": "OCSF Class Name"},
    {"name": "category_uid", "type": "numeric", "description": "OCSF Category Identifier"},
    {"name": "time", "type": "numeric", "description": "Event timestamp in epoch milliseconds"},
    {"name": "src_endpoint.ip", "type": "ipv4", "description": "Source IP address"},
    {"name": "src_endpoint.port", "type": "numeric", "description": "Source port number"},
    {"name": "src_endpoint.hostname", "type": "hostname", "description": "Source host name"},
    {"name": "dst_endpoint.ip", "type": "ipv4", "description": "Destination IP address"},
    {"name": "dst_endpoint.port", "type": "numeric", "description": "Destination port number"},
    {"name": "http_request.http_method", "type": "text", "description": "HTTP request method"},
    {"name": "http_request.url.path", "type": "text", "description": "HTTP request URL path"},
    {"name": "http_request.version", "type": "text", "description": "HTTP protocol version"},
    {"name": "http_response.status_code", "type": "numeric", "description": "HTTP response status code"},
    {"name": "http_response.length", "type": "numeric", "description": "HTTP response length in bytes"},
    {"name": "status", "type": "text", "description": "Event status (Success, Failure)"},
    {"name": "status_id", "type": "numeric", "description": "Event status ID (1=Success, 2=Failure)"},
    {"name": "action", "type": "text", "description": "Event action (Allowed, Denied)"},
    {"name": "action_id", "type": "numeric", "description": "Event action ID (1=Allowed, 2=Denied)"},
    {"name": "severity", "type": "text", "description": "Event severity (Informational, Low, Medium, High, Critical)"},
    {"name": "severity_id", "type": "numeric", "description": "Event severity ID (1-5)"},
    {"name": "device.hostname", "type": "hostname", "description": "Device hostname"},
    {"name": "device.ip", "type": "ipv4", "description": "Device IP"},
    {"name": "actor.user.name", "type": "username", "description": "Actor / User name"},
    {"name": "connection_info.protocol_name", "type": "protocol", "description": "Network protocol name"},
    {"name": "unmapped", "type": "json", "description": "Unmapped vendor/custom fields preserved without data loss"},
]

ECS_FIELDS: List[Dict[str, Any]] = [
    {"name": "@timestamp", "type": "timestamp", "description": "UTC ISO-8601 event timestamp"},
    {"name": "source.ip", "type": "ipv4", "description": "Source IP address"},
    {"name": "source.port", "type": "numeric", "description": "Source port number"},
    {"name": "destination.ip", "type": "ipv4", "description": "Destination IP address"},
    {"name": "destination.port", "type": "numeric", "description": "Destination port number"},
    {"name": "network.protocol", "type": "protocol", "description": "Network protocol (tcp, udp, http)"},
    {"name": "network.bytes", "type": "numeric", "description": "Total network transfer bytes"},
    {"name": "http.request.method", "type": "text", "description": "HTTP request method (GET, POST)"},
    {"name": "http.response.status_code", "type": "numeric", "description": "HTTP response status code"},
    {"name": "http.response.bytes", "type": "numeric", "description": "HTTP response size in bytes"},
    {"name": "http.version", "type": "text", "description": "HTTP version string"},
    {"name": "url.path", "type": "text", "description": "HTTP request URL path"},
    {"name": "host.name", "type": "hostname", "description": "Host name"},
    {"name": "service.type", "type": "text", "description": "Service type / name (e.g. nginx, apache)"},
    {"name": "event.action", "type": "action", "description": "Event action name"},
    {"name": "event.category", "type": "text", "description": "Event category list"},
    {"name": "event.outcome", "type": "text", "description": "Event outcome (success, failure)"},
    {"name": "user.name", "type": "username", "description": "User username"},
    {"name": "labels", "type": "json", "description": "Custom labels and unmapped vendor fields"},
]


def get_schema_fields(schema_name: str) -> List[Dict[str, Any]]:
    """Retrieve field definitions for a supported schema."""
    s_low = (schema_name or "").lower()
    if "ocsf" in s_low:
        return OCSF_FIELDS
    if "ecs" in s_low:
        return ECS_FIELDS
    return CORE_FIELDS


def get_core_field(name: str) -> Optional[Dict[str, Any]]:
    """Lookup a field definition across schemas."""
    for f in CORE_FIELDS + OCSF_FIELDS + ECS_FIELDS:
        if f["name"] == name:
            return f
    return None
