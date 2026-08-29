import json
import re
from typing import Dict, Any

def parse_json(payload: bytes) -> Dict[str, Any]:
    text = payload.decode('utf-8', errors='ignore').strip()
    return json.loads(text)

def parse_key_value(payload: bytes) -> Dict[str, Any]:
    text = payload.decode('utf-8', errors='ignore').strip()
    # Matches k=v, k="v", k='v'
    matches = re.findall(r'\b(\w+)\s*=\s*([\'"]?)([^\s\'"]+)\2', text)
    result = {}
    for k, _, v in matches:
        result[k] = v
    return result

def parse_delimited(payload: bytes, delimiter: str = '|') -> Dict[str, Any]:
    text = payload.decode('utf-8', errors='ignore').strip()
    parts = text.split(delimiter)
    result = {}
    for i, part in enumerate(parts):
        result[f"pos_{i+1}"] = part.strip()
    return result

def parse_syslog_3164(payload: bytes) -> Dict[str, Any]:
    text = payload.decode('utf-8', errors='ignore').strip()
    # Basic parsing for <PRIVAL>TIMESTAMP HOSTNAME MSG
    match = re.match(r'^<(\d{1,3})>([A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+(.*)', text)
    if match:
        return {
            "syslog.priority": match.group(1),
            "syslog.timestamp": match.group(2),
            "syslog.hostname": match.group(3),
            "syslog.message": match.group(4)
        }
    return {"raw_message": text}
