# Implementation Plan: Security & Reliability Hardening

**Branch**: `020-security-testing` | **Date**: 2026-09-11 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/020-security-testing/spec.md`

## Summary

Day 29 adds no new features. It verifies the four critical behaviors the system
has relied on silently, and applies three small, surgical fixes where a gap is
proven by that verification:

1. **User Isolation** — verify (with A/B + guessed-ID tests) that messages,
   tasks, connections, and analytics are strictly user-scoped and that cross-user
   access is indistinguishable from "not found".
2. **Webhook Security** — verify signature + structure rejection with a suite of
   negative payloads (invalid/missing signature, malformed body).
3. **AI Reliability** — verify store-first behavior and **add the missing retry**:
   a background sweep that re-runs pending analyses against the single AI
   entry point and updates the *same* stored document in place.
4. **Duplicate Prevention** — make the dedupe key **user-scoped**
   (`{user_id, external_message_id}`) and verify one-document-per-delivery across
   all reprocessing paths.

Primary deliverable is the verification test suite (backend pytest, ~15 new
tests). Two lines of behavioral code change (dedupe scoping + retry sweep) are
covered by the tests that prove them.

## Technical Context

**Language/Version**: Python 3.13 (backend only — zero frontend changes)  
**Primary Dependencies**: existing motor/pymongo/pytest/httpx; **no new dependencies** (stdlib `hmac`, `hashlib` already in use)  
**Storage**: MongoDB — `messages` (index change: composite `{user_id, external_message_id}` dedupe index), `tasks`/`connections`/`users` (read-only verification)  
**Testing**: pytest (operational suite `python -m pytest tests/` from `backend/` — 212 passing today); frontend `npm run lint` + vitest untouched (no regression check only)  
**Target Platform**: Web (localhost dev: backend :8000, frontend :3000)  
**Project Type**: Web monorepo — `backend/` FastAPI + frontend Next.js at repo root  
**Performance Goals**: webhook returns ≤ 1s (existing); retry sweep is rate-bounded and never runs on the ingestion path; `GET /analytics` stays < 500ms  
**Constraints**: `user_id` is the FIRST condition in every query/aggregation; NO code path calls `analyze_message` outside `process_message` (Day 24); retries update the existing document (never a new one); no new collections; no new LLM round-trips; secrets stay in env vars  
**Scale/Scope**: FYP demo (single user per view); test DB = `communication_ai_test`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Verdict |
|---|---|---|
| I. Simplicity First | No new dependencies, services, or collections; two small fixes + a test suite | ✅ PASS |
| V. Security and Privacy | Dedupe key becomes user-scoped; webhook rejection verified at the boundary; secrets remain env-only | ✅ PASS |
| VII. Progressive Enhancement | Pending message stays visible and usable while AI is down; retry happens later | ✅ PASS |
| Day 18 User Isolation | A/B + guessed-ID verification across messages/tasks/connections/analytics; 404 indistinguishable from not-found | ✅ PASS |
| Day 23 Webhook Security | Invalid/missing signature → 403 before parsing; malformed payload → 400; negative payload suite | ✅ PASS |
| Day 24 AI Orchestrator | Retry sweep routes through `process_message` (single entry point) — never `analyze_message` directly | ✅ PASS |
| Day 29 Hardening (constitution) | Four critical tests pass with zero regression on both suites | ✅ PASS |

No violations — Complexity Tracking is left empty.

## Project Structure

### Documentation (this feature)

```text
specs/020-security-testing/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (verification findings + fix decisions)
├── data-model.md        # Phase 1 output (ownership, dedupe key, analysis state)
├── quickstart.md        # Phase 1 output (how to run the verification suites)
├── contracts/           # Phase 1 output (no new endpoints; verification surface)
│   └── security-testing.md
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (backend only)

```text
backend/
├── main.py                          # EDIT — user-scoped dedupe index; start retry sweep in lifespan
├── services/
│   ├── webhook_ingest.py            # EDIT — scoped dedupe lookup ({user_id, external_message_id})
│   │                                #        instead of external_message_id alone
│   └── retry_pending.py             # NEW — retry_pending_analyses() sweep (exported for tests)
├── routes/
│   └── webhooks.py                  # NO CODE CHANGE — verification target (owner resolution note)
└── tests/
    ├── test_ai_reliability.py       # NEW — AI outage → stored + pending + retry updates in place, no dup
    ├── test_dedup.py                # NEW — user-scoped dedupe incl. cross-user same-key independence
    ├── test_security_testing.py     # NEW — isolation matrix (connections + analytics + guessed IDs)
    └── test_webhooks.py             # EDIT — backfill malformed-payload / UPPERCASE-signature negatives
```

**Structure Decision**: Conventional structure, no new projects or packages. All
additions live in existing `backend/services/` and `backend/tests/`. The three
behavioral edits (index, dedupe scope, retry sweep) are one-liners against
existing functions plus a new ~40-line service.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations — table intentionally empty.

## Research Decisions

See [research.md](./research.md) for full rationale:

1. **Dedupe key becomes user-scoped.** Today `main.py` creates a unique index on
   `external_message_id` alone and `ingest_message` recovers a duplicate via
   `find_one({"external_message_id": ...})` with **no user filter** — a cross-user
   collision (e.g., two users simulating the same id) would return the *other*
   user's message id. Fix: composite unique index `{user_id, external_message_id}`
   (partial on string) + user-scoped recovery `find_one`. Verified as a real gap,
   not hypothetical.
2. **Pending-analysis retry is missing.** `process_message` degrades AI failure
   to `ai_analysis.status: "pending"` and it is persisted — but *nothing ever
   retries it*. Day 29 adds a small background sweep (`retry_pending_analyses`)
   that re-runs `process_message` for pending messages and `update_one`s the same
   document ({_id, user_id}), started in `main.py` lifespan (skipped on the test
   DB, mirroring the Gmail poller pattern) and exported for direct tests.
3. **Key-less messages are explicitly exempt from dedupe.** Simulate/manual
   messages carry no provider id; a deterministic hash can only approximate "the
   same message", risking false dedupe of legitimate identical sends. Per
   constitution Day 29 rule 5, these stay exempt and documented rather than
   derived — relay (WhatsApp/Gmail) dedupe is unaffected.
4. **`POST /messages` (manual API create) stays out of dedupe scope.** It is a
   manual CRUD entry point, not a reprocessing path; intentional duplicates there
   are user-meaningful. Webhook/simulate/Gmail ingest paths (the delivery and
   retry paths) all funnel through `ingest_message` and are dedupe-covered.
5. **Webhook owner resolution limitation accepted.** `_resolve_owner()` maps
   inbound WhatsApp to the first `provider: whatsapp, status: connected`
   connection. Correct for a single WABA deployment (the FYP setup); cross-user
   multi-number routing is a future amendment, documented as a known limitation,
   NOT fixed in Day 29 (Simplicity First).
6. **No new API contracts.** Day 29 changes no public endpoints; the retry sweep
   is internal. Verification surface is documented in `contracts/`.

## Implementation Steps (in order)

1. **Red: write the Day 29 test suites first**
   - `backend/tests/test_ai_reliability.py` — provider mocked to fail (raise /
     timeout) → message still stored with `ai_analysis.status == "pending"` and
     visible; restore provider → `retry_pending_analyses()` completes the SAME
     document (count unchanged at 1); failure never crashes the ingest path.
   - `backend/tests/test_dedup.py` — same `external_message_id` delivered twice →
     1 document, no re-analysis (webhook + real paths); two DIFFERENT users with
     the same external id → 2 independent documents each owned by its user (this
     fails today — proves the gap).
   - `backend/tests/test_security_testing.py` — A/B for connections and
     `/analytics` (guessed IDs → 404 identical to non-existent; lists contain
     zero of the other user's data); 404-body equality between "not yours" and
     "not found".
   - Backfill `test_webhooks.py` negatives (malformed JSON body → 400,
     non-sha256 signature header → 403) if not already implied.
   - Run → confirm the dedupe-user-scope and retry tests are RED.
2. **Fix the dedupe scope** — `backend/main.py`: replace the single-field index
   with composite `[("user_id",1),("external_message_id",1)]` + partial filter
   (drop/recreate; idempotent in lifespan). `backend/services/webhook_ingest.py`:
   scope the `DuplicateKeyError` recovery `find_one` with `{"user_id": user_id, ...}`.
   → dedupe tests GREEN.
3. **Add the retry sweep** — `backend/services/retry_pending.py`:
   `retry_pending_analyses()` iterates user-scoped pending messages, calls
   `process_message` (the Orchestrator — never `analyze_message`), and
   `update_one({"_id":..., "user_id":...}, {"$set":{"ai_analysis":...}})`. Wire a
   rate-bounded loop into `main.py` lifespan, skipped on `communication_ai_test`
   (same pattern as the Gmail poller). → reliability tests GREEN.
4. **Green: run the backend operational suite** — `python -m pytest tests/` from
   `backend/` (212 existing + ~15 new, all green; run with a 600s shell timeout).
5. **No-regression on the frontend** — `npm run lint` and the vitest suite
   (`npx vitest run`); expect clean with zero source changes (Day 29 client is
   untouched by design).
6. **Manual verification** — follow `quickstart.md`: register A/B, send messages
   per user, attempt guessed-ID reads, send an unsigned webhook via testing tools,
   kill the provider key and simulate an outage → pending card visible → restore
   → completed without duplicate. Update `AGENTS.md` manual additions.

## Test Cases (concrete, mapped to TC-01..15 from the spec)

| TC | Test (file) | Expected |
|---|---|---|
| TC-01/02 | B requests A's message / guessed ObjectId (`test_user_isolation`, extended) | 404, body identical to non-existent |
| TC-03 | A and B list messages/tasks/connections/analytics (`test_security_testing.py`) | each sees only own data, exact totals |
| TC-04 | POST with body/user_id claims of another user (`test_messages.py`) | claimed id ignored; JWT id used |
| TC-05/06 | Webhook missing / invalid signature (`test_webhooks.py` + backfill) | 403, zero storage |
| TC-07 | Valid signature, malformed payload (`test_webhooks.py` backfill) | 400, zero storage |
| TC-08 | Valid signature, well-formed payload (`test_webhooks.py`) | 200, stored |
| TC-09/10 | AI mocked-down on ingest, then restored → `retry_pending_analyses()` (`test_ai_reliability.py`) | stored + pending, visible; completed in place, same doc |
| TC-11 | `process_message`/provider raises mid-analysis (`test_ai_reliability.py`) | no crash, message kept, pending, no new doc |
| TC-12/13 | Same `external_message_id` twice / concurrently (`test_dedup.py`, `test_webhooks.py`) | exactly 1 doc |
| TC-14 | AI-failure retry after pending (`test_ai_reliability.py`) | 1 doc updated in place |
| TC-15 | Key-less (simulate) messages (`test_dedup.py`) | stored exactly once per delivery, documented exemption |

## Definition of Done

A Day 29 is DONE when:

1. **Four critical behaviors are proven by tests**: A/B isolation passes for
   messages, tasks, connections, AND analytics (guessed IDs → 404, identical to
   not-found); invalid/missing/malformed webhook requests are rejected before any
   processing; an AI outage stores the message with pending state, keeps it
   visible, and retries it later with zero loss; duplicate `externalMessageId`
   deliveries (and concurrent/cross-`user_id` collisions) produce exactly one
   document each — backed by a user-scoped unique index.
2. **Three gaps are closed**: dedupe recovery is user-scoped, dedupe index is
   composite `{user_id, external_message_id}`, pending analyses are retried
   through `process_message` and updated in place.
3. **Full backend suite green**: `python -m pytest tests/` from `backend/`
   passes (existing 212 + new tests), no regression.
4. **Frontend unchanged and green**: `npm run lint` + vitest pass with zero
   Day-29 source changes.
5. **Zero new dependencies**, zero new collections, zero new APIs, zero password/
   token/secret exposure (secrets env-only, verified in diff review).
6. **Documented**, not just tested: research decisions, data-model, contracts,
   quickstart manual steps, and AGENTS.md additions capture the verification
   surface and the accepted limitations (single-WABA owner resolution,
   key-less exemption, manual-create exemption).