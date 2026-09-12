# ULPF V2 API Specification

## 1. Onboarding (Control Plane)
- `POST /api/v1/onboarding/{session_id}/samples?target_schema={schema}`: Submits a list of raw log sample strings to check if an active rule already matches the fingerprint for the requested schema.
- `POST /api/v1/onboarding/{session_id}/draft?target_schema={schema}`: Synchronously invokes the local Qwen LLM to return a drafted deterministic rule JSON configuration, forcing the schema to `target_schema`.
- `POST /api/v1/onboarding/{session_id}/validate`: Validates a provided rule JSON config against a list of sample strings to confirm no `required_fields` are missed.
- `POST /api/v1/onboarding/{session_id}/approve`: Commits a drafted rule to the Data Plane Rule Registry and increments the active version.

## 2. Ingestion (Data Plane Hot Path)
- `POST /api/v1/sessions`: Creates an ingestion session for streaming payloads.
- `POST /api/v1/sessions/{session_id}/events`: Accepts a micro-batch (JSON Array) of string payloads for fast-path parsing.
- `POST /api/v1/jobs?source_id={source_id}`: Uploads a bulk log file (CSV, JSONL, TXT) via `multipart/form-data` for batch parsing.

## 3. Rule Registry
- `GET /api/v1/rules`: Lists all rule versions across all sources.
- `GET /api/v1/rules/{rule_id}`: Retrieves the detailed JSON configuration of a specific rule.

## 4. Events (Data Plane Queries)
- `GET /api/v1/events`: Search and filter normalized OCSF/ECS events stored in the OpenSearch backend.
- `GET /api/v1/events/{trace_id}`: Trace a specific event, returning the raw payload, the parsed result, and the cryptographic hash from the vault.

## 5. Sources
- `GET /api/v1/sources`: List all configured sources (e.g. Cisco ASA, Palo Alto, AWS VPC Flow).
- `POST /api/v1/sources`: Create a new source.
