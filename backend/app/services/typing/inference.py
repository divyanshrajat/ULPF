import re
from typing import List

IPV4_RE = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
MAC_RE = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
TIMESTAMP_RE = re.compile(r'^\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?$')
URL_RE = re.compile(r'^https?://[^\s]+$')
PATH_RE = re.compile(r'^(/[\w.-]+)+/?$')
NUMERIC_RE = re.compile(r'^-?\d+(?:\.\d+)?$')

# Controlled vocabularies
ACTIONS = {"permit", "allow", "accept", "pass", "deny", "drop", "block", "reject", "log", "alert"}
SEVERITIES = {"debug", "info", "notice", "warning", "warn", "error", "err", "critical", "crit", "alert", "emergency", "emerg"}
PROTOCOLS = {"tcp", "udp", "icmp", "http", "https", "ftp", "ssh", "tls", "ssl", "dns"}

def infer_value_type(values: List[str]) -> str:
    if not values:
        return "text"
        
    val = values[0].strip()
    
    if IPV4_RE.match(val):
        return "ipv4"
        
    if MAC_RE.match(val):
        return "mac"
        
    if TIMESTAMP_RE.match(val):
        return "timestamp"
        
    if URL_RE.match(val):
        return "url"
        
    if PATH_RE.match(val):
        return "path"
        
    if NUMERIC_RE.match(val):
        num = float(val)
        # Check port heuristic
        if 0 <= num <= 65535 and "." not in val:
            # We can't definitely say it's a port without context, but we will return numeric 
            # and let the semantic mapper contextualize it, or return a combined type.
            # The TRD says "Integer within 0-65535, positionally adjacent to an address".
            # For now, if it's small, it's numeric, semantic mapping will help.
            return "numeric"
        return "numeric"
        
    val_lower = val.lower()
    
    if val_lower in {"true", "false", "yes", "no", "1", "0", "t", "f"}:
        return "boolean"
        
    if val_lower in ACTIONS:
        return "action"
        
    if val_lower in SEVERITIES:
        return "severity"
        
    if val_lower in PROTOCOLS:
        return "protocol"
        
    return "text"
