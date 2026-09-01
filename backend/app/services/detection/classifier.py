import json
import re
import xml.etree.ElementTree as ET
from app.schemas.detection import DetectedFormat

# RFC 5424 regex: <PRIVAL>VERSION TIMESTAMP HOSTNAME APP-NAME PROCID MSGID [SD-ID] MSG
RFC5424_RE = re.compile(r'^<\d{1,3}>[1-9]\d{0,2}\s+')
# RFC 3164 regex: <PRIVAL>TIMESTAMP HOSTNAME MSG
RFC3164_RE = re.compile(r'^<\d{1,3}>[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\s+')

def classify_format(payload: bytes, source_pinned_format: str = None) -> DetectedFormat:
    text = payload.decode('utf-8', errors='ignore').strip()
    
    if source_pinned_format:
        return DetectedFormat(
            format_name=source_pinned_format,
            confidence=1.00,
            reason="Source configuration pinned format"
        )
        
    if text.startswith("CEF:") or "CEF:" in text[:40]:
        return DetectedFormat(format_name="cef", confidence=0.99, reason="Literal grammar marker (CEF:)")

    if "%ASA-" in text:
        return DetectedFormat(format_name="cisco_asa", confidence=0.98, reason="Literal grammar marker (%ASA-)")
        
    if "LEEF:" in text[:20]:
        return DetectedFormat(format_name="leef", confidence=0.99, reason="Literal grammar marker (LEEF:)")
        
    try:
        parsed = json.loads(text)
        if isinstance(parsed, (dict, list)):
            return DetectedFormat(format_name="json", confidence=0.98, reason="Strict parse success", parsed_data=parsed if isinstance(parsed, dict) else None)
    except json.JSONDecodeError:
        pass
        
    if text.startswith("<") and text.endswith(">"):
        try:
            ET.fromstring(text)
            return DetectedFormat(format_name="xml", confidence=0.97, reason="Strict parse success")
        except ET.ParseError:
            pass
            
    if RFC5424_RE.match(text):
        return DetectedFormat(format_name="syslog_5424", confidence=0.95, reason="Structural regex RFC 5424")
        
    if RFC3164_RE.match(text):
        return DetectedFormat(format_name="syslog_3164", confidence=0.90, reason="Structural regex RFC 3164")
        
    # Check for CSV/Delimited consistency (simple heuristic)
    pipes = text.count('|')
    commas = text.count(',')
    tabs = text.count('\t')
    if pipes > 3:
        return DetectedFormat(format_name="delimited_pipe", confidence=0.75, reason="Statistical consistency (pipes)")
    if commas > 3:
        return DetectedFormat(format_name="csv", confidence=0.75, reason="Statistical consistency (commas)")
    if tabs > 3:
        return DetectedFormat(format_name="tsv", confidence=0.75, reason="Statistical consistency (tabs)")

    # Key-value (e.g. k=v k='v')
    kv_matches = len(re.findall(r'\b\w+\s*=\s*[\'"]?[^\s\'"]+[\'"]?', text))
    if kv_matches >= 3:
        return DetectedFormat(format_name="key_value", confidence=0.80, reason="Token statistics (key=value)")

    # Unrecognized / proprietary
    return DetectedFormat(format_name="unknown", confidence=0.31, reason="No rule matched")
