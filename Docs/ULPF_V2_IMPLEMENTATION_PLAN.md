# ULPF Implementation / Remediation Plan

Companion to `prd.md` (what must be true) and `rule.md` (rule format spec). This document is organized by subsystem; each item names the exact file, the current behavior, why it's wrong, and the concrete fix. `task.md` turns this into a prioritized, checkable backlog.

---

## 1. Security — Authentication & Authorization (P0, blocking)

### 1.1 Client-controlled role header
**File:** `backend/app/core/auth.py`
**Current:** `get_current_user()` accepts an `X-ULPF-Role` header from the caller and grants that role with zero verification if no HTTP Basic credential is presented. The single hardcoded Basic user (`admin` / `settings.ADMIN_PASSWORD`) is the *only* real credential in the system.
**Why it's broken:** Any HTTP client can set `X-ULPF-Role: administrator` and pass every `require_admin`/`require_approver` check.
**Fix:**
1. Delete the header-based identity branch entirely (lines handling `x_ulpf_user`/`x_ulpf_role`).
2. Require HTTP Basic (or better, a signed session/JWT issued at login) on every mutating route.
3. Add a real `users` table (username, password hash, role) instead of the single in-memory `_USERS` dict, so roles are assignable without a redeploy.
4. Return `401` with `WWW-Authenticate: Basic` for any mutating call with no credential — do not default to an anonymous "viewer" that mutating endpoints still happen to allow through if a dependency is missing.

### 1.2 Frontend hardcodes admin identity
**File:** `frontend/src/services/api.ts` (lines 28-29 and 214-215)
**Current:** Every request the SPA makes sends `X-ULPF-User: admin`, `X-ULPF-Role: administrator` hardcoded in the Axios/fetch client config.
**Fix:** Build a real login screen (username/password → Basic auth header or a session cookie/JWT stored in memory, never in `localStorage`). Remove the hardcoded headers. Until backend RBAC is meaningful (1.1), this is purely cosmetic — fix 1.1 first, then this.

### 1.3 API keys are generated but never checked
**File:** `backend/app/api/api_keys.py` (generation/storage only), `backend/app/api/jobs.py`, `backend/app/api/sessions.py`, `backend/app/api/sources.py` (no auth dependency anywhere)
**Current:** `POST /api-keys` creates and SHA-256-hashes a key. No endpoint has a dependency that re-hashes an incoming `Authorization: Bearer <key>` and compares it, and no endpoint reads `source_scope` to restrict which `source_id` a key may act on. The README documents Bearer-auth usage that does nothing server-side.
**Fix:**
1. Add `verify_api_key(authorization: str = Header(...), db: Session = Depends(get_db)) -> ApiKey` dependency: strip `Bearer `, hash it, look up by `key_hash`, reject if missing/`status != "active"`.
2. Apply this dependency to `POST /jobs`, `POST /sessions`, `POST /sessions/{id}/events`, and the (currently unwired) syslog/file ingestion paths.
3. Enforce scope: if `api_key.source_scope not in ("*", requested_source_id)`, return `403`.
4. Update `last_used_at` on successful use.

### 1.4 Multi-tenancy (decide scope first — see `prd.md` §6 Open Decision 1)
**File:** `backend/app/models/domain.py` (no `tenants`/`users` tables at all)
**Fix if in scope:** add `Tenant` model, add `tenant_id` FK to `Source`, `Rule`, `IngestionJob`, `IngestionSession`, `ApiKey`; enforce via Postgres Row-Level Security (`CREATE POLICY ... USING (tenant_id = current_setting('app.tenant_id')::text)`), set `app.tenant_id` per request in a DB session hook. **If out of scope for this submission,** document "ULPF is single-tenant for the SIH26156 MVP; multi-tenancy is roadmap" in the README and PRD, and remove the false impression created by the doc's Section 13 claiming full tenant isolation.

---

## 2. Rule Authoring Agent (LLM) (P0/P1)

### 2.1 Mock is the default, not a fallback
**Files:** `docker-compose.yml` (`ULPF_MOCK_LLM=${ULPF_MOCK_LLM:-true}`), `backend/.env.example` (`ULPF_MOCK_LLM=true`)
**Fix:** Flip both defaults to `false`. Ship a documented, tested procedure (already drafted in the newer README's Air-Gap section) for placing the real `.gguf` file at `/models/qwen.gguf` before first run. Keep mock mode available but opt-in and clearly labeled `ULPF_MOCK_LLM=true  # dev-only, non-functional for real onboarding`.

### 2.2 Mock generator is hardcoded string-matching, not a stand-in model
**File:** `backend/app/authoring/agent.py::_mock_generate` (lines 83-205)
**Current:** `if "PAN" in s`, `if "ASA" in s`, `if "sensor-0029" in s or "link_flap" in s`, `if "LEEF:" in s` — literal substring checks tied to the team's own demo log samples.
**Fix:** This is fine *as a unit-test fixture* (rename it clearly, e.g. `tests/fixtures/canned_llm_responses.py`) but must not be reachable from a production config, and should not be presented as "AI-assisted onboarding" in a demo without disclosing it's a canned response. Once 2.1 lands, this code path only matters for CI.

### 2.3 No structural/forbidden-content validation of LLM output
**File:** `backend/app/api/onboarding.py::generate_draft_rule` (calls `create_rule_version` directly on raw `rule_json`)
**Fix:** Implement `validate_rule_json()` per `rule.md` §3 in a new `backend/app/services/rules/safety.py`, call it before `create_rule_version`. On violation, do not persist a `DRAFT`; return `422` with the violation list and record a `rule_llm_generations` row with `success=False`.

### 2.4 No secret redaction before prompting
**File:** `backend/app/authoring/prompt.py::build_prompt`
**Fix:** Add a `redact_secrets(sample: str) -> str` pass (regex for `Authorization:`, `Bearer `, `Cookie:`, `password=`, AWS key patterns, JWTs) applied to every sample before it's interpolated into the prompt string.

### 2.5 No retry loop on validation failure
**File:** `backend/app/api/onboarding.py::validate_rule` (returns `passed=False` and stops)
**Fix:** When validation fails, feed the structured failure (`missing required fields`, `regex did not match`, sample index) back into a follow-up prompt and re-invoke `generate_rule_from_samples`, capped at 2 additional attempts (matches doc §8 step 7). Persist each attempt as its own `rule_llm_generations` row.

### 2.6 `rule_llm_generations` table is never written
**File:** `backend/app/api/onboarding.py`
**Fix:** Insert a row on every call to `generate_rule_from_samples` (success and failure), storing `prompt`, `response_json`, `success`, `error_message`. This is required for the doc's own provenance requirement (§8 step 9) and for 2.5's retry bookkeeping.

### 2.7 Sample count minimum not enforced
**File:** `backend/app/api/onboarding.py::upload_samples` (`if not samples or len(samples) < 1`)
**Fix:** Require `len(samples) >= 3` before allowing `POST /{session_id}/draft`, matching doc §8 step 1 ("3–5 representative samples").

---

## 3. Deterministic Parsers (P1)

### 3.1 CEF/LEEF/keyvalue/XML silently fall back to regex
**File:** `backend/app/services/rules/parsers/factory.py` (lines 17-20)
**Fix:** Implement real parsers:
- `CefParser`: split on unescaped `|`, parse the 7 CEF header fields + `key=value` extension string.
- `LeefParser`: same idea for `LEEF:version|vendor|product|version|eventid|extensions`.
- `KeyValueParser`: tokenize on whitespace, split each token on the first `=`, respecting quoted values.
- `XmlParser`: use `xml.etree.ElementTree` (already imported in the unused `classifier.py` — reuse it) with XXE disabled (`defused xml` or manually disable entity resolution) and an XPath-like dotted-path field mapping.
Until these exist, change the factory's fallback branch to `raise ValueError(f"Parser type '{parser_type}' has no implementation yet")` instead of silently substituting `RegexParser` — a loud failure during onboarding is much better than a rule that appears to validate and then breaks in production.

### 3.2 No ReDoS protection
**File:** `backend/app/services/rules/parsers/regex_parser.py`
**Fix (pick one):**
- **Preferred:** swap `re` for the `google-re2` binding (linear-time by construction, no catastrophic backtracking possible) for all rule-authored patterns. Requires adding `google-re2` to `requirements.txt`; some capture-group features differ slightly from `re` — audit `field_mappings` usage against re2's supported syntax.
- **Fallback if RE2 isn't available for target patterns:** wrap `self.regex.search()` in a hard wall-clock timeout (e.g., run in a `ProcessPoolExecutor` with `.result(timeout=parser_def.get("timeout_ms", 25)/1000)`), and add a compile-time complexity check rejecting nested quantifiers like `(a+)+` before a rule can leave `DRAFT`.

### 3.3 No type-constraint checking
**File:** `backend/app/services/rules/parsers/base.py` / new `type_check.py`
**Fix:** After a parser extracts fields, run declared `type_constraints` (`ipv4_or_ipv6`, `int`, `iso8601`, `mac`, `uuid`) against extracted values; treat a mismatch the same as a missing required field (route to `unresolved`, don't silently coerce or pass through).

### 3.4 Duplicated required-field validation logic
**Files:** `workers/processor.py`, `api/jobs.py`, `api/sessions.py`, `api/onboarding.py` (each reimplements the same `for req in required_fields: if req not in parsed_data` loop)
**Fix:** Extract to `services/rules/validation.py::check_required_fields(parsed, required_fields) -> list[str]` (returns missing fields) and call it from all four sites. Reduces drift risk when the check needs to change (e.g., to add type-constraint checking from 3.3).

---

## 4. Ingestion Pipeline Consistency (P1)

### 4.1 `gateway.py`, `syslog_server.py`, `file_watcher.py` are dead code
**Files:** `backend/app/services/ingestion/gateway.py`, `syslog_server.py`, `file_watcher.py`; `backend/app/main.py` (`startup_event` only starts `worker_loop()`)
**Current:** Docker exposes port `5140/tcp` and `5140/udp` for syslog, but nothing calls `start_syslog_servers()`. `gateway.process_ingestion()` — the intended single ingestion entry point — is never called by `jobs.py`/`sessions.py`, which duplicate its logic inline instead (and use `uuid4()` for `trace_id` where `gateway.py` uses `ulid.new()` — two different ID schemes for the same concept across the codebase).
**Also:** `gateway.py` constructs `Trace(..., file_id=file_id, ...)`, but the `Trace` model in `models/domain.py` has no `file_id` column — this will raise `TypeError` the moment it's actually invoked. It has never been exercised end-to-end.
**Also:** `file_watcher.py` imports `watchfiles`, which is **not in `requirements.txt`** — importing this module today raises `ModuleNotFoundError`.
**Fix:**
1. Decide: either (a) make `gateway.process_ingestion()` the one real ingestion entry point and refactor `jobs.py`/`sessions.py`/`syslog_server.py`/`file_watcher.py` to call it (removing the duplicated inline logic and unifying on ULID trace IDs), or (b) if the syslog/file-watch paths are not needed for the submission, delete them and drop the unused `5140` port mappings from `docker-compose.yml`/`Dockerfile.app` so the exposed surface matches what's real.
2. If keeping file-watcher: add `watchfiles` to `requirements.txt`.
3. If keeping `gateway.py`: remove the non-existent `file_id` kwarg or add the column.
4. Wire whichever paths are kept into `main.py`'s `startup_event` via `asyncio.create_task(...)`.

### 4.2 Format classifier is unused
**File:** `backend/app/services/detection/classifier.py`
**Fix:** Either wire `classify_format()` into the onboarding flow (to pre-label a sample's format before fingerprinting/LLM drafting — useful for the CEF/LEEF parsers in 3.1) or delete it. An unused, untested "S2 Format Detection Engine" that the architecture diagram claims exists is worse than not claiming it.

---

## 5. Normalization & Schema Adapters (P1)

**File:** `backend/app/services/normalization/engine.py`
**Current:** Hardcodes `event.normalization["schema"] = "ulpf-core-1.0"` regardless of the rule's `target_schema`. No OCSF field-name mapping (e.g., `src_endpoint.ip`, `activity_id`, `category_uid`), no ECS field-name mapping (`source.ip`, `event.action`).
**Fix:**
1. Define two adapter functions, `to_ocsf(canonical_event) -> dict` and `to_ecs(canonical_event) -> dict`, each doing a field-name/shape remap from the existing internal canonical representation.
2. Branch on `rule_version.target_schema` at the end of `NormalizationEngine.normalize()` to pick the adapter.
3. Decide (and document in `prd.md`) whether every event gets both representations or a rule is pinned to exactly one — the understanding document itself flags this as an open question (§23.2); resolve it before building the adapters, not after.

---

## 6. Queue / Durability (P1, or explicitly document as accepted limitation — see `prd.md` §6)

**File:** `backend/app/core/queue.py` (`InMemoryEventQueue` wraps `asyncio.Queue`)
**Fix (if pursuing):** Swap for a Redis-Streams-backed queue (Redis is already deployed and unused — see 8.2 — this is the lowest-effort durable option before a full Kafka/Redpanda migration) or add Kafka/Redpanda per the original doc. Either way: persisted, replayable, survives process restart.
**Fix (if deferring):** Add an explicit note to `README.md` and `prd.md`: "Current ingestion queue is in-memory; events accepted between the last DB commit and a process crash may be lost. Not suitable for production ingestion volumes." Silence on this point is the actual problem, not necessarily the architecture choice for an MVP.

---

## 7. Batch/Streaming Lock Logic (P2)

**Files:** `backend/app/api/jobs.py`, `backend/app/api/sessions.py` (both: `random.randint(1, 50) == 1` fixed spot-check rate; unlock threshold `mismatch_count >= 5` fixed)
**Fix:** Implement the adaptive table from the understanding document §10.1:
| Condition | Rate |
|---|---|
| Immediately after a lock | 1 in 50 |
| Stable, long-running fast path | 1 in 500 |
| Immediately after a mismatch | 1 in 25 |
| After repeated mismatches | unlock |

Track a `lock.events_since_lock` counter and `lock.events_since_mismatch` counter on `RuleLock` to pick the rate; this is a small, self-contained change once the columns are added.

**Also:** `sessions.py`'s `POST /{session_id}/events` accepts a JSON array in one request — it is a batch endpoint with a session id attached, not a persistent stream. If the demo narrative depends on "streaming," either add a WebSocket/SSE endpoint that keeps a connection open, or explicitly describe this as "micro-batch streaming" in documentation rather than implying a persistent connection.

---

## 8. Observability & Bug Fixes (P0 — small, fast, high-value)

### 8.1 `ParserError` NameError in the fast path
**File:** `backend/app/workers/processor.py` line 138: `except ParserError as e:` — `ParserError` is never imported (only `ParserFactory` is imported from `app.services.rules.parsers.factory`).
**Effect:** Every genuine parser failure on the fast path raises `NameError`, which the outer `except Exception` catches and misreports as a `NameError` dead letter instead of the real cause.
**Fix:** `from app.services.rules.parsers.base import ParserError` at the top of `processor.py`.

### 8.2 Fake health check
**File:** `backend/app/main.py::get_system_health` — hardcodes `"redis": "healthy", "opensearch": "healthy"`.
**Fix:** Actually ping both: `redis.Redis.from_url(settings.REDIS_URI).ping()` in a try/except, and `get_opensearch_client().ping()` in a try/except; report `"degraded"`/`"down"` on failure per-component.

### 8.3 `fast_events` counter always zero
**File:** `backend/app/main.py::get_stats_overview` — filters `NormalizedEvent.processing_path == 'fast'`, but the pipeline writes `'fast_path'` (`workers/processor.py`) or `'studio_test'` (`onboarding.py`).
**Fix:** Use the actual constant `'fast_path'`, and centralize these string literals as an enum/constants module (`PROCESSING_PATH_FAST = "fast_path"`, etc.) so this class of typo can't recur silently.

### 8.4 `verify_digest()` is dead code
**File:** `backend/app/services/preservation/vault.py::verify_digest` — defined, never called.
**Fix:** Call it from `api/events.py::get_event_raw` after reading the bytes back; include `"digest_verified": bool` in the response. This is the concrete fix behind `prd.md` FR-1.3.

### 8.5 Demo data seeded on every startup
**File:** `backend/app/main.py::startup_event` — always creates `paloalto`/`cloudtrail` demo sources/rules if missing.
**Fix:** Gate behind `settings.ULPF_MODE == "demo"` or a dedicated `ULPF_SEED_DEMO_DATA` flag, off by default in a "production" compose profile.

### 8.6 No dashboard/frontend page for Sessions
**File:** `frontend/src/pages/` (has `Jobs.tsx`, no `Sessions.tsx`) despite a working `api/sessions.py` backend.
**Fix:** Add `Sessions.tsx` mirroring `Jobs.tsx`'s lock/progress display, per the doc's §10.2 "Jobs & Sessions" combined vendor-portal screen.

### 8.7 Air-gap bundle omits the model weights
**File:** `airgap/export_bundle.sh` — saves only Docker images (`ulpf-app`, `postgres`, `redis`, `opensearch`); never copies `models/qwen.gguf` into the transferable artifact.
**Fix:** Add a step copying `./models/*.gguf` alongside `ulpf-airgap-bundle.tar`, and have `import_bundle.sh` place it at the path `ULPF_MODEL_PATH` expects before first container start.

---

## 9. Testing Gaps (P1/P2)

**Current:** `backend/tests/` totals 202 lines across 5 files; `test_e2e.py` explicitly skips LLM generation "to avoid dependency on the LLM model."
**Missing categories (per understanding doc §15.1), all currently absent:**
- Rule lifecycle: reject/disable/archive transitions (can't test what doesn't exist yet — depends on `rule.md` §4 fixes landing first)
- Malformed input: broken JSON/XML, invalid CEF escaping, partial/multi-line events
- Security regression: a ReDoS payload against a pathological pattern, an XML external-entity payload, a prompt-injection string embedded in a log sample
- Streaming: lock → spot-check mismatch → re-match → repeated-mismatch → unlock, asserted against actual counters, not just code-read
- Air-gap: process starts and serves `/api/health` with outbound network blocked (can be simulated with `iptables`/a Docker network with no internet route in CI)
- Multi-tenant isolation (once/if 1.4 lands): tenant A cannot read tenant B's events/rules
- Digest verification: tamper with a vault file after write, assert `digest_verified: false` on read (depends on 8.4 landing first)

**Fix:** Add one test file per category above under `backend/tests/`, wired into whatever CI exists (none was found in the repo — add a minimal GitHub Actions workflow running `pytest` on push if none exists).

---

## 10. Documentation Corrections (P2)

- `README.md` §9 previously listed known limitations (in the old V1 README) — the current V2 README dropped this section. Re-add a **Known Limitations** section covering: in-memory queue durability, mocked LLM default, missing OCSF/ECS field-level mapping, single-tenant only, CEF/LEEF/keyvalue/XML parser fallback behavior — so evaluators and future contributors aren't misled by the architecture diagrams into thinking these are solved.
- The team's own `ULPF_Full_Understanding_Document.pdf` §22 requirement coverage table should be updated to match `prd.md` §2's corrected scoring before submission, or evaluators who read both documents and inspect the code will find a credibility gap.
