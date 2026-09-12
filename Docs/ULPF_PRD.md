# ULPF — Product Requirements Document (Gap-Corrected)

**Status:** Supersedes/complements `ULPF_PRD.pdf` for engineering purposes. This version is written against the actual state of the `divyanshrajat/ULPF` repository as audited on 2026-09-10, cross-checked line-by-line against `ULPF_Full_Understanding_Document.pdf`.
**Owner:** Team S.W.O.R.D. — SIH26156 (NTRO)
**Audience:** Engineering team implementing the fixes in `implementation.md` / `task.md`.

---

## 1. Purpose

ULPF ingests logs from perimeter security devices (firewall, router, VPN, IDS/IPS, WAF, proxy, cloud edge), preserves the exact raw bytes before any transformation, extracts fields through a versioned, human-approved parsing rule, normalizes into a common taxonomy, and exports to SIEM/data-lake/analytics systems — without ever putting an LLM in the production hot path.

This PRD exists because the current repository **implements the shape of this system but not its guarantees**. Several requirements marked "Yes" in the team's own Section 22 coverage table (in the understanding document) are not actually true of the running code today. This document restates requirements at the level of "what must be true for a reviewer/evaluator to verify it," not "what module exists."

---

## 2. Requirement Coverage — Corrected

Re-scored against `SIH26156` "Expected Solutions," based on actual code inspection, not design intent.

| # | Requirement | Doc's self-score | **Actual score** | Why |
|---|---|---|---|---|
| (a) | Preserve complete raw event data without loss | Yes | **Partial** | Raw bytes are hashed and written write-once to local disk — good. But the hash is never re-verified on read (`vault.verify_digest()` is defined, never called), so "verified losslessness" is not actually enforced. |
| (b) | Extract and parse source-specific attributes | Yes | **Partial** | Only `regex` and `jsonpath` parsers are real. `cef`/`leef`/`keyvalue`/`xml` silently degrade to the regex parser and will raise `ParserError` on any definition that isn't a bare regex pattern. |
| (c) | Normalize into a common taxonomy | Yes | **No** | There is no OCSF or ECS adapter. `target_schema` is stored on the rule but never changes normalization behavior. Every event is emitted in one ad-hoc shape labeled `"ulpf-core-1.0"`. |
| (d) | Maintain traceability | Yes | **Partial** | `event_id` → raw hash → rule id/version/hash chain exists structurally, but the hash is unverified on read (see (a)). |
| (e) | Plug-and-play onboarding | Yes | **No (as shipped)** | The onboarding flow (fingerprint → LLM draft → validate → approve) exists, but the LLM is mocked by default (`ULPF_MOCK_LLM=true` in `docker-compose.yml` and `.env.example`) and the mock is a hardcoded string-matcher for the team's own demo samples only. It cannot onboard a genuinely new format. |
| (f) | Unified visibility | Partial | **Partial** | Studio/Rules/Jobs/Events/ApiKeys pages exist; no cross-source correlation dashboard; no Sessions page in the frontend despite a Sessions API existing. |
| (g) | SIEM / data-lake integration | Yes | **Partial** | OpenSearch indexing exists (best-effort, swallowed on failure). No Kafka/Redpanda export path exists anywhere in the code. |
| (h) | AI/ML-ready analytics | Partial | **No** | No ML/analytics workflow of any kind is implemented; normalized data sits in a Postgres JSONB column. |
| (i) | Reduced parser development effort | Yes | **No (as shipped)** | Same root cause as (e) — the authoring agent that is meant to remove hand-written parser work is mocked by default. |
| (j) | Air-gapped deployment | Yes | **Partial** | `airgap/export_bundle.sh` bundles Docker images but does **not** bundle the actual `.gguf` model weights — a separate manual step. `ULPF_MODE=airgap` exists as a setting but nothing in the code branches on it to disable network calls; it is an unenforced flag. |
| (k) | Container packaging | Yes | **Yes** | `Dockerfile.app` + `docker-compose.yml` genuinely build and run the stack. No Kubernetes manifests exist despite being named in the stack reference. |

**Net:** of 11 requirements, **1 is fully met (k)**, **6 are partial**, **4 are not met as currently configured**. This is the single most important number in this document — treat "9 of 11 covered" from the understanding doc as a design claim, not a verified fact.

---

## 3. Functional Requirements (restated, verifiable)

### FR-1 Raw Evidence Preservation
- FR-1.1 Every ingested event's exact byte payload MUST be written to storage before any parsing, decoding, or transformation touches it.
- FR-1.2 A SHA-256 digest MUST be computed at write time and stored alongside the raw reference.
- FR-1.3 **[NEW, currently missing]** Any API that serves a raw payload back to a caller MUST re-compute the digest and include a `digest_verified: true/false` field in the response. Silently trusting the write-time hash forever is not acceptable for an evidentiary system.
- FR-1.4 Raw objects MUST be immutable (write-once). Overwriting an existing `trace_id` MUST fail loudly (this already works — `FileExistsError` in `vault.py`).

### FR-2 Deterministic Parsing
- FR-2.1 The system MUST support, as first-class parser types with dedicated implementations: `regex`, `jsonpath`, `cef`, `leef`, `syslog` (RFC3164/RFC5424), `keyvalue`, `xml`/`xpath`.
- FR-2.2 Every regex-based parser type MUST enforce a compile-time complexity check and a per-event execution timeout (target: RE2 engine, or a timeout-guarded `re` fallback with a documented list of unsafe constructs rejected at validation time).
- FR-2.3 A rule declares `required_fields`; failure to extract any of them MUST route the event to `unresolved`, never to a partially-normalized "success."

### FR-3 Rule Registry & Lifecycle
- FR-3.1 States: `DRAFT → PENDING_REVIEW → ACTIVE → DEPRECATED → ARCHIVED`, with `DISABLED` reachable from `ACTIVE`/`DEPRECATED` and `REJECTED` reachable from `PENDING_REVIEW`. (Full state machine in `rule.md`.)
- FR-3.2 Exactly one `ACTIVE` version per logical rule MUST be enforced **at the database level** (partial unique index), not only in application code, to survive concurrent approval requests.
- FR-3.3 Auto-detection (fingerprint matching) MUST only consider `ACTIVE` rules.
- FR-3.4 A `DISABLED` rule MUST be rejected even when called by explicit `rule_id`.

### FR-4 Local Rule Authoring Agent
- FR-4.1 The production default MUST be the real local model path (`ULPF_MOCK_LLM=false`), with mock mode clearly labeled as a *developer convenience only*, never the default in `docker-compose.yml` or `.env.example`.
- FR-4.2 Samples MUST be redacted for obvious secrets (`Authorization:`, `Bearer `, `password=`, cookie headers, etc.) before being placed in a prompt.
- FR-4.3 The LLM's JSON output MUST pass a structural validator that rejects: any key/value containing `exec`, `eval`, `import `, `subprocess`, `os.system`, shell metacharacters, SQL keywords outside of string literals, `http://`/`https://` URLs, or anything resembling a credential — before it is ever persisted as a `DRAFT`.
- FR-4.4 On deterministic validation failure, the system MUST retry generation up to 2–3 times with structured error feedback appended to the prompt, before falling back to `unresolved`/manual authoring.
- FR-4.5 Every generation attempt (success or failure) MUST be recorded in `rule_llm_generations` including model name, quantization, and prompt/response — this table exists but nothing currently writes to it.

### FR-5 Batch & Streaming Ingestion
- FR-5.1 Sample-detect-lock-fastpath-spotcheck lifecycle, as currently implemented in `jobs.py`/`sessions.py`, is functionally acceptable for MVP but MUST move to the adaptive spot-check table (1-in-50 immediately after lock, 1-in-500 stable, 1-in-25 after a mismatch, unlock after repeated mismatches) instead of a flat 1-in-50.
- FR-5.2 **[NEW]** A true streaming ingestion path (persistent connection, not a REST call with a list of strings) is required if "session" is to mean anything different from "job." Until implemented, document this explicitly as a known simplification.

### FR-6 Authentication, Authorization & Multi-tenancy
- FR-6.1 **[P0 — currently absent]** No request MUST be able to self-declare its own role via a client-supplied header. Role/identity MUST be derived from a verified credential (session token, signed JWT, or validated API key) on the server side only.
- FR-6.2 **[P0 — currently absent]** Every ingestion endpoint (`/jobs`, `/sessions/*`, syslog listener once wired) MUST validate the caller's API key against the `api_keys` table and MUST enforce `source_scope` — a key scoped to one source cannot push/pull another source's data.
- FR-6.3 **[P1]** If genuine multi-tenant isolation is in scope for a "fully working prototype" (the doc's Section 13 explicitly requires `tenants` + RLS), add a `tenants` table and scope all rule/event/job/session queries by tenant. If multi-tenancy is explicitly out of scope for the hackathon MVP, this PRD requires that decision be written down (see Section 6) rather than left ambiguous.

### FR-7 Normalization & Schema Adapters
- FR-7.1 A rule's `target_schema` (`ocsf` | `ecs`) MUST actually select a distinct adapter that renames/reshapes fields into that taxonomy's field names (e.g., OCSF `src_endpoint.ip` vs. ECS `source.ip`), not just a label on an otherwise-identical payload.
- FR-7.2 Unmapped vendor fields MUST continue to be preserved under a `vendor`/source-namespaced extension key (this already works).

### FR-8 Observability
- FR-8.1 `/api/v1/system/health` MUST report the actual, live status of Postgres, Redis, and OpenSearch — not hardcoded `"healthy"` strings.
- FR-8.2 The `fast_events` / `adaptive_events` counters MUST use the same string constant the pipeline actually writes (`fast_path`, not `fast`).

---

## 4. Non-Functional Requirements

| Category | Requirement | Current Status |
|---|---|---|
| Security | No client-controlled privilege escalation | **Failing** — see FR-6.1 |
| Security | ReDoS resistance on all regex rules | **Failing** — no timeout, no RE2 |
| Durability | No data loss on process crash mid-ingestion | **Failing** — in-memory `asyncio.Queue`, no persistence |
| Air-gap | Zero outbound network calls when `ULPF_MODE=airgap` | **Unenforced** — flag exists, nothing checks it |
| Scale | Documented, measured throughput; no invented benchmark numbers | Not yet measured — must be added before claiming "billions/day" |
| Auditability | Every rule lifecycle transition is attributable to a real actor | **Partial** — `RuleLifecycleEvent` is written, but `actor` is always the fake `"admin"` header value today |

---

## 5. Explicitly Out of Scope (for the hackathon submission, to keep task.md realistic)

Call these out as accepted MVP limitations rather than silent gaps:
- ClickHouse (Postgres JSONB is acceptable for MVP data volumes).
- Kubernetes manifests (Docker Compose is sufficient for the demo).
- Full Kafka/Redpanda swap — acceptable to defer *if* the in-memory queue's data-loss risk is explicitly documented as a known limitation (it currently is not documented anywhere).
- True multi-tenancy / RLS — acceptable to defer *if* explicitly written down as single-tenant for this submission.

## 6. Open Decisions (need an owner before `task.md` items can be closed)

1. Is multi-tenancy in scope for submission, or is ULPF explicitly single-tenant for SIH26156? (Drives FR-6.3.)
2. Is the in-process queue an accepted MVP limitation, or does Kafka/Redpanda need to land before demo day? (Drives task priority P1 vs P2 in `task.md`.)
3. Who owns downloading/verifying the Qwen2.5-Coder-7B GGUF model and testing real (non-mock) generation before the demo? This is currently untested in the repository — no evidence any real (non-mock) LLM generation has ever succeeded.

---

## 7. Acceptance Criteria for "Fully Working Prototype" (not demo)

A build is considered a **fully working prototype** (as distinct from a demo) when, without code changes:
1. A brand-new, previously-unseen log format can be onboarded end-to-end using the **real** local LLM (mock disabled), including at least one retry-on-validation-failure cycle.
2. An unauthenticated request to any mutating endpoint is rejected with 401/403.
3. An API key scoped to source A cannot submit or read data for source B.
4. Killing the app process mid-batch-job does not silently drop already-accepted events (either via persistence or an explicit documented at-least-once/at-most-once contract).
5. `/api/v1/system/health` reflects a real outage when Postgres, Redis, or OpenSearch is stopped.
6. At least one CEF and one LEEF sample parse through a dedicated (non-regex-fallback) parser.
7. The traceability endpoint reports `digest_verified` computed at request time, not just the stored value.

None of these currently pass. `task.md` is organized to close them in priority order.
