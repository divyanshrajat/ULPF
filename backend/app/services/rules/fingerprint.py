import re

# Pre-compiled regexes for common token types
TOKEN_TYPES = [
    ("IP", re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b|\b(?:[A-Fa-f0-9]{1,4}:){7}[A-Fa-f0-9]{1,4}\b')),
    ("TIME", re.compile(r'\b\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\b')),
    ("NUM", re.compile(r'\b\d+\b')),
    ("HEX", re.compile(r'\b(?:0x)?[a-fA-F0-9]{8,}\b')),
    ("UUID", re.compile(r'\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b')),
    ("MAC", re.compile(r'\b(?:[0-9A-Fa-f]{2}[:-]){5}(?:[0-9A-Fa-f]{2})\b')),
    ("URL", re.compile(r'\bhttps?://[^\s/$.?#].[^\s]*\b')),
    ("EMAIL", re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')),
]

def generate_fingerprint(raw_event: str, vendor_token: str = "") -> str:
    """
    Generates a deterministic structural fingerprint from a raw log event.
    Example input: "2023-10-27 10:00:00 INFO User admin logged in from 192.168.1.10"
    Example output: "<TIME> <WORD> <WORD> <WORD> <WORD> <WORD> <WORD> <IP>"

    vendor_token: an opaque string (e.g. source_id or vendor name) prepended to the
    fingerprint so that two sources with structurally identical logs but different vendors
    never collide (T37 fingerprint collision hardening).
    """
    import hashlib
    # Simple JSON fingerprinting (basic structural extraction without values)
    if raw_event.strip().startswith("{") and raw_event.strip().endswith("}"):
        structural = _generate_json_fingerprint(raw_event.strip())
    else:
        # Syslog / unstructured fingerprinting
        structural = raw_event

        # Replace known complex tokens first
        for token_name, pattern in TOKEN_TYPES:
            structural = pattern.sub(f"<{token_name}>", structural)

        # Replace remaining word blocks
        structural = re.sub(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', '<WORD>', structural)

        # Collapse multiple spaces
        structural = re.sub(r'\s+', ' ', structural).strip()

    if vendor_token:
        # Prefix with a short hash of vendor_token so the composite is vendor-scoped
        vhash = hashlib.sha256(vendor_token.encode()).hexdigest()[:8]
        return f"{vhash}::{structural}"
    return structural

def _generate_json_fingerprint(raw_json: str) -> str:
    import json
    try:
        parsed = json.loads(raw_json)
        return _traverse_json(parsed)
    except json.JSONDecodeError:
        return "<INVALID_JSON>"

def _traverse_json(obj: any, prefix: str = "") -> str:
    if isinstance(obj, dict):
        keys = sorted(obj.keys())
        structs = [f"{k}:{_traverse_json(obj[k])}" for k in keys]
        return "{" + ",".join(structs) + "}"
    elif isinstance(obj, list):
        if len(obj) == 0:
            return "[]"
        # Collect unique type signatures across all elements (T38 heterogeneous fix).
        # Sorting gives a deterministic fingerprint regardless of element ordering.
        signatures = sorted({_traverse_json(item) for item in obj})
        return "[" + "|".join(signatures) + "]"
    else:
        # Scalar
        if isinstance(obj, bool):
            return "<BOOL>"
        elif isinstance(obj, int) or isinstance(obj, float):
            return "<NUM>"
        elif isinstance(obj, str):
            for token_name, pattern in TOKEN_TYPES:
                if pattern.fullmatch(obj):
                    return f"<{token_name}>"
            return "<STR>"
        elif obj is None:
            return "<NULL>"
        else:
            return "<UNKNOWN>"
