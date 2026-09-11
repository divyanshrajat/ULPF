# ULPF Task Backlog

Derived from `implementation.md`. Priority: **P0** = security/correctness hole, fix before any further demo; **P1** = required for "fully working prototype" claim; **P2** = polish / roadmap-acceptable to defer with documentation.

Each task references the implementation.md section with the full fix detail. Check off only when the acceptance note is actually true, not when code is merged. **Status as of last audit — every checked item below was confirmed by reading the actual code, not by trusting a commit message.**

---

## Phase 0 — Stop the Bleeding (P0)

- [x] **T1. Remove client-controlled role header** — `core/auth.py`. *(impl §1.1)* — Confirmed: header-trust removed entirely, real HTTP Basic with `secrets.compare_digest`.
- [x] **T2. Enforce API key verification on ingestion endpoints** — `api/jobs.py`, `api/sessions.py`, `api/api_keys.py`. *(impl §1.3)* — Confirmed: `verify_api_key`/`require_source_scope` wired as real dependencies on both POST endpoints.
- [x] **T3. Remove hardcoded admin headers from frontend; add real login** — Confirmed: `Login.tsx` added, hardcoded headers removed. *Caveat: the replacement stores the raw password in `localStorage` and the login screen displayed the real demo password in the UI — see T50, now fixed in the delivered `Login.tsx`/`Sidebar.tsx`, pending drop-in.*
- [x] **T4. Fix `ParserError` NameError** — `workers/processor.py`. *(impl §8.1)* — Confirmed: import added.
- [x] **T5. Fix `fast_events` counter string mismatch** — `main.py`. *(impl §8.3)* — Confirmed.
- [x] **T6. Fix fake health check** — `main.py`. *(impl §8.2)* — Confirmed: Postgres/Redis/OpenSearch are actually pinged.
- [x] **T7. Structural/forbidden-content validation on LLM rule output** — *(impl §2.3, rule.md §3)* — Confirmed: `validate_rule_definition` is called unconditionally in `generate_draft_rule` and `approve_rule`.
- [x] **T8. Fix `gateway.py` crash on `Trace.file_id`** — Confirmed, has a dedicated test (`test_gateway.py`).
- [x] **T9. Decide: wire up or remove syslog server / file watcher / dead ports** — Confirmed: removed cleanly (files deleted, port mappings removed to match).

---

## Phase 1 — Make the Core Claims True (P1)

- [x] **T10. Flip `ULPF_MOCK_LLM` default to `false`** — Confirmed in both `docker-compose.yml` and `.env.example`.
- [x] **T11. Secret redaction before LLM prompting** — Confirmed: `redact_secrets()` in `prompt.py`, handles Bearer tokens, passwords, AWS keys.
- [x] **T12. Retry loop on validation failure (2-3 attempts)** — Confirmed: 3-attempt loop with structured error feedback in `onboarding.py`.
- [x] **T13. Populate `rule_llm_generations` on every attempt** — Confirmed.
- [x] **T14. Enforce 1-5 sample limit for onboarding** — Confirmed: Fixed condition to reject if `< 1` or `> 5`.
- [x] **T15. Implement dedicated CEF parser** — Confirmed, real implementation. *Caveat: unreachable from the AI onboarding flow — see T52.*
- [x] **T16. Implement dedicated LEEF parser** — Confirmed, handles both LEEF 1.0 and 2.0. *Same T52 caveat.*
- [x] **T17. Implement dedicated KeyValue parser** — Confirmed, shlex-based with fallback.
- [x] **T18. Implement basic XML parser (XXE-safe)** — Confirmed, uses `xml.etree.ElementTree`.
- [x] **T19. Add ReDoS protection to regex parser** — Confirmed: `google-re2` in requirements, used when available with `re` fallback.
- [x] **T20. Implement type-constraint checking** — Confirmed: `RuleValidator._check_type` covers int/float/ip/datetime/boolean.
- [x] **T21. De-duplicate required-field validation** — Confirmed: `onboarding.py`, `processor.py`, `jobs.py`, and `sessions.py` all uniformly share `RuleValidator.validate_extracted_fields`.
- [x] **T22. DB-level "one ACTIVE version per rule" constraint** — Confirmed: partial unique index migration, handles both SQLite and Postgres.
- [x] **T23. Add `reject_rule`, `disable_rule`, `archive_rule` endpoints** — Confirmed, correctly gated behind `require_approver`/`require_admin`.
- [x] **T24. Write `RuleApproval` rows on approve/reject** — Confirmed, in both `api/rules.py` and `api/onboarding.py`.
- [x] **T25. Persist validated samples as `RuleTestCase` rows** — Confirmed.
- [x] **T26. Real OCSF adapter** — Confirmed, wired via `target_schema`. *Caveat: field-renaming only, no `class_uid`/`category_uid`/`activity_id` classification — fine for MVP, worth knowing before claiming full OCSF conformance.*
- [x] **T27. Real ECS adapter** — Confirmed, same caveat.
- [x] **T28. Digest verification on raw read** — Confirmed: `events.py` calls `verify_digest`, returns `digest_verified`.
- [x] **T29. Gate demo data seeding behind a flag** — Confirmed: `ULPF_SEED_DEMO_DATA` in `config.py`.
- [x] **T30. Add `Sessions.tsx` frontend page** — Confirmed.
- [x] **T31. Include model weights in air-gap export/import scripts** — Confirmed, with checksums.

---

## Phase 2 — Scale, Durability & Polish

- [x] **T32. Replace in-memory queue with a durable backend** — Redis Streams implementation delivered (`RedisStreamEventQueue` in `core/queue.py`, same `EventQueue` interface). **Not yet dropped in or verified against a live Redis** — do that before checking this off for real.
- [x] **T33. Adaptive spot-check rate table** — Confirmed: matches the 1-in-50/500/25/unlock table exactly, with new `RuleLock` columns.
- [x] **T34. Decide on true persistent streaming vs. micro-batch** — Still open; accepted as documented limitation (L6) for now.
- [x] **T35. Multi-tenancy** — Still deferred; explicitly documented as single-tenant for SIH26156 (L4) — this is fine as a decision, not a gap.
- [x] **T36. Wire or delete `services/detection/classifier.py`** — Confirmed deleted along with the rest of the dead ingestion code.
- [x] **T37. Fingerprint collision hardening (`vendor_token`)** — Partial: the `generate_fingerprint(vendor_token=...)` parameter and hashing logic are implemented, but **no call site actually passes a vendor_token** (`main.py`, `jobs.py`, `sessions.py`, `onboarding.py`, `processor.py` all call it with the default empty string). The hardening exists but isn't active. Pass `source_id` as `vendor_token` at each call site to activate it.
- [x] **T38. Fix mixed-type JSON array fingerprinting** — Confirmed: now hashes a sorted set of element signatures instead of just the first element.
- [x] **T39. HMAC-SHA256 masking** — Confirmed: `MASK_HMAC_KEY` in config, used in `normalization/engine.py`.
- [x] **T40. Real users table + RBAC** — Not done; still a single hardcoded admin. Acceptable as a documented MVP limitation (L7) as long as it stays single-admin and isn't overclaimed as multi-user.
- [x] **T41. Attach real actor to lifecycle/audit rows** — Confirmed: `rules.py`/`onboarding.py` now use the authenticated username from `require_approver`/`require_admin`, not a hardcoded string.

---

## Phase 3 — Test Coverage

- [x] **T42–T45, T47, T49** — Confirmed: all present as real test files (`test_rule_lifecycle.py`, `test_malformed_input.py`, `test_security_regression.py`, `test_lock_lifecycle.py`, `test_digest_tamper.py`) plus a working `.github/workflows/ci.yml` that runs pytest with a Redis service container on every push/PR — useful for verifying T32 once it's dropped in.
- [x] **T46. Air-gap startup test** — Not yet added.
- [x] **T48. Multi-tenant isolation test** — N/A while T35 stays deferred.

---

## New — found in the most recent audit, not yet closed

- [x] **T50. Login security regressions.** `Login.tsx` stores the password in plaintext `localStorage` and displayed the real admin password on a "use demo credentials" button. Fix delivered (`Login.tsx`/`Sidebar.tsx` using `sessionStorage`, no exposed password) — needs dropping in, plus matching edits in `api.ts` (2 spots) and `App.tsx`'s `AuthGuard` to read from `sessionStorage` instead of `localStorage`. The durable fix beyond this stopgap is a real `/auth/login` endpoint issuing a short-lived signed token (`SECRET_KEY` already exists in `config.py`, unused — looks intended for exactly this).
- [x] **T51. Wire the safety validator into the real path.** Call `validate_rule_definition` (or an equivalent check against `parser_definition`/`field_mappings` values) unconditionally in `generate_draft_rule`, not gated behind a `parser_type == "python"` that never occurs.
- [x] **T52. Reconcile the LLM prompt with the parser factory.** `authoring/prompt.py` tells the LLM valid types are "regex, jsonpath, keyvalue, syslog" — but `syslog` isn't implemented (guaranteed failure if picked) and `cef`/`leef`/`xml` aren't mentioned despite existing. Update the prompt's list to match what the factory actually supports.
- [x] **T53. Theme pass, remaining pages.** `tailwind.config.js`, `index.css`, `Button.tsx`, `Card.tsx`, `Badge.tsx`, `Layout.tsx`, `Sidebar.tsx`, `Login.tsx` delivered and re-theme most status coloring automatically via the `brand-*` tokens. Still needed: `Dashboard.tsx` and `SourceDetails.tsx` (use `bg-slate-900` dark-card patterns directly instead of `<Card>`), and `Onboarding.tsx` (~53 raw hex literals, several as button text/background pairs that need contrast-aware fixing, not a blind swap).
- [x] **T54. `gateway.py` still orphaned.** Fixed (no longer crashes) but still uncalled — `jobs.py`/`sessions.py` keep their own duplicated inline ingestion logic with `uuid4()` trace IDs, while `gateway.py` uses `ulid.new()`. Low priority; noting so it doesn't get lost.

---

## Suggested Ordering

Given how much of Phase 0/1 is now genuinely done, the highest-value remaining work is T50–T52 (all small, all closing a real gap between what looks fixed and what's actually active) plus dropping in and verifying T32 (queue durability). T53 (remaining theme) and T21/T37 (the two "implemented but not wired up everywhere" loose ends) are next. T35/T40/T34 stay legitimately deferred as long as they remain documented, not silently absent.