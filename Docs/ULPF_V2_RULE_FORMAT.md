# ULPF Rule Specification (Canonical)

This is the authoritative definition of a **Parsing Rule** — the artifact produced by an analyst or the Local Rule Authoring Agent, validated deterministically, and executed by the Data Plane. Code should be brought into conformance with this spec (see `implementation.md` §2 for the delta and fix plan). This intentionally mirrors `ULPF_Full_Understanding_Document.pdf` §7–§8, corrected against what `backend/app/models/domain.py` and `backend/app/services/rules/` actually implement today.

---

## 1. Rule Identity

| Concept | Field | Notes |
|---|---|---|
| Logical rule | `rule_id` (UUID) + `name` | Stable identity, e.g. `cisco-asa-syslog`. Matches `Rule` model. |
| Version | `rule_versions.version` (int, monotonic per `rule_id`) | Immutable once created. |
| Human-readable pointer | `name@version`, e.g. `cisco-asa-syslog@2` | Used in UI/logs (`jobs.py` already builds this string). |
| Rule hash | SHA-256 over the canonical JSON of the version's content | Already implemented in `registry.py::_calculate_rule_hash`. Keep this — it's correct. |

## 2. Rule Version Document Shape

```json
{
  "rule_key": "cisco-asa-v1",
  "version": 2,
  "status": "ACTIVE",
  "parser_type": "regex",
  "parser_definition": {
    "engine": "re2",
    "pattern": "<named-capture-regex>",
    "timeout_ms": 25
  },
  "field_mappings": {
    "source_ip": "src_endpoint.ip",
    "destination_ip": "dst_endpoint.ip"
  },
  "required_fields": ["time", "src_endpoint.ip", "dst_endpoint.ip", "action"],
  "type_constraints": {
    "src_endpoint.ip": "ipv4_or_ipv6",
    "dst_port": "int"
  },
  "masking_policy": {
    "actor.user.email": "hash"
  },
  "target_schema": "ocsf",
  "schema_version": "1.0",
  "fingerprints": [
    { "type": "vendor_token", "value": "%ASA-", "required": true }
  ]
}
```

### Field-by-field requirements

| Field | Required | Current code support | Gap |
|---|---|---|---|
| `parser_type` | Yes | `regex`, `jsonpath` fully implemented. `syslog`, `cef`, `leef`, `keyvalue`, `xml` accepted by the factory but silently routed to `RegexParser` | **Must implement dedicated parsers** for `cef`, `leef`, `keyvalue`, `syslog`, and at least a basic `xml`/`xpath` parser, or the factory must raise `NotImplementedError` instead of silently mis-routing. Silent fallback is worse than an explicit error. |
| `parser_definition.timeout_ms` | Should be required for `regex`/`syslog`/`cef`/`leef` | **Not read anywhere** in `regex_parser.py` | Add a timeout wrapper (see `implementation.md` §3) or migrate to `re2` (recommended: `google-re2` Python binding, which has no catastrophic-backtracking risk by construction, making `timeout_ms` a documentation field rather than an enforced one). |
| `field_mappings` | Yes | Implemented for regex named groups + `capture_N` positional, and JSONPath keys | OK as-is. |
| `required_fields` | Yes | Checked in `processor.py`, `jobs.py`, `sessions.py`, `onboarding.py` | OK, but duplicated four times — should be a single shared function (`validate_required_fields(parsed, required_fields)`). |
| `type_constraints` | Recommended | **Not implemented at all** — column exists on `RuleVersion` but is never read during parsing or validation | Add a lightweight type-checker (regex/format check per declared type: `ipv4`, `ipv6`, `int`, `iso8601`, `mac`, `uuid`) run after extraction, before a rule can move to `PENDING_REVIEW`. |
| `masking_policy` | Recommended | Implemented in `normalization/engine.py` for `hash`/`mask`/`drop` | OK as-is, but only three policies — doc mentions `hmac_sha256` specifically for stable, keyed correlation (plain SHA-256 hash is guessable for low-entropy values like short usernames). Recommend switching `"hash"` to `HMAC-SHA256` with a locally-held, non-exported key. |
| `target_schema` | Yes (`ocsf` \| `ecs`) | Stored, **never changes behavior** | See `implementation.md` §5 — needs real adapters. |
| `fingerprints` | Yes | A single string fingerprint per rule (`RuleFingerprint.fingerprint`), not a typed list of `{type, value, required}` entries | Acceptable simplification for MVP, but multi-fingerprint disambiguation (the doc's own "Open Question" about fingerprint collisions) is not solvable with a single string field. If two vendors produce logs with the same fingerprint, `find_active_rule_by_fingerprint` returns whichever rule happens to be first in the `ACTIVE` scan — this is a real, currently-unhandled collision. |

## 3. Forbidden Content (Structural Safety Rule)

A rule version's `parser_definition` and `field_mappings` MUST NOT contain, anywhere in their JSON values:

- Any of: `exec(`, `eval(`, `import os`, `import subprocess`, `__import__`, `os.system`, backticks, `$(`, `;rm `, `curl `, `wget `
- Any `http://` or `https://` literal
- Anything matching a common credential pattern (`AKIA[0-9A-Z]{16}`, `-----BEGIN`, `Bearer [A-Za-z0-9\-_.]+`, `password\s*[:=]`)
- SQL keywords adjacent to string concatenation patterns (`' OR '1'='1`, `; DROP TABLE`, `UNION SELECT`)

**Current status: none of this is checked.** `authoring/agent.py` returns raw LLM JSON straight into `create_rule_version` with no structural scan. This is the single highest-priority security fix in `implementation.md`, because it is the exact mitigation the understanding document names for LLM Risk #3 (prompt injection in a log) and #18 (excessive autonomy) — and it is currently absent.

Implementation: a pure-function validator, e.g. `validate_rule_json(rule_json: dict) -> list[str]` returning a list of violations, called in `onboarding.py::generate_draft_rule` **before** `create_rule_version` is invoked. If violations are non-empty, do not create a `DRAFT` — return the violations to the caller and log a security event.

## 4. Lifecycle State Machine

```
DRAFT ──(passes structural+deterministic validation)──► PENDING_REVIEW
PENDING_REVIEW ──(reviewer approves)──► ACTIVE
PENDING_REVIEW ──(reviewer rejects)──► REJECTED   [terminal]
ACTIVE ──(new version approved for same rule_id)──► DEPRECATED
ACTIVE ──(known-bad, security incident)──► DISABLED
DEPRECATED ──(known-bad)──► DISABLED
DISABLED ──(never auto-reactivated; new version required)──► [terminal until archived]
ACTIVE/DEPRECATED/DISABLED ──(retention policy)──► ARCHIVED   [terminal]
```

| From | To | Who/What can trigger | Current code |
|---|---|---|---|
| `DRAFT` | `PENDING_REVIEW` | Deterministic validation passing (`onboarding.py::validate_rule`) | ✅ implemented |
| `PENDING_REVIEW` | `ACTIVE` | Human reviewer only (`approve_rule`) | ✅ implemented, but **no `RuleApproval` row is written** — only a `RuleLifecycleEvent`. The dedicated `rule_approvals` table (with `reviewer`, `decision`, `comments`) exists in the schema and is never populated. Fix: write a `RuleApproval` row in `approve_rule`. |
| `PENDING_REVIEW` | `REJECTED` | Human reviewer | ❌ **not implemented** — there is no reject endpoint at all today. |
| `ACTIVE` (new version) | `DEPRECATED` (old version) | Automatic, on activation of a newer version | ✅ implemented in `update_rule_version_status` |
| `ACTIVE`/`DEPRECATED` | `DISABLED` | Administrator, on discovering a known-bad rule | ❌ **not implemented** — no endpoint, no code path sets `DISABLED`. |
| `DISABLED` | auto-detect | MUST always be excluded | Partially true only because `find_active_rule_by_fingerprint` filters on `status == "ACTIVE"` — so `DISABLED` rules are correctly excluded from auto-detect by omission, but there's no way to *reach* `DISABLED` in the first place. |
| any | `ARCHIVED` | Retention policy / manual | ❌ **not implemented**. |

**Required fix set:** add `reject_rule`, `disable_rule`, and `archive_rule` endpoints/functions to `services/rules/registry.py` and `api/rules.py`, each writing both a `RuleLifecycleEvent` and, where applicable, a `RuleApproval`. Also move the "exactly one ACTIVE version" invariant from application code (`update_rule_version_status`, lines 88-96) to a **database-level partial unique index**:

```sql
CREATE UNIQUE INDEX one_active_version_per_rule
ON rule_versions (rule_id)
WHERE status = 'ACTIVE';
```

This closes a real race condition: two concurrent `approve_rule` calls for two different `PENDING_REVIEW` versions of the same rule can currently both succeed if they interleave between the "deactivate old" and "commit" steps, since there's no row lock or DB constraint stopping it.

## 5. Fingerprint Rules

- JSON payloads: structural key-set fingerprint (sorted keys, scalar values replaced by type tokens). Implemented in `fingerprint.py::_traverse_json`. **Known gap:** `"assume homogeneous list"` — a JSON array with mixed-type elements will fingerprint only from the first element, silently misclassifying arrays whose later elements differ in shape.
- Unstructured/text payloads: token-substitution structural signature (IP/TIME/NUM/HEX/UUID/MAC/URL/EMAIL replaced, then remaining words replaced with `<WORD>`). Implemented in `fingerprint.py`. Reasonable approach; keep.
- **Gap vs. spec:** the understanding document calls for typed, multi-signal fingerprints (`vendor_token` markers, required/optional flags) to disambiguate collisions. Current code has a single opaque string per rule. Minimum viable fix: also store a `vendor_token` (first non-variable literal substring, e.g. `%ASA-`, `CEF:`, `LEEF:`) alongside the structural fingerprint, and require both to match before treating a rule as a confident candidate.

## 6. Test Cases (`rule_test_cases` table)

**Currently unused** — the table exists in the schema but nothing writes to it. Per the doc's Section 8 step 6 ("compiles the parser in a sandbox and runs all test samples") and Section 15.1 ("Golden-sample regression tests per rule version"), every validated sample used in `onboarding.py::validate_rule` should be persisted as a `RuleTestCase` row tied to the rule version, so that:
1. Future edits to a rule version can be regression-tested against the original golden samples.
2. Section 19 deliverable #7 ("At least 3 approved rule files with test cases") is actually satisfiable from the running system, not hand-assembled for submission.

## 7. What "Approved for Production" Means

A rule version may only reach `ACTIVE` when **all** of the following are true — this is the acceptance gate `task.md` should test against:
- [ ] Passes structural forbidden-content validation (§3)
- [ ] Has at least 3 distinct validated samples recorded as `RuleTestCase` rows
- [ ] All `required_fields` extracted on every sample
- [ ] All `type_constraints` (if declared) satisfied on every sample
- [ ] A human reviewer decision is recorded in `rule_approvals`
- [ ] Rule hash is computed and stored
- [ ] Exactly one `ACTIVE` version exists per `rule_id` (DB-enforced)
