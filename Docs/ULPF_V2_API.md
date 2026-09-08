# ULPF V2 API Specification

## 1. Onboarding (Control Plane)
- `POST /api/v1/onboarding/{source_id}/draft`: Submits a list of raw log sample strings. Synchronously invokes the local Qwen LLM to return a drafted deterministic rule JSON configuration.
- `POST /api/v1/onboarding/{source_id}/validate`: Validates a provided rule JSON config against a list of sample strings to confirm no `required_fields` are missed.
- `POST /api/v1/onboarding/{source_id}/approve`: Commits a drafted rule to the Data Plane Rule Registry and increments the active version.

## 2. Rule Registry
- `GET /api/v1/rules`: Lists all rule versions across all sources.
- `GET /api/v1/rules/{rule_id}`: Retrieves the detailed JSON configuration of a specific rule.

## 3. Events (Data Plane Queries)
- `GET /api/v1/events`: Search and filter normalized OCSF events stored in the OpenSearch backend.
- `GET /api/v1/events/{trace_id}`: Trace a specific event, returning the raw payload, the parsed result, and the cryptographic hash from the vault.

## 4. Sources
- `GET /api/v1/sources`: List all configured sources (e.g. Cisco ASA, Palo Alto, AWS VPC Flow).
- `POST /api/v1/sources`: Create a new source.
