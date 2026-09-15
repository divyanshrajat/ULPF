# ULPF — Product Requirements Document (Gap-Corrected)

**Status:** Supersedes/complements `ULPF_PRD.pdf` for engineering purposes. Originally written against the repository as audited on 2026-09-10, cross-checked line-by-line against `ULPF_Full_Understanding_Document.pdf`. **Updated after a second audit round** once a substantial fix pass landed — status tags below mark what changed. See `Docs/ULPF_V2_TASKS.md` for the live task-by-task checklist this document summarizes.
**Owner:** Team S.W.O.R.D. — SIH26156 (NTRO)
**Audience:** Engineering team implementing the fixes in `implementation.md` / `task.md`.

---

## 1. Purpose

ULPF ingests logs from perimeter security devices (firewall, router, VPN, IDS/IPS, WAF, proxy, cloud edge), preserves the exact raw bytes before any transformation, extracts fields through a versioned, human-approved parsing rule, normalizes into a common taxonomy, and exports to SIEM/data-lake/analytics systems — without ever putting an LLM in the production hot path.

This PRD exists because the repository, at the time of the first audit, **implemented the shape of this system but not its guarantees**. A second audit round confirmed a real fix pass closed most of those gaps — this version reflects that, while keeping a few genuinely still-open items honest rather than declaring victory across the board.

---

## 2. Requirement Coverage — Corrected

Re-scored against `SIH26156` "Expected Solutions," based on actual code inspection across two audit rounds.

| # | Requirement | Doc's self-score | **First audit** | **Now** | Why it changed |
|---|---|---|---|---|---|
| (a) | Preserve complete raw event data without loss | Yes | Partial | **Yes** | Digest is now actually re-verified on read (`vault.verify_digest()` wired into `events.py`, T28) — the original gap (hash computed once, never re-checked) is closed. |
| (b) | Extract and parse source-specific attributes | Yes | Partial | **Partial** | `cef`/`leef`/`keyvalue`/`xml` are now real dedicated parsers (T15-T18), not regex fallback — genuine progress. Still Partial because the LLM onboarding prompt only offers `regex, jsonpath, keyvalue, syslog` (syslog isn't even implemented) — the new parsers are reachable only via manually-authored rules, not the AI flow that's supposed to be the point (T52). |
| (c) | Normalize into a common taxonomy | Yes | No | **Partial** | Real OCSF and ECS adapters now exist and are actually wired via `target_schema` (T26/T27) — a genuine jump from "no adapter at all" to "field-renaming adapter." Still Partial, not Yes: no OCSF `class_uid`/`category_uid`/`activity_id` classification codes or ECS `event.category` arrays — known, documented limitation (L3). |
| (d) | Maintain traceability | Yes | Partial | **Yes** | Same fix as (a) — hash chain is now verified end to end, not just structurally present. |
| (e) | Plug-and-play onboarding | Yes | No (as shipped) | **Partial** | The mock LLM is off by default now (T10), redaction and a real retry loop exist (T11/T12). Still Partial: the forbidden-content safety check that's meant to gate a drafted rule before it becomes `DRAFT` never actually runs (T7/T51 — see below), and the sample-count floor is inverted, accepting as few as 1 sample instead of requiring 3+ (T14). |
| (f) | Unified visibility | Partial | Partial | **Partial** | A `Sessions.tsx` page now exists (T30), closing one concrete gap. No cross-source correlation dashboard yet. |
| (g) | SIEM / data-lake integration | Yes | Partial | **Partial** | A durable Redis Streams queue implementation has been written against the existing `EventQueue` interface (T32) — a real fix for the "events lost on crash" problem — but it hasn't been dropped into the running repo or verified against a live Redis yet. Still no Kafka/Redpanda, which is fine as a documented MVP choice. |
| (h) | AI/ML-ready analytics | Partial | No | **No** | Unchanged — no analytics/ML workflow exists; normalized data still sits in a Postgres JSONB column. Lowest-priority gap per the original coverage table, and it's stayed that way. |
| (i) | Reduced parser development effort | Yes | No (as shipped) | **Partial** | Same root fix as (e) — the authoring agent is genuinely functional now (real model, real parsers to target), but the same T7/T14/T52 caveats apply. |
| (j) | Air-gapped deployment | Yes | Partial | **Yes*** | `airgap/export_bundle.sh`/`import_bundle.sh` now actually bundle the `.gguf` model weights with checksums (T31) — the concrete gap named in the first audit is closed. *Not re-verified: whether `ULPF_MODE=airgap` is actually enforced anywhere in code, or remains a flag nothing branches on. |
| (k) | Container packaging | Yes | Yes | **Yes** | Unchanged. |

**Net: from "1 fully met, 6 partial, 4 not met" to roughly 4 fully met, 6 partial, 1 not met.** That's the single most important number to update if this table gets quoted anywhere external — the original "9 of 11" claim from the team's own understanding document is now much closer to true than it was at first audit, even if not exactly matching either self-score.

---

## 3. Functional Requirements (restated, verifiable) — status per item

### FR-1 Raw Evidence Preservation
- FR-1.1 Every ingested event's exact byte payload MUST be written to storage before any parsing, decoding, or transformation touches it. — **[Unchanged, already true]**
- FR-1.2 A SHA-256 digest MUST be computed at write time and stored alongside the raw reference. — **[Unchanged, already true]**
- FR-1.3 Any API that serves a raw payload back to a caller MUST re-compute the digest and include a `digest_verified: true/false` field in the response. — **[RESOLVED, T28]**
- FR-1.4 Raw objects MUST be immutable (write-once). — **[Unchanged, already true]**

### FR-2 Deterministic Parsing
- FR-2.1 Dedicated implementations for `regex`, `jsonpath`, `cef`, `leef`, `syslog`, `keyvalue`, `xml`/`xpath`. — **[PARTIAL]** All but `syslog` now have real implementations (T15-T18); `syslog` is advertised in the LLM prompt but not implemented anywhere in the factory — will raise `ValueError` if ever selected (T52).
- FR-2.2 Regex-based parser types enforce a compile-time complexity check and execution timeout. — **[RESOLVED, T19]** via `google-re2`.
- FR-2.3 Missing required fields route to `unresolved`, never a partial "success." — **[Unchanged, already true, now also covers type constraints via T20]**
- FR-2.4 Fingerprint collision hardening (`vendor_token`) is actually invoked, not just implemented. — **[STILL OPEN, T37]** `generate_fingerprint()` accepts a `vendor_token` parameter and hashes it in, but every call site (`main.py`, `jobs.py`, `sessions.py`, `onboarding.py`, `processor.py`) calls it with the default empty string. The hardening exists in code and is inactive in practice.

### FR-3 Rule Registry & Lifecycle
- FR-3.1 Full state machine including `DISABLED`/`REJECTED`/`ARCHIVED`. — **[RESOLVED, T23]**
- FR-3.2 Exactly one `ACTIVE` version enforced at the database level. — **[RESOLVED, T22]** Partial unique index, handles both SQLite and Postgres.
- FR-3.3 Auto-detection only considers `ACTIVE` rules. — **[Unchanged, already true]**
- FR-3.4 A `DISABLED` rule is rejected even via explicit `rule_id`. — **[RESOLVED, T23]**

### FR-4 Local Rule Authoring Agent
- FR-4.1 Real local model path is the production default. — **[RESOLVED, T10]** *Not independently verified: has real (non-mock) generation been run successfully end-to-end against an actual `.gguf` file? Flip-the-default is confirmed; the model actually working hasn't been watched happen.*
- FR-4.2 Samples redacted for secrets before prompting. — **[RESOLVED, T11]**
- FR-4.3 LLM JSON output passes a structural forbidden-content validator before persisting as `DRAFT`. — **[STILL OPEN, T7/T51]** The validator exists and is well-built, but is gated behind a `parser_type == "python"` condition that never occurs — it has never actually run against a real rule.
- FR-4.4 Retry up to 2-3 times with structured error feedback on validation failure. — **[RESOLVED, T12]**
- FR-4.5 Every generation attempt recorded in `rule_llm_generations`. — **[RESOLVED, T13]**

### FR-5 Batch & Streaming Ingestion
- FR-5.1 Adaptive spot-check rate table (1-in-50/500/25/unlock). — **[RESOLVED, T33]**
- FR-5.2 True persistent streaming vs. micro-batch. — **[STILL OPEN, T34]** Documented as an accepted limitation (L6), not silently absent.
- FR-5.3 A batch job and a streaming session can be started from the UI, not only via direct API call — per the understanding document's own §5.2 vendor-portal spec ("UI Upload panel... one-off conversion directly in Studio"). — **[STILL OPEN, T55/T56]** `Jobs.tsx` and `Sessions.tsx` are read-only monitors; the API client functions to do this (`createJob`, `createSession`, `submitSessionEvents`) already exist and work, they're just never called from any UI element. This was missed by the earlier audit rounds, which focused on backend correctness rather than whether the frontend fulfills the doc's own required demo flow.

### FR-6 Authentication, Authorization & Multi-tenancy
- FR-6.1 No request self-declares its own role via header. — **[RESOLVED, T1]**
- FR-6.1a The credential used to authenticate is never persisted in a way readable by client-side script (no raw password in `localStorage`), and no UI surface displays the real password value. — **[STILL OPEN, T50]** The login screen built to close FR-6.1 introduced this: it stores the raw password in `localStorage` and previously rendered the real demo password on a button. A `sessionStorage`-based fix is delivered but not yet dropped in; the durable fix is a backend session/token endpoint so the password is never replayed per-request at all.
- FR-6.2 Every ingestion endpoint validates the API key and enforces `source_scope`. — **[RESOLVED, T2]**
- FR-6.3 Multi-tenancy in scope or explicitly deferred. — **[RESOLVED as a decision, T35]** Explicitly documented single-tenant for SIH26156 (L4) — this satisfies the requirement's actual intent (make a decision and write it down), even though the technical feature itself remains unbuilt by design.

### FR-7 Normalization & Schema Adapters
- FR-7.1 `target_schema` actually selects a distinct field-renaming adapter. — **[RESOLVED, T26/T27]** With the classification-code scope limit noted in §2(c) above.
- FR-7.2 Unmapped vendor fields preserved. — **[Unchanged, already true]**

### FR-8 Observability
- FR-8.1 `/api/v1/system/health` reports live component status. — **[RESOLVED, T6]**
- FR-8.2 `fast_events` counter uses the actual pipeline constant. — **[RESOLVED, T5]**

---

## 4. Non-Functional Requirements

| Category | Requirement | First audit | **Now** |
|---|---|---|---|
| Security | No client-controlled privilege escalation | Failing | **Passing** (T1) |
| Security | ReDoS resistance on all regex rules | Failing | **Passing** (T19) |
| Durability | No data loss on process crash mid-ingestion | Failing | **Pending verification** (T32 — written, not yet dropped in or tested against a live Redis) |
| Air-gap | Zero outbound network calls when `ULPF_MODE=airgap` | Unenforced | **Not re-checked** — model bundling is fixed (T31); whether the mode flag itself gates network calls in code hasn't been re-verified |
| Scale | Documented, measured throughput; no invented benchmark numbers | Not yet measured | **Still not measured** |
| Auditability | Every rule lifecycle transition attributable to a real actor | Partial (fake `"admin"` string) | **Passing** (T41 — `rules.py`/`onboarding.py` now use the real authenticated username) |

---

## 5. Explicitly Out of Scope (for the hackathon submission, to keep task.md realistic)

- ClickHouse (Postgres JSONB is acceptable for MVP data volumes) — unchanged.
- Kubernetes manifests (Docker Compose is sufficient for the demo) — unchanged.
- Full Kafka/Redpanda swap — **superseded**: rather than deferring with a documented limitation, a Redis Streams implementation was actually built (T32). Once dropped in and verified, this line item closes rather than staying deferred.
- True multi-tenancy / RLS — deferred and documented as single-tenant (L4). Still the right call for this submission.

## 6. Open Decisions

1. ~~Is multi-tenancy in scope for submission~~ — **Resolved**: single-tenant, documented (L4).
2. ~~Is the in-process queue an accepted MVP limitation~~ — **Resolved in favor of fixing it**: Redis Streams implementation delivered, pending drop-in and live-Redis verification. Don't mark T32 done in `task.md` until that verification happens.
3. Who owns downloading/verifying the Qwen2.5-Coder-7B GGUF model and testing real (non-mock) generation — **still open**. The default is flipped to real-model mode, but no evidence yet that a real (non-mock) generation has been watched succeed end-to-end on the actual demo hardware. Worth doing before relying on it live.

---

## 7. Acceptance Criteria for "Fully Working Prototype" (not demo)

A build is considered a **fully working prototype** (as distinct from a demo) when, without code changes:
1. A brand-new, previously-unseen log format can be onboarded end-to-end using the **real** local LLM (mock disabled), including at least one retry-on-validation-failure cycle. — **Partial.** Mock is disabled by default and the retry loop exists, but this hasn't been watched succeed live (open decision 3), and the LLM currently can't be steered toward the newer `cef`/`leef`/`xml` parser types (T52) — it can only draft `regex`/`jsonpath`/`keyvalue` rules today.
2. An unauthenticated request to any mutating endpoint is rejected with 401/403. — **Passes** (T1, T2).
3. An API key scoped to source A cannot submit or read data for source B. — **Passes** (T2).
4. Killing the app process mid-batch-job does not silently drop already-accepted events. — **Pending.** Fix delivered (T32), not yet verified live — don't check this box until someone has actually killed the worker mid-job and confirmed nothing was lost.
5. `/api/v1/system/health` reflects a real outage when Postgres, Redis, or OpenSearch is stopped. — **Passes** (T6).
6. At least one CEF and one LEEF sample parse through a dedicated (non-regex-fallback) parser. — **Passes** (T15/T16) — reachable via a manually-authored rule; not yet reachable via the AI onboarding flow (T52).
7. The traceability endpoint reports `digest_verified` computed at request time, not just the stored value. — **Passes** (T28).

**5 of 7 pass outright, 1 is pending live verification, 1 is genuinely partial.** That's a real, substantial change from the original "none of these currently pass" — worth stating plainly rather than either overclaiming full completion or leaving the old verdict standing unmodified.