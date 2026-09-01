"""
deterministic.py — Multi-layer deterministic format and payload parsers.

Supports:
1. Container/Envelope Layers: Syslog RFC 3164, Syslog RFC 5424, CEF, LEEF, JSON, Key-Value, Delimited.
2. Embedded Payload Layers: Web/Nginx access logs, Key=Value strings, Cisco ASA patterns.
"""
import json
import re
from typing import Dict, Any, Optional

# IPv4 and Port regex helpers
IPV4_REGEX = r'(?:\d{1,3}\.){3}\d{1,3}'
HTTP_METHODS = r'(?:GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS|CONNECT|TRACE)'


def parse_json(payload: bytes) -> Dict[str, Any]:
    """Parse JSON payload."""
    text = payload.decode('utf-8', errors='ignore').strip()
    data = json.loads(text)
    if isinstance(data, dict):
        return data
    return {"raw_json": data}


def parse_key_value(payload: bytes) -> Dict[str, Any]:
    """Parse key=value string format."""
    text = payload.decode('utf-8', errors='ignore').strip()
    return parse_kv_text(text)


def parse_kv_text(text: str) -> Dict[str, Any]:
    """Extract key=value and key="value with spaces" tokens."""
    matches = re.findall(r'\b([\w\.\-]+)\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|([^\s]+))', text)
    result: Dict[str, Any] = {}
    for match in matches:
        key = match[0]
        val = match[1] or match[2] or match[3]
        result[key] = val
    return result


def parse_delimited(payload: bytes, delimiter: str = '|') -> Dict[str, Any]:
    """Parse delimited text into positional fields."""
    text = payload.decode('utf-8', errors='ignore').strip()
    parts = text.split(delimiter)
    result = {}
    for i, part in enumerate(parts):
        result[f"pos_{i+1}"] = part.strip()
    return result


def parse_cef(payload: bytes) -> Dict[str, Any]:
    """
    Parse CEF (Common Event Format):
    CEF:Version|Device Vendor|Device Product|Device Version|Device Event Class ID|Name|Severity|[Extension]
    """
    text = payload.decode('utf-8', errors='ignore').strip()
    return parse_cef_text(text)


def parse_cef_text(text: str) -> Dict[str, Any]:
    """Parse CEF header and key-value extensions."""
    cef_pattern = re.compile(r'^(?:<\d+>\d*\s*)?(?:[^\s]+\s+)?CEF:\s*(\d+)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|(.*)$')
    match = cef_pattern.match(text)
    if not match:
        return {}

    result = {
        "cef.version": match.group(1),
        "cef.device_vendor": match.group(2),
        "cef.device_product": match.group(3),
        "cef.device_version": match.group(4),
        "cef.signature_id": match.group(5),
        "cef.name": match.group(6),
        "cef.severity": match.group(7),
    }

    # Parse extensions
    ext_text = match.group(8)
    if ext_text:
        ext_kv = parse_kv_text(ext_text)
        result.update(ext_kv)

    return result


def parse_web_access_log(text: str) -> Dict[str, Any]:
    """
    Parse standard / combined Nginx or Apache access log formats.
    e.g. '203.0.113.55 GET /api/v1/health HTTP/1.1 200 612'
    or '203.0.113.55 - - [29/Aug/2026:09:30:12 +0000] "GET /api/v1/health HTTP/1.1" 200 612'
    """
    # Pattern 1: Combined / Common access log with quotes and brackets
    combined_pattern = re.compile(
        r'(' + IPV4_REGEX + r')\s+\S+\s+\S+\s+\[([^\]]+)\]\s+"(' + HTTP_METHODS + r')\s+(\S+)(?:\s+HTTP/(\S+))?"\s+(\d{3})\s+(\d+|-)'
    )
    m1 = combined_pattern.search(text)
    if m1:
        return {
            "client_ip": m1.group(1),
            "http_timestamp": m1.group(2),
            "http_method": m1.group(3),
            "url_path": m1.group(4),
            "http_version": m1.group(5) or "1.1",
            "status_code": int(m1.group(6)),
            "response_bytes": int(m1.group(7)) if m1.group(7) != "-" else 0,
        }

    # Pattern 2: Simplified web access log: '<ip> <METHOD> <path> HTTP/<version> <status> <bytes>'
    simple_pattern = re.compile(
        r'(' + IPV4_REGEX + r')\s+(' + HTTP_METHODS + r')\s+(\S+)\s+HTTP/(\S+)\s+(\d{3})\s+(\d+)'
    )
    m2 = simple_pattern.search(text)
    if m2:
        return {
            "client_ip": m2.group(1),
            "http_method": m2.group(2),
            "url_path": m2.group(3),
            "http_version": m2.group(4),
            "status_code": int(m2.group(5)),
            "response_bytes": int(m2.group(6)),
        }

    return {}


def parse_cisco_asa(text: str) -> Dict[str, Any]:
    """
    Parse Cisco ASA security appliance log messages:
    %ASA-6-302013: Built outbound TCP connection ...
    %ASA-4-106023: Deny tcp src ...
    """
    asa_header = re.search(r'%ASA-(\d)-(\d+):\s*(.*)', text)
    if not asa_header:
        return {}

    severity = int(asa_header.group(1))
    code = asa_header.group(2)
    body = asa_header.group(3)

    result: Dict[str, Any] = {
        "cisco.facility": "ASA",
        "cisco.severity": severity,
        "cisco.message_code": code,
        "cisco.message": body,
    }

    # Check connection built / teardown
    conn_match = re.search(
        r'(Built|Teardown)\s+(?:(inbound|outbound)\s+)?(?:(\w+)\s+)?connection\s+(\d+)\s+for\s+(?:[\w\-]+:)?(' + IPV4_REGEX + r')/(\d+)(?:\s+\([^\)]+\))?\s+to\s+(?:[\w\-]+:)?(' + IPV4_REGEX + r')/(\d+)',
        body,
        re.IGNORECASE
    )
    if conn_match:
        result["event_action"] = conn_match.group(1).lower()
        if conn_match.group(2):
            result["network_direction"] = conn_match.group(2).lower()
        if conn_match.group(3):
            result["network_protocol"] = conn_match.group(3).upper()
        result["src_ip"] = conn_match.group(5)
        result["src_port"] = int(conn_match.group(6))
        result["dst_ip"] = conn_match.group(7)
        result["dst_port"] = int(conn_match.group(8))
        return result

    # Check access-list deny / permit
    acl_match = re.search(
        r'(Deny|Permit)\s+(\w+)\s+src\s+(?:[\w\-]+:)?(' + IPV4_REGEX + r')/(\d+)\s+dst\s+(?:[\w\-]+:)?(' + IPV4_REGEX + r')/(\d+)',
        body,
        re.IGNORECASE
    )
    if acl_match:
        result["event_action"] = acl_match.group(1).lower()
        result["network_protocol"] = acl_match.group(2).upper()
        result["src_ip"] = acl_match.group(3)
        result["src_port"] = int(acl_match.group(4))
        result["dst_ip"] = acl_match.group(5)
        result["dst_port"] = int(acl_match.group(6))
        return result

    return result


def parse_syslog_3164(payload: bytes) -> Dict[str, Any]:
    """
    Multi-layer parser for RFC 3164 Syslog:
    1. Parse Syslog envelope (<PRI>TIMESTAMP HOSTNAME TAG: MSG).
    2. Recursively parse embedded message (Web, CEF, Cisco ASA, Key-Value).
    """
    text = payload.decode('utf-8', errors='ignore').strip()
    match = re.match(r'^<(\d{1,3})>([A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+(.*)', text)
    if not match:
        if "%ASA-" in text:
            return parse_cisco_asa(text)
        if "CEF:" in text:
            return parse_cef_text(text)
        web_data = parse_web_access_log(text)
        if web_data:
            return web_data
        kv_data = parse_kv_text(text)
        if len(kv_data) >= 2:
            return kv_data
        return {"raw_message": text}

    priority = match.group(1)
    timestamp = match.group(2)
    hostname = match.group(3)
    raw_msg = match.group(4)

    result: Dict[str, Any] = {
        "syslog.priority": priority,
        "syslog.timestamp": timestamp,
        "syslog.hostname": hostname,
        "syslog.message": raw_msg,
    }

    # Extract App Tag if present (e.g. 'nginx:', 'sshd[1234]:')
    tag_match = re.match(r'^([\w\.\-]+)(?:\[\d+\])?:\s*(.*)$', raw_msg)
    app_tag = None
    inner_msg = raw_msg
    if tag_match:
        app_tag = tag_match.group(1)
        inner_msg = tag_match.group(2)
        result["syslog.app_name"] = app_tag

    # Layer 2: Deep message payload extraction
    # 2a. Check if inner message is CEF
    if "CEF:" in inner_msg:
        cef_data = parse_cef_text(inner_msg)
        if cef_data:
            result.update(cef_data)
            return result

    # 2b. Check if inner message is Cisco ASA
    if "%ASA-" in raw_msg:
        asa_data = parse_cisco_asa(raw_msg)
        if asa_data:
            result.update(asa_data)
            return result

    # 2c. Check if inner message is a Web Access Log
    web_data = parse_web_access_log(inner_msg)
    if web_data:
        result.update(web_data)
        return result

    # 2d. Check if inner message has Key=Value pairs
    kv_data = parse_kv_text(inner_msg)
    if len(kv_data) >= 2:
        result.update(kv_data)
        return result

    return result


def parse_syslog_5424(payload: bytes) -> Dict[str, Any]:
    """
    Parse RFC 5424 Syslog:
    <PRI>VERSION TIMESTAMP HOSTNAME APP-NAME PROCID MSGID [SD-ID] MSG
    """
    text = payload.decode('utf-8', errors='ignore').strip()
    match = re.match(
        r'^<(\d{1,3})>(\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(?:\[([^\]]*)\])?\s*(.*)$',
        text
    )
    if not match:
        return parse_syslog_3164(payload)

    result = {
        "syslog.priority": match.group(1),
        "syslog.version": match.group(2),
        "syslog.timestamp": match.group(3),
        "syslog.hostname": match.group(4),
        "syslog.app_name": match.group(5),
        "syslog.proc_id": match.group(6),
        "syslog.msg_id": match.group(7),
        "syslog.structured_data": match.group(8),
        "syslog.message": match.group(9),
    }

    # Inner message parsing
    inner_msg = match.group(9) or ""
    if "CEF:" in inner_msg:
        result.update(parse_cef_text(inner_msg))
    elif "%ASA-" in inner_msg:
        result.update(parse_cisco_asa(inner_msg))
    else:
        web_data = parse_web_access_log(inner_msg)
        if web_data:
            result.update(web_data)
        else:
            kv_data = parse_kv_text(inner_msg)
            if len(kv_data) >= 2:
                result.update(kv_data)

    return result
