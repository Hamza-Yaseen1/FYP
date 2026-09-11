# Tasks: Security & Reliability Hardening

**Input**: Design documents from `/specs/020-security-testing/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/security-testing.md

**Tests**: Tests are required for this feature — the user explicitly requested "Write and run concrete test cases" and the plan follows a TDD red-first approach.

**Organization**: Tasks are grouped by user story. US1 and US2 are verification-only (no code changes). US3 and US4 each carry one small code fix that the tests prove is needed. The TDD discipline is enforced *within* each story: tests are written and confirmed red before the fix is applied.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- Backend: `backend/` (FastAPI, Python 3.13)
- Tests: `backend/tests/` (pytest, `DB_NAME=communication_ai_test`)
- Services: `backend/services/`
- Routes: `backend/routes/`
- Run suite: `python -m pytest tests/` from `backend/`

---

## Phase 1: Setup

**Purpose**: Confirm the test infrastructure runs and environment is ready for Day 29 work.

- [x] T001 Run `python -m pytest tests/ -q` from `backend/` and confirm all 212 existing tests pass (600s timeout) — baseline green before any changes
- [x] T002 [P] Confirm `WHATSAPP_APP_SECRET=test_app_secret` is set in the test environment so `verify_signature` functions in `backend/routes/webhooks.py` (tests set it via `os.environ`; verify no stale state)

**Checkpoint**: Existing suite green; test infra confirmed.

---

## Phase 2: Foundational

**Purpose**: Verify that the existing codebase already satisfies the behavioral requirements for US1 and US2. No code changes — the research audit (research.md §1, §2) proved this. The only deliverable is a green confirmation.

- [x] T003 Verify existing isolation tests pass: `python -m pytest tests/test_user_isolation.py -q` — confirms `test_user_isolation.py` (15 tests) is green as the baseline for extending in US1

**Checkpoint**: Foundation confirmed; US1 and US2 test-writing can begin.

---

## Phase 3: User Story 1 — A user sees only their own data (Priority: P1)

**Goal**: Extend the A/B isolation matrix to connections and analytics, with guessed-`ObjectId` probes and 404-body-equality assertions — proving cross-user access is indistinguishable from "not found."

**Independent Test**: Register users A and B; create messages, tasks, connections, and analytics data for each; verify A sees only A's data (and vice versa) via direct API calls, including guessed record IDs.

### Tests for User Story 1

> **NOTE: Write these tests FIRST. Confirm they PASS against the existing code (US1 requires no code fix).**

- [x] T004 [P] [US1] Write `backend/tests/test_security_testing.py` — test `test_user_b_connection_returns_404_to_a`: register A and B, A creates a WhatsApp connection, B attempts `GET /connections/{A_connection_id}` → 404; verify response body matches `GET /connections/{valid_but_nonexistent_id}` (same status + detail)

- [x] T005 [P] [US1] Add tests to `backend/tests/test_security_testing.py` — test `test_user_b_guessed_connection_id_returns_404_to_a`: A creates connection, B attempts `GET /connections/{random_valid_object_id}` → 404 identical to non-existent; response bodies are indistinguishable

- [x] T006 [P] [US1] Add tests to `backend/tests/test_security_testing.py` — test `test_user_a_connections_list_excludes_b`: register A and B, each creates a WhatsApp connection, A lists `GET /connections` → A sees exactly A's connection, B's is absent

- [x] T007 [P] [US1] Add tests to `backend/tests/test_security_testing.py` — test `test_analytics_user_isolation`: register A and B, create 3 messages for A with `ai_analysis` and 5 for B with `ai_analysis`, A calls `GET /analytics?period=week` → `total == 3`, B calls → `total == 5`; cross-user data never visible

- [x] T008 [US1] Run `python -m pytest tests/test_security_testing.py -q` — confirm all US1 tests PASS (existing code already enforces isolation; tests prove it)

**Checkpoint**: US1 verified — isolation holds for messages, tasks, connections, analytics, including guessed IDs and 404 indistinguishability. No code changes needed.

---

## Phase 4: User Story 2 — Bad webhook requests are rejected (Priority: P1)

**Goal**: Backfill negative webhook tests for malformed payloads and edge-case signature headers, proving the existing boundary holds without code changes.

**Independent Test**: Send webhook requests with (a) invalid/missing signatures, (b) malformed JSON body, (c) valid signature + well-formed payload — confirm only (c) is stored.

### Tests for User Story 2

> **NOTE: Write these tests FIRST. Confirm they PASS against the existing code (US2 requires no code fix).**

- [x] T009 [P] [US2] Add tests to `backend/tests/test_webhooks.py` — test `test_post_rejects_malformed_json_body`: POST a valid `X-Hub-Signature-256` over `{"not": "valid meta payload"}` → expect 400, message count unchanged

- [x] T010 [P] [US2] Add tests to `backend/tests/test_webhooks.py` — test `test_post_rejects_non_sha256_header`: POST with `X-Hub-Signature-256: md5=abc123` header → expect 403, message count unchanged

- [x] T011 [P] [US2] Add tests to `backend/tests/test_webhooks.py` — test `test_post_rejects_valid_signature_wrong_secret`: POST with a signature computed using a different secret than the configured `WHATSAPP_APP_SECRET` → expect 403, message count unchanged

- [x] T012 [US2] Run `python -m pytest tests/test_webhooks.py -q` — confirm all webhook tests (existing + new) PASS

**Checkpoint**: US2 verified — invalid/missing/malformed webhook requests are rejected before any processing. No code changes needed.

---

## Phase 5: User Story 3 — The system survives AI failure without data loss (Priority: P2)

**Goal**: Verify store-first behavior, then implement the missing retry mechanism. Tests are written and confirmed red before the code fix.

**Independent Test**: Mock the AI provider to fail, send a message → confirm it is stored with `ai_analysis.status == "pending"` and visible; restore the provider → `retry_pending_analyses()` completes the same document in place, with zero new documents.

### Tests for User Story 3

> **NOTE: Write these tests FIRST. The retry tests MUST FAIL (RED) until T017 is implemented.**

- [x] T013 [P] [US3] Write `backend/tests/test_ai_reliability.py` — test `test_message_stored_with_pending_on_ai_failure`: monkeypatch `process_message` to return a `status: "pending"` fallback dict; POST `/webhooks/simulate`; confirm document exists with `ai_analysis.status == "pending"` and `content` preserved

- [x] T014 [P] [US3] Add test to `backend/tests/test_ai_reliability.py` — test `test_ai_failure_never_crashes_ingest`: monkeypatch `process_message` to raise `RuntimeError`; POST `/webhooks/simulate` → expect 200 (message stored); confirm document exists (message preserved), no unhandled exception

- [x] T015 [P] [US3] Add test to `backend/tests/test_ai_reliability.py` — test `test_pending_message_visible_in_listing`: send message with mocked `process_message` → `status: "pending"`; `GET /messages` → message appears in the listing (not hidden or dropped)

- [x] T016 [US3] Add test to `backend/tests/test_ai_reliability.py` — test `test_retry_pending_completes_in_place`: monkeypatch `process_message` once to return `status: "pending"`, send a message via simulate; then monkeypatch `process_message` to return a `status: "completed"` analysis; call `retry_pending_analyses()` directly; confirm the SAME document (`_id` unchanged) now has `ai_analysis.status == "completed"` and document count is still exactly 1

- [x] T017 [US3] Add test to `backend/tests/test_ai_reliability.py` — test `test_retry_pending_idempotent`: call `retry_pending_analyses()` twice; confirm document count unchanged, `ai_analysis.status` still `"completed"`, no duplication

- [x] T018 [US3] Run `python -m pytest tests/test_ai_reliability.py -q` — confirm T013–T015 PASS (store-first and pending state work today); confirm T016 and T017 FAIL (RED) — retry mechanism does not yet exist

### Implementation for User Story 3

- [x] T019 [US3] Create `backend/services/retry_pending.py` with `async def retry_pending_analyses(limit: int = 50) -> int`: query `{"ai_analysis.status": "pending"}` messages, for each call `process_message(content, message_id=str(_id), user_id=user_id, thread_id=doc.get("threadId"))` (the Orchestrator — NEVER `analyze_message`), then `update_one({"_id": ObjectId(message_id), "user_id": user_id}, {"$set": {"ai_analysis": analysis}})`; catch exceptions per-message (log + continue); return count of retried messages. Reference: `contracts/security-testing.md §4`

- [x] T020 [US3] Wire `retry_pending_analyses` into `backend/main.py` lifespan: add `RETRY_INTERVAL_SECONDS = int(os.getenv("RETRY_INTERVAL_SECONDS", "60"))`; create `_retry_pending_loop()` mirroring `_gmail_poll_loop` pattern (guarded by `DB_NAME != "communication_ai_test"`); start as `asyncio.create_task` in the lifespan block alongside the Gmail poller; cancel on shutdown. Add import for `services.retry_pending.retry_pending_analyses`

- [x] T021 [US3] Run `python -m pytest tests/test_ai_reliability.py -q` — confirm ALL tests including T016 and T017 now PASS (GREEN)

**Checkpoint**: US3 complete — AI failure stores with pending state, retry sweep completes in place, idempotent, no new documents. Existing suite unaffected.

---

## Phase 6: User Story 4 — The same message is never stored twice (Priority: P2)

**Goal**: Make the dedupe key user-scoped and verify one-document-per-delivery. Tests are written and confirmed red before the code fix.

**Independent Test**: Deliver the same `external_message_id` twice → one document; two different users with the same key → two independent documents; key-less messages stored exactly once per delivery.

### Tests for User Story 4

> **NOTE: Write these tests FIRST. T024 MUST FAIL (RED) until T027 is implemented.**

- [x] T022 [P] [US4] Write `backend/tests/test_dedup.py` — test `test_same_external_id_twice_yields_one_document`: register a user, connect WhatsApp, POST two signed webhook payloads with the same `wamid.DEDUP1` → `sync_db.messages.count_documents({"external_message_id": "wamid.DEDUP1"}) == 1`

- [x] T023 [P] [US4] Add test to `backend/tests/test_dedup.py` — test `test_duplicate_skips_reanalysis`: monkeypatch `process_message` to track calls, POST same payload twice → `len(calls) == 1`

- [x] T024 [US4] Add test to `backend/tests/test_dedup.py` — test `test_cross_user_same_external_id_independent`: register users A and B; A and B each connect WhatsApp; A receives `wamid.SHARED1` via webhook; B receives `wamid.SHARED1` via webhook; confirm A has exactly 1 doc with `user_id == A` and B has exactly 1 doc with `user_id == B` (total 2 documents in collection). **This test FAILS (RED) today** — the global unique index causes B's insert to raise `DuplicateKeyError` and the unscoped `find_one` returns A's document

- [x] T025 [US4] Add test to `backend/tests/test_dedup.py` — test `test_keyless_simulate_stored_once_per_delivery`: POST the same `/webhooks/simulate` payload twice → 2 documents (simulate is exempt from dedupe; each delivery is its own document)

- [x] T026 [US4] Run `python -m pytest tests/test_dedup.py -q` — confirm T022/T023/T025 PASS, T024 FAILS (RED)

### Implementation for User Story 4

- [x] T027 [US4] Edit `backend/main.py` lifespan: replace the single-field index on `external_message_id` with composite `[("user_id", 1), ("external_message_id", 1)]` and `partialFilterExpression={"external_message_id": {"$type": "string"}}`. Use `messages_collection.drop_index(...)` first to remove the old index if it exists (guard with try/except for `OperationFailure`); then `create_index` with the new spec. Idempotent across restarts

- [x] T028 [US4] Edit `backend/services/webhook_ingest.py`: in the `DuplicateKeyError` handler (~line 120), change `find_one({"external_message_id": external_message_id})` to `find_one({"user_id": user_id, "external_message_id": external_message_id})` — the recovery lookup is now user-scoped

- [x] T029 [US4] Run `python -m pytest tests/test_dedup.py -q` — confirm ALL tests including T024 now PASS (GREEN)

**Checkpoint**: US4 complete — dedupe key is `{user_id, external_message_id}`, cross-user same-key deliveries are independent, key-less exempt. No false dedupes.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Full suite green, no-regression, documentation.

- [x] T030 Run the full backend operational suite: `python -m pytest tests/ -q` from `backend/` (600s timeout) — all existing + new tests GREEN, no regression

- [x] T031 [P] Run `npm run lint` from repo root — expect clean (zero Day-29 frontend source changes)

- [x] T032 [P] Run `npx vitest run` from repo root — expect all frontend tests pass (no regression)

- [x] T033 [P] Update `AGENTS.md` manual additions: add a `020-security-testing man:` entry to the `<!-- MANUAL ADDITIONS -->` block documenting the new index (`{user_id, external_message_id}` composite), the `retry_pending_analyses()` sweeper in `main.py` lifespan, and the key-less/manual-create dedupe exemptions

- [ ] T034 Run quickstart.md manual smoke checks: register users A and B via API, create messages for each, attempt cross-user reads → 404; POST unsigned webhook → 403; verify no new dependencies or collections were added (`git diff --stat` shows only `backend/` + `AGENTS.md`)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (T001 confirms suite green)
- **US1 (Phase 3)**: Depends on Phase 2 — no code changes, verification only
- **US2 (Phase 4)**: Depends on Phase 2 — no code changes, verification only; **US1 and US2 are independent and can run in parallel**
- **US3 (Phase 5)**: Depends on Phase 2 — code fix (T019–T020) is independent of US1/US2 code but the full suite check in T030 runs after all stories
- **US4 (Phase 6)**: Depends on Phase 2 — code fix (T027–T028) is independent of US3; **US3 and US4 can run in parallel** (different files: `retry_pending.py` + `main.py` lifespan vs. `main.py` index + `webhook_ingest.py`)
- **Polish (Phase 7)**: Depends on all user stories (US1–US4) being complete

### Within Each User Story

- Tests written FIRST and confirmed (PASS for US1/US2, RED then GREEN for US3/US4)
- For US3/US4: code fix tasks run only after tests are confirmed red
- Commit after each code-fix task

### Parallel Opportunities

- **Phase 3 + Phase 4** (US1 + US2): entirely parallel — different test files, no code changes
- **Phase 5 + Phase 6** (US3 + US4): parallel after Phase 2 — different test files, different code files (the only overlap is `main.py`, but T020 edits lifespan loop while T027 edits the index block — different code regions; run sequentially if desired)
- **T031 + T032**: frontend lint and vitest are independent

---

## Parallel Example: User Story 1 + User Story 2

```bash
# Launch US1 and US2 test-writing in parallel (different test files):
Task: "Write backend/tests/test_security_testing.py — isolation matrix" [US1]
Task: "Add negative tests to backend/tests/test_webhooks.py" [US2]

# Both can run simultaneously — no file overlap
```

---

## Implementation Strategy

### TDD Within Each Story

1. Write the tests for the story
2. Run the tests: if the story requires no code fix (US1, US2), confirm PASS; if it does (US3, US4), confirm RED
3. Apply the code fix
4. Confirm GREEN
5. Move to the next story

### Incremental Delivery

1. Phase 1–2 complete → existing suite green, infra confirmed
2. US1 (isolation) complete → critical security invariant verified; deployable milestone
3. US2 (webhook) complete → boundary rejection verified; deployable milestone
4. US3 (AI reliability) complete → store-first + retry sweep working; deployable milestone
5. US4 (dedupe) complete → user-scoped dedupe working; deployable milestone
6. Polish → full suite green, no regression, documented

---

## Notes

- [P] tasks target different test files or are independent frontend checks
- [Story] labels map to spec.md user stories for traceability
- Each user story is independently completable and testable
- Tests MUST be written and confirmed (PASS or RED) before the associated code fix
- Commit after each code-fix task (T019, T020, T027, T028)
- Stop at any checkpoint to validate the story independently
- Avoid: vague tasks, same-file conflicts between stories, code changes before tests
