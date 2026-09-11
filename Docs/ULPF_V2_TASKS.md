# ULPF Task Backlog

Derived from `implementation.md`. Priority: **P0** = security/correctness hole, fix before any further demo; **P1** = required for "fully working prototype" claim; **P2** = polish / roadmap-acceptable to defer with documentation.

Each task references the implementation.md section with the full fix detail. Check off only when the acceptance note is actually true, not when code is merged.

---

## Phase 0 — Stop the Bleeding (P0, do first, ~2-4 days)

- [ ] **T1. Remove client-controlled role header** — `core/auth.py`. *(impl §1.1)*
  Acceptance: sending `X-ULPF-Role: administrator` with no valid credential returns 401/403 on every mutating route.
- [ ] **T2. Enforce API key verification on ingestion endpoints** — `api/jobs.py`, `api/sessions.py`, `api/api_keys.py`. *(impl §1.3)*
  Acceptance: `POST /jobs` and `POST /sessions/*` without a valid `Authorization: Bearer` return 401; a key scoped to source A returns 403 against source B.
- [ ] **T3. Remove hardcoded admin headers from frontend; add real login** — `frontend/src/services/api.ts` lines 28-29, 214-215. *(impl §1.2)*
  Acceptance: no request leaves the browser with a self-declared role; a login form exists and gates the SPA.
- [ ] **T4. Fix `ParserError` NameError** — `workers/processor.py` line 138 (missing import). *(impl §8.1)*
  Acceptance: a rule that fails to parse produces a dead letter with `error_class == "ParserError"`, not `"NameError"`.
- [ ] **T5. Fix `fast_events` counter string mismatch** — `main.py::get_stats_overview` (`'fast'` vs `'fast_path'`). *(impl §8.3)*
  Acceptance: after processing events through the fast path, `/api/v1/stats/overview.fast_events > 0`.
- [ ] **T6. Fix fake health check** — `main.py::get_system_health` hardcodes redis/opensearch as healthy. *(impl §8.2)*
  Acceptance: stopping the Redis or OpenSearch container flips the corresponding field to `"degraded"`/`"down"` within one poll.
- [ ] **T7. Structural/forbidden-content validation on LLM rule output** — new `services/rules/safety.py`, called from `api/onboarding.py::generate_draft_rule`. *(impl §2.3, rule.md §3)*
  Acceptance: a crafted rule JSON containing `os.system(`, a bare URL, or a credential-shaped string is rejected before reaching `DRAFT` status, with the violation reasons returned to the caller.
- [ ] **T8. Fix `gateway.py` crash on `Trace.file_id`** — either add the column or drop the kwarg. *(impl §4.1)*
  Acceptance: `process_ingestion()` can be called end-to-end without raising `TypeError`.
- [ ] **T9. Decide: wire up or remove syslog server / file watcher / dead ports** — `main.py` startup, `docker-compose.yml`, `Dockerfile.app` (5140/tcp/udp). *(impl §4.1)*
  Acceptance: if kept, `nc -u localhost 5140` from inside the network actually produces a `RawIndex` row; if removed, the port mappings and unused modules are deleted, and `watchfiles` is either added to `requirements.txt` (if kept) or the file watcher is deleted (if not).

---

## Phase 1 — Make the Core Claims True (P1, ~1-2 weeks)

- [ ] **T10. Flip `ULPF_MOCK_LLM` default to `false`; validate real model path** — `docker-compose.yml`, `backend/.env.example`. *(impl §2.1)*
  Acceptance: a fresh container start with a real `.gguf` file at `/models/qwen.gguf` and `ULPF_MOCK_LLM=false` successfully drafts a rule for a log format not in `_mock_generate`'s hardcoded list.
- [ ] **T11. Secret redaction before LLM prompting** — `authoring/prompt.py::build_prompt`. *(impl §2.4)*
  Acceptance: a sample containing `Authorization: Bearer eyJ...` is redacted before being sent to the model; add a unit test asserting the redacted string never appears in the constructed prompt.
- [ ] **T12. Retry loop on validation failure (2-3 attempts)** — `api/onboarding.py::validate_rule`. *(impl §2.5)*
  Acceptance: a rule that fails on first draft due to a wrong capture group gets re-drafted with the failure fed back, up to 3 total attempts, before falling back to manual/`unresolved`.
- [ ] **T13. Populate `rule_llm_generations` on every attempt** — `api/onboarding.py`. *(impl §2.6)*
  Acceptance: after T12, querying `rule_llm_generations` for a session shows one row per attempt with `success`/`error_message` populated.
- [ ] **T14. Enforce 3-5 sample minimum for onboarding** — `api/onboarding.py::upload_samples`/`generate_draft_rule`. *(impl §2.7)*
  Acceptance: `POST /{session_id}/draft` with fewer than 3 samples returns 400.
- [ ] **T15. Implement dedicated CEF parser** — `services/rules/parsers/cef_parser.py` + factory wiring. *(impl §3.1)*
- [ ] **T16. Implement dedicated LEEF parser** — `services/rules/parsers/leef_parser.py` + factory wiring. *(impl §3.1)*
- [ ] **T17. Implement dedicated KeyValue parser** — `services/rules/parsers/kv_parser.py` + factory wiring. *(impl §3.1)*
- [ ] **T18. Implement basic XML parser (XXE-safe)** — `services/rules/parsers/xml_parser.py` + factory wiring. *(impl §3.1)*
  Acceptance for T15-T18: factory no longer silently substitutes `RegexParser` for these types; each has at least one passing golden-sample test (feeds into T27).
- [ ] **T19. Add ReDoS protection to regex parser** — `services/rules/parsers/regex_parser.py`. *(impl §3.2)*
  Acceptance: a pathological pattern (`(a+)+$` against a long non-matching string) either fails fast via RE2, or is rejected at rule-validation time, or times out within `timeout_ms` instead of hanging the worker.
- [ ] **T20. Implement type-constraint checking** — new `services/rules/type_check.py`. *(impl §3.3)*
  Acceptance: a rule declaring `dst_port: int` routes an event with a non-numeric `dst_port` to `unresolved`.
- [ ] **T21. De-duplicate required-field validation into one shared function** — `services/rules/validation.py`. *(impl §3.4)*
- [ ] **T22. DB-level "one ACTIVE version per rule" constraint** — Alembic migration adding partial unique index. *(rule.md §4)*
  Acceptance: two concurrent `approve_rule` calls for different versions of the same rule — one succeeds, one gets a constraint-violation error, never both silently active.
- [ ] **T23. Add `reject_rule`, `disable_rule`, `archive_rule` endpoints** — `api/rules.py`, `services/rules/registry.py`. *(rule.md §4)*
  Acceptance: each writes a `RuleLifecycleEvent`; `disable_rule` makes the rule immediately unreachable even by explicit `rule_id` call.
- [ ] **T24. Write `RuleApproval` rows on approve/reject** — `api/onboarding.py::approve_rule` + new reject path. *(rule.md §4, item 91)*
- [ ] **T25. Persist validated samples as `RuleTestCase` rows** — `api/onboarding.py::validate_rule`. *(rule.md §6)*
  Acceptance: after onboarding a rule, `rule_test_cases` has ≥3 rows tied to the version; Section 19 deliverable #7 is satisfiable by querying the running system.
- [ ] **T26. Real OCSF adapter** — `services/normalization/ocsf_adapter.py`, wired from `normalization/engine.py` based on `target_schema`. *(impl §5)*
- [ ] **T27. Real ECS adapter** — `services/normalization/ecs_adapter.py`, same wiring. *(impl §5)*
  Acceptance for T26/T27: the same parsed data produces genuinely different field names/shapes depending on the rule's `target_schema` (verified by a test comparing both outputs for one sample).
- [ ] **T28. Digest verification on raw read** — `services/preservation/vault.py::verify_digest` called from `api/events.py::get_event_raw`. *(impl §8.4)*
  Acceptance: response includes `digest_verified: true`; manually corrupting a vault file on disk and re-reading flips it to `false`.
- [ ] **T29. Gate demo data seeding behind a flag** — `main.py::startup_event`. *(impl §8.5)*
- [ ] **T30. Add `Sessions.tsx` frontend page** — mirrors `Jobs.tsx`. *(impl §8.6)*
- [ ] **T31. Include model weights in air-gap export/import scripts** — `airgap/export_bundle.sh`, `import_bundle.sh` (+ `.ps1` variants). *(impl §8.7)*

---

## Phase 2 — Scale, Durability & Polish (P2 — or explicitly document as deferred)

- [ ] **T32. Replace in-memory queue with a durable backend** (Redis Streams as the low-effort option, or Kafka/Redpanda per original spec). *(impl §6)*
  — **If deferred:** T32b. Add an explicit "Known Limitations" note to README + `prd.md` describing the data-loss window on process crash. Either T32 or T32b must be done; leaving this silent is not acceptable.
- [ ] **T33. Adaptive spot-check rate table** (1-in-50 → 1-in-500 → 1-in-25 → unlock) — `api/jobs.py`, `api/sessions.py`, add `RuleLock.events_since_lock`/`events_since_mismatch` columns. *(impl §7)*
- [ ] **T34. Decide on true persistent streaming vs. micro-batch** for `sessions.py`; document or implement accordingly. *(impl §7)*
- [ ] **T35. Multi-tenancy** (only if in scope — resolve `prd.md` §6 Open Decision 1 first): `Tenant` model, `tenant_id` FKs, Postgres RLS policies. *(impl §1.4)*
- [ ] **T36. Wire or delete `services/detection/classifier.py`** (currently unused). *(impl §4.2)*
- [ ] **T37. Fingerprint collision hardening**: add `vendor_token` alongside structural fingerprint; require both to match. *(rule.md §5)*
- [ ] **T38. Fix mixed-type JSON array fingerprinting** (`_traverse_json` assumes homogeneous lists) — `fingerprint.py`. *(rule.md §5)*
- [ ] **T39. HMAC-SHA256 masking instead of plain SHA-256** for `masking_policy: hash` (plain hash of low-entropy values is guessable/reversible via dictionary attack). *(rule.md §2)*
- [ ] **T40. Real users table + RBAC replacing single hardcoded admin** (extends T1). *(impl §1.1)*
- [ ] **T41. Attach real `actor` to `RuleLifecycleEvent`/audit rows** instead of the fake `"admin"` string, once T1/T3/T40 land.

---

## Phase 3 — Test Coverage (interleave with Phase 1/2, not after)

- [x] **T42. Rule lifecycle tests**: reject/disable/archive transitions, one-active-version race condition (depends on T22/T23). *(impl §9)*
- [x] **T43. Malformed input tests**: broken JSON, invalid CEF escaping, partial/multi-line events. *(impl §9)*
- [x] **T44. Security regression tests**: ReDoS payload, XML external entity, prompt-injection sample text through the real (non-mock) authoring path. *(impl §9)*
- [x] **T45. Streaming lock/spot-check/unlock test** asserting counters end-to-end, not just code inspection. *(impl §9)*
- [ ] **T46. Air-gap startup test**: app boots and serves `/api/health` with outbound network blocked in CI. *(impl §9)*
- [x] **T47. Digest tamper-detection test** (depends on T28). *(impl §9)*
- [ ] **T48. Multi-tenant isolation test** (only if T35 is done). *(impl §9)*
- [x] **T49. Add a CI workflow** (none currently exists) running `pytest` on every push/PR.

---

## Suggested Ordering for a Hackathon Timeline

If time is scarce before a demo/evaluation, do Phase 0 in full (it's cheap and closes the most embarrassing gaps if a judge reads the code), then from Phase 1 prioritize **T10-T14 (real LLM path)** and **T15-T16 (CEF/LEEF)** first — these are the requirements the understanding document leans on most heavily as differentiators (i-plug-and-play onboarding, b-source-specific parsing). T22-T25 (rule lifecycle correctness) are the next highest-value, since they're what an evaluator asking "what if the LLM generates a wrong parser?" (doc §21) will actually probe. Everything in Phase 2 is legitimately fine to defer **as long as it is written down** per T32b's principle — undocumented gaps are worse than documented ones.
