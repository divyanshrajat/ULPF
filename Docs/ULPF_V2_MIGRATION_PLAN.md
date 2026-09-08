# ULPF V2 Migration Plan

## 1. Existing Architecture
The current ULPF architecture relies heavily on an active "hot path" LLM and AI-based template discovery mechanisms (Drain3, SentenceTransformers). 
The legacy architecture pipeline operates as follows:
- Ingestion → `RawIndex` (Storage)
- Discovery (Drain3) extracts templates (`Template` model).
- Extraction & Mapping semantic pipeline uses NLP to guess field mapping (`Mapping` model).
- Production traffic uses this mapped template pipeline.

## 2. Target Architecture
The revised ULPF V2 architecture introduces a strict separation between the **Data Plane** and **Control Plane**, ensuring high performance, determinism, and security in production.

**Data Plane (Hot Path):**
- Ingestion Gateway (Syslog / REST / Batch / Streaming)
- Raw Evidence Immutable Vault (Exact bytes + SHA-256)
- Fingerprint + Rule Detection
- Active Rule Registry Lookup
- Deterministic Rule Engine (Regex, JSONPath, CEF, LEEF, Syslog, XML, KV)
- Canonical Event Model Normalization (OCSF + ECS Adapter)
- Traceability + Governance (event_id, raw_hash, rule_id, rule_version)
- Delivery (OpenSearch, ClickHouse, Kafka/Redpanda)

**Control Plane (Onboarding):**
- Fingerprint Miss Detection
- Local Rule Authoring Agent (Qwen2.5-Coder-7B GGUF via llama.cpp)
- Candidate Rule Declarative JSON Generation
- Structural and Golden Test Validation
- Human Review & Approval (DRAFT → PENDING_REVIEW → ACTIVE)

## 3. Component Mapping & Migration Strategy

### A. What Can Be Reused
- **FastAPI Application:** Routing, middleware, and lifecycle hooks.
- **React SPA:** Frontend framework, layout, styling, and Vite build pipeline.
- **PostgreSQL & SQLAlchemy:** Core database connectivity and Alembic setup.
- **Raw Evidence Concepts:** Existing `RawIndex` and `Trace` models.
- **Docker Infrastructure:** Basic `docker-compose.yml` structure.
- **OpenSearch Integration:** If present, can be repurposed for delivery.

### B. What Must Be Modified
- **Ingestion Pipeline:** Must enforce exact byte preservation and SHA-256 *before* any parsing.
- **API Endpoints:** Repurpose legacy `/api/v1/endpoints` and `/api/v1/onboarding` to match the new strict workflow.
- **Frontend Pages:** Refactor "Dashboard", "Review", and "Discovery" to focus on "Rule Registry", "Onboarding", and "Log Review". Remove Drain3/Semantic UI terminology.
- **Database Schema:** Redesign models for `Rules`, `RuleVersions`, `RuleFingerprints`, and Drop legacy `Template`/`Mapping`.

### C. What Must Be Deprecated/Deleted
- **Legacy AI Services:** `backend/app/services/discovery/`, `backend/app/services/extraction/`, `backend/app/services/mapping/`.
- **Legacy Dependencies:** `Drain3`, `SentenceTransformers`.
- **Legacy Models:** `Template`, `Mapping`, `ReviewItem`, `Field`.

### D. New Components Required
- **Rule Registry:** Domain models for Rules, Versions, Fingerprints, Test Cases, Validation Runs, Approvals, and Lifecycle Events.
- **Fingerprint Engine:** Deterministic structural fingerprinting logic.
- **Deterministic Rule Engine:** Parser factory supporting Regex, JSONPath, CEF, LEEF, Syslog, KV, XML.
- **Local Rule Authoring Agent:** Interface with `llama.cpp` using Qwen2.5-Coder-7B GGUF.
- **Validation Engine:** Strict declarative JSON validation and execution against golden samples.
- **OCSF/ECS Adapters:** Canonical model generators preserving `unmapped_fields`.

## 4. Database Migration Strategy
1. Create Alembic migration to introduce new core tables: `rules`, `rule_versions`, `rule_fingerprints`, `rule_test_cases`, `rule_validation_runs`, `rule_approvals`, `rule_lifecycle_events`, `rule_llm_generations`.
2. Migrate `RawIndex` and `Trace` references if necessary.
3. Introduce `normalized_events` modifications to support OCSF/ECS payload structures and `rule_id` references.
4. Drop legacy `Template`, `Mapping`, and `Field` tables once V2 paths are verified.

## 5. API Migration Strategy
1. **Ingestion:** `/v1/convert`, `/v1/jobs`, `/v1/sessions`
2. **Onboarding:** `/v1/onboarding`, `/v1/onboarding/{id}/samples`, `/v1/onboarding/{id}/draft`, `/v1/onboarding/{id}/validate`, `/v1/onboarding/{id}/approve`
3. **Rule Registry:** `/v1/rules`, `/v1/rules/{id}/versions/...`
4. **Traceability:** `/v1/events/{id}`, `/v1/events/{id}/raw`, `/v1/events/{id}/trace`

## 6. Frontend Migration Strategy
- Remove references to "Templates" and "Mappings".
- Build **Onboarding Wizard**: Upload samples → Generate Fingerprint → Trigger Local LLM → Validate → Approve.
- Build **Rule Registry View**: Display active/inactive rules, JSON declarative schema, and parsers.
- Enhance **Log Review**: Side-by-side view of Raw (Hex/Text), Parsed Fields, OCSF, and Unmapped fields.

## 7. Testing & Deployment Migration
- Rewrite test suite focusing on: deterministic parsing, schema validation, and strict boundary enforcement (No LLM in hot path).
- Ensure `airgap` mode skips external network calls and strictly relies on mounted `.gguf` weights.
- Create explicit `docker-compose.demo.yml` for rapid evaluation.
