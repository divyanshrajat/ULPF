# ULPF V2 Rule Format

A ULPF V2 deterministic rule defines how the Data Plane parses an incoming raw log line into a canonical JSON structure.

## JSON Schema Example
```json
{
  "parser_type": "regex",
  "config": {
    "pattern": "^(?P<timestamp>\\S+) (?P<src_ip>\\d+\\.\\d+\\.\\d+\\.\\d+) (?P<action>\\w+)$"
  },
  "mapping": {
    "timestamp": "event.time",
    "src_ip": "src_endpoint.ip",
    "action": "event.action"
  },
  "required_fields": ["event.time", "src_endpoint.ip"]
}
```

## Fields
- **`parser_type`**: `regex` (for unstructured text/syslog) or `jsonpath` (for nested JSON logs).
- **`config`**: 
  - If `regex`: Requires a `pattern` string using Python-style named capture groups `(?P<name>pattern)`.
  - If `jsonpath`: Requires a `paths` object mapping keys to JSONPath expressions.
- **`mapping`**: A dictionary mapping the extracted variable names (e.g., `src_ip`) to the standard OCSF taxonomy fields (e.g., `src_endpoint.ip`).
- **`required_fields`**: A list of OCSF fields that MUST be successfully extracted for the parsing to be considered valid.

Any extracted fields that are NOT explicitly mapped in the `mapping` dictionary will be automatically appended to the `unmapped_fields` namespace to ensure zero data loss.
