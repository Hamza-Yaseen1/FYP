# Tasks: Agent Memory / Context (Day 25)

**Input**: Design documents from `specs/016-agent-memory/`
**Prerequisites**: plan.md (required), spec.md (user stories), research.md,
data-model.md, contracts/thread-identity-contract.md,
contracts/ai-context-prompt-contract.md, quickstart.md
**Tests**: Included — the plan (Steps 7–9) specifies a pytest matrix and the
spec mandates testable user scenarios (`## User Scenarios & Testing`). Tests
are written FIRST per story and must FAIL before implementation.
**Organization**: Tasks are grouped by user story to enable independent
implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US5)
- Include exact file paths in descriptions

## Focus-area → Task mapping (requested groupings)

| Focus area | Tasks |
|---|---|
| Database | T003 (model fields), T004 (indexes) — Foundational |
| Backend | T005 (link module), T015 (ingest wiring), T018, T022, T030 |
| AI Context | T011 (context.py), T012 (provider prompt), T013 (analyzer), T014 (orchestrator), T026 |
| Testing | Per-story test tasks T007–T010, T016–T017, T019–T021, T023–T025, T027–T028 + Polish T030–T031 |

## Contract → User Story Mapping

| Contract element | Served by |
|---|---|
| Identity fields (`messageId`/`threadId`/`conversationId`) + response mapping | Foundational (T003) |
| Per-user indexes `{user_id, conversationId|threadId, received_at}` | Foundational (T004) |
| `threads.py::resolve_and_stamp` (deterministic link + anchor stamping) | US1 (link), US2 (no link), US5 (isolation) |
| Ingest wiring in `webhook_ingest.py` + `routes/messages.py` | US1 (T015) |
| `fetch_thread_context` ≤ 5 + `build_context_block` + provider CONTEXT block | US1 |
| `validate_context_updates` / `apply_context_updates` (explainable outward revisions) | US4 (+ US1 happy path) |
| Single-call guarantee (context inside existing `analyze`) | US1 (T010), US3 (T019) |
| Dashboard renders stored results only — no new rendering path | US3 |
| User isolation on every resolve/fetch/update | US5 |

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify the baseline — Day 25 adds NO new runtime dependencies, so
setup is verification only.

- [x] T001 [P] Confirm the working branch is `016-agent-memory` (`git branch --show-current`) and re-read the Day 25 design: `specs/016-agent-memory/plan.md`, `specs/016-agent-memory/spec.md`, `specs/016-agent-memory/data-model.md`, `specs/016-agent-memory/contracts/thread-identity-contract.md`, `specs/016-agent-memory/contracts/ai-context-prompt-contract.md`
- [x] T002 [P] Confirm no new runtime dependencies or env vars are introduced: linking uses stdlib `re` + `datetime.timedelta`; `LINK_WINDOW_MINUTES` defaults to `60` and is optional (documented in plan.md Step 1); `GROQ_API_KEY`/`GROQ_MODEL` already in `backend/.env`

**Acceptance Criteria**:
- Branch is `016-agent-memory`; docs re-read; no dependency or mandatory env
  changes; `LINK_WINDOW_MINUTES` override is the only new (optional) knob.

--- 

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The shared identity model, indexes, and the deterministic link
module that every user story's storage/behavior depends on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T003 [P] Add `ContextUpdate` BaseModel and declare `messageId: Optional[str]`, `threadId: Optional[str]`, `conversationId: Optional[str]` on `MessageResponse` in `backend/models/message.py` (`context_updates` sentiment: `ContextUpdate` fields `field`, `value`, `source_message_id`, `reason`, `applied_at`); map them in `message_doc_to_response` — `messageId` defaults to `str(doc["_id"])`, `threadId`/`conversationId` from `doc.get(...)` (Pydantic 2 drops undeclared keys, so the fields MUST be declared or they silently vanish from responses)
- [x] T004 [P] Add the two per-user indexes in the `lifespan` block of `backend/main.py`: `await messages_collection.create_index([("user_id", 1), ("conversationId", 1), ("received_at", -1)])` and `await messages_collection.create_index([("user_id", 1), ("threadId", 1), ("received_at", -1)])` (constitution's `receivedAt` concept is realized by the existing `received_at` field — research.md §3.3)
- [x] T005 [P] Create `backend/services/threads.py`: `LINK_WINDOW_MINUTES = int(os.getenv("LINK_WINDOW_MINUTES", "60"))`; `def normalize_sender(sender) -> str` (`.strip().lower()`); `async def resolve_and_stamp(user_id, source, sender, received_at) -> tuple[str | None, str | None]` — find latest `{user_id, source, sender: normalized, state: "active", received_at: {"$gte": received_at - timedelta(minutes=LINK_WINDOW_MINUTES)}}` sorted `received_at` desc; none → `(None, None)`; candidate has `threadId` → inherit `(threadId, threadId)`; else anchor: `thread_id = str(candidate["_id"])`, guard-stamp candidate via `find_one_and_update({"_id": candidate["_id"], "user_id": user_id}, {"$set": {"threadId": thread_id, "conversationId": thread_id}})` then return `(thread_id, thread_id)` (no threadId is ever minted for a lone message; every query is user-scoped)
- [x] T006 [P] Verify no memory-framework artifacts (spec FR-015 / SC-008): `rg -i "vector|embedding|rag" backend/services backend/models` returns only documentation/prompt-text mentions, zero runtime imports

**Checkpoint**: Response fields serialize `None` when absent; indexes created
on startup; `resolve_and_stamp` is importable and pure-logic testable with a
fake collection (never motor under `asyncio.run`); no new deps.

---

## Phase 3: User Story 1 - A Follow-Up Message Completes an Earlier Task (Priority: P1) 🎯 MVP

**Goal**: Ingest wires the deterministic link; then the ≤5 most recent
same-thread messages are injected into the existing single AI call, and a
validated deadline/urgency revision is stored on the anchor message with an
explanation naming the follow-up.

**Independent Test**: `python -m pytest backend/tests/test_threads.py backend/tests/test_context_ai.py -k "link or context or enrich"` —
send "Can you send the report?" then "Need it before our meeting." and assert
the pair shares one `threadId` and the first message gains an explainable
`context_updates` item naming the second (spec US1 independent test /
SC-004).

### Tests for User Story 1 (write FIRST; must FAIL before implementation) ⚠️

- [x] T007 [P] [US1] Add link-rule unit tests in `backend/tests/test_threads.py` (fake in-memory collection, never motor under `asyncio.run`): first message → `(None, None)`; in-window same user/source/sender → anchor thread (`threadId == str(first._id)`); chain A→B→C stays linked when B→C in-window; window boundary 59:59 links / 60:01 does not; `normalize_sender("  Ali  ") == "ali"` (spec FR-002/FR-003)
- [x] T008 [P] [US1] Add labeled-set test `test_labeled_30_pairs` in `backend/tests/test_threads.py`: table of 30 message pairs (mix of same-sender in-window pairs — ≥ 24 expected-linked for ≥ 80% recall — plus different-sender/channel/out-of-window pairs that MUST NOT link); assert false-link count ≤ 1 (≤ 5%, SC-002) and recall ≥ 80% (SC-003); print both rates
- [x] T009 [P] [US1] Add context-fetch/injection test in `backend/tests/test_context_ai.py`: with a `thread_id`, `fetch_thread_context` returns ≤ 5 most recent same-user messages excluding the message being analyzed; `build_context_block` is non-empty and brace-safe; a mocked `GroqProvider.analyze` captures the prompt and shows the `CONTEXT — PREVIOUS MESSAGES IN THIS CONVERSATION` block only when context is passed (the `context=None` case is covered in US3)
- [x] T010 [P] [US1] Add single-call + enrich test in `backend/tests/test_context_ai.py`: monkeypatch the provider with an invocation counter, asserting exactly ONE `analyze` await per analyzed message, spec FR-008/SC-006); a mocked response with `context_updates: [{target, field:"deadline", value:"before the meeting", source, reason}]` is applied to the anchor document with `source_message_id` + `reason` (spec US1 acceptance 1 / FR-009)

### Implementation for User Story 1

- [x] T011 [P] [US1] Create `backend/services/ai/context.py`: `async fetch_thread_context(user_id, thread_id, exclude_message_id, limit=5)` (user+thread scoped, sorted `received_at` desc, exclude self, enrich each with `handle = str(_id)[-7:]`); `build_context_block(messages) -> str | None`; `_handle_to_id(handle, messages)`; `validate_context_updates(candidates, thread_messages, current_message_id)`; `async apply_context_updates(valid_updates, current_message_id, user_id) -> int` (`$push` into `ai_analysis.context_updates` on `{_id: target, user_id}` only)
- [x] T012 [P] [US1] Extend the provider contract in `backend/services/ai/providers/base.py`: `async analyze(self, message, context=None)` (default keeps current behavior) and add `context_updates: list[dict] = []` to `AIAnalysisResult`; then `backend/services/ai/providers/groq.py`: render a `CONTEXT — PREVIOUS MESSAGES IN THIS CONVERSATION` block into `ANALYSIS_PROMPT` via `.replace("{context}", ...)` ONLY when context is present (rules: may enrich missing deadline/urgency; MUST NOT override an explicit statement in the current message; may emit `context_updates` using context handles; never invent values not in the linked messages) and parse `context_updates` from the JSON; mirror the signature in `backend/services/ai/providers/openai.py` (best-effort parity, zero behavior change without context)
- [x] T013 [P] [US1] Extend `analyze_message(message_content, message_id=None, user_id=None, run_tasks=True, routing=None, context_messages=None)` in `backend/services/ai/analyzer.py` to forward `context_messages` to `provider.analyze(...)` and include `context_updates: list(result.context_updates)` in the returned dict (consumed by the Orchestrator, never stored verbatim on the current message)
- [x] T014 [US1] Wire the Orchestrator in `backend/services/ai/orchestrate.py`: give `process_message(..., thread_id=None)` an analyze-branch step that, when `thread_id` and `routing.needs_llm`, fetches context via `context.fetch_thread_context`, passes it into `_analyze_with_fallback(..., context_messages=context)`, then validates + applies `analysis.get("context_updates")` on the anchor (each step in its own try/except — never raises, never blocks; pop `context_updates` before returning the current message's analysis)
- [x] T015 [P] [US1] Store identity fields at both entry points: `ingest_message` in `backend/services/webhook_ingest.py` calls `resolve_and_stamp(user_id, source, sender, now)` before insert, stores `messageId` (always) and `threadId`/`conversationId` (when linked) in the doc, and passes `thread_id` to `_analyze_and_store(content, message_id, user_id, thread_id=None)` → `process_message`; `create_message` in `backend/routes/messages.py` does the same resolve+store and passes `thread_id` into `process_message`

**Acceptance Criteria**:
- A simulated pair (report + "Need it before our meeting.") shares one
  `threadId`; the first message's stored record gains a `context_updates`
  entry with a reason naming the second message; the current message stores a
  normal analysis with a `CONTEXT` block prompt; provider `analyze` awaited
  exactly once per analyzed message.
- Standalone behavior unchanged (no link = null `threadId`, identical
  analysis).

**Checkpoint**: Link + context + enrichment suites green on a fake
collection + mocked provider; both entry points persist the identity fields.

---

## Phase 4: User Story 2 - Unrelated Messages Stay Independent (Priority: P1)

**Goal**: The link rule's negative path — different senders, different
channels, or out-of-window arrivals never group, and each unrelated message is
analyzed exactly as today.

**Independent Test**: `python -m pytest backend/tests/test_threads.py -k independent` —
messages from a different sender, a different channel, or > 60 minutes apart
keep null `threadId`/`conversationId` and independent analysis (spec US2
independent test).

### Tests for User Story 2 (write FIRST; must FAIL before implementation) ⚠️

- [x] T016 [P] [US2] Add no-link unit tests in `backend/tests/test_threads.py`: different sender → no link; same sender different `source` → no link; same sender gap > `LINK_WINDOW_MINUTES` → no link; parallel same-sender strands resolve to the latest consecutive arrival (never a wrong cross-strand link, spec EC-13); media-only / empty messages still store identity without injecting context (spec FR-011)
- [x] T017 [US2] Add standalone-analysis regression test in `backend/tests/test_messages.py`: `POST /messages` for an unlinked message returns `threadId`/`conversationId` null and an `ai_analysis` identical to the Day 24 shape (spec US2 acceptance 1 + 2)

### Implementation for User Story 2

- [x] T018 [US2] Verify the negative path end-to-end (no new code expected): confirm `resolve_and_stamp` in `backend/services/threads.py` returns `(None, None)` for sender/channel/window mismatches and that both entry points (T015) store null identity as a result; grep confirms no path invents a `threadId` for a lone or unrelated message (spec FR-002/FR-003)

**Acceptance Criteria**:
- Unrelated messages never share a `threadId`; they analyze independently with
  the exact Day 24 stored shape.

**Checkpoint**: Negative-path suites green; null-identity stored path proven.

---

## Phase 5: User Story 3 - Existing Pipeline and Dashboard Keep Working (Priority: P1)

**Goal**: Standalone messages are analyzed byte-identically to Day 24 (including
the exact prompt), the additive identity fields never change the response
shape, and the Dashboard keeps rendering stored results only with zero
frontend changes.

**Independent Test**: `python -m pytest backend/tests/test_messages.py backend/tests/test_webhooks.py -k standalone` and
`git status --short -- frontend components` is clean (spec US3 independent
test).

### Tests for User Story 3 (write FIRST; must FAIL before implementation) ⚠️

- [x] T019 [P] [US3] Add byte-compat prompt test in `backend/tests/test_context_ai.py`: with `context=None`, a mocked provider receives the exact Day 24 `ANALYSIS_PROMPT` (no `CONTEXT` block, assert equality) — the zero-regression guard (spec SC-005)
- [x] T020 [P] [US3] Add test in `backend/tests/test_webhooks.py`: a simulate ingestion persists `messageId` (and null `threadId` when standalone) with an unchanged `ai_analysis` incl. the Day 24 `routing` record (spec FR-013/SC-005)
- [x] T021 [P] [US3] Add test in `backend/tests/test_messages.py`: `POST /messages` response includes `messageId`/`threadId`/`conversationId` as additive optional fields while every existing field of `MessageResponse.ai_analysis` stays present and unchanged (spec FR-011/SC-005)

### Implementation for User Story 3

- [x] T022 [US3] Verify the Dashboard contract (no code change expected): `git status --short -- frontend components` is clean; grep confirms no service/endpoint/component reads `threadId`/`conversationId`/`context_updates` at render time — the UI reads stored `ai_analysis` only (spec FR-013)

**Acceptance Criteria**:
- Standalone stored analysis and Dashboard cards are identical to Day 24;
  `context=None` prompt is byte-identical; frontend untouched.

**Checkpoint**: Regression suites green; frontend clean; additive fields only.

---

## Phase 6: User Story 4 - Context Is Explainable and Dismissible (Priority: P2)

**Goal**: Enrichment is provable — forged/self/unproven context updates are
dropped, targets are limited to the same thread and user, and every applied
revision is an additive, reason-named change that never rewrites the original
analysis; an explicit user-stated fact always wins.

**Independent Test**: `python -m pytest backend/tests/test_context_ai.py -k validate` —
invalid `context_updates` (unknown target, self-target, disallowed field,
value absent from source content, unlabelled source) are dropped with zero
writes; original analysis fields of the anchor are unchanged (spec US4
independent test / FR-009).

### Tests for User Story 4 (write FIRST; must FAIL before implementation) ⚠️

- [x] T023 [P] [US4] Add validation tests in `backend/tests/test_context_ai.py`: `validate_context_updates` drops candidates with unknown target handle, target == the message currently being analyzed, `field` ∉ {`deadline`, `priority`, `note`}, `value` not a verbatim substring of the source message's content, or unknown source handle — assert ZERO writes to the anchor on drop (spec FR-009 / constitution "NEVER invent") 
- [x] T024 [P] [US4] Add scoping test in `backend/tests/test_context_ai.py`: a `context_updates` candidate targeting a message in a DIFFERENT thread or DIFFERENT user is never applied (`apply_context_updates` writes only on `{_id: target, user_id}`), and `fetch_thread_context` for user A never includes user B's messages (spec FR-006/FR-014)
- [x] T025 [P] [US4] Add explainability test in `backend/tests/test_context_ai.py`: an applied update stores `field`, `value`, `source_message_id`, `reason`, `applied_at`; the anchor's ORIGINAL `ai_analysis` fields (e.g. `priority`, `deadlines`, `tasks_extracted`) are unchanged (constitution "NEVER silently rewrite prior analysis"; spec US4 acceptance 2)

### Implementation for User Story 4

- [x] T026 [US4] Enforce explainability invariants in `backend/services/ai/context.py` + `backend/services/ai/orchestrate.py`: log every dropped candidate with its drop reason; pop `context_updates` from the current message's analysis before it is stored; keep the prompt rule that an explicitly stated user fact beats inferred context; confirm anchor updates are `$push`-only additive revisions (never `$set` on analysis fields) (spec FR-010 / constitution Day 25 Core Principle #4)

**Acceptance Criteria**:
- Invalid context candidates never reach storage; applied revisions are
  additive and reason-named; original wording is never overwritten; a stated
  deadline always beats inferred context.

**Checkpoint**: Validation + scoping + explainability suites green.

---

## Phase 7: User Story 5 - Threads Contain Only My Messages (Priority: P1)

**Goal**: Linked data is isolation-safe — resolve, context fetch, and context
update are all user-scoped, so a thread never contains another user's messages
even on the same channel with the same sender.

**Independent Test**: `python -m pytest backend/tests/test_threads.py backend/tests/test_context_ai.py -k isolation` —
two users on the same channel/sender in-window each get their own `threadId`;
no enrichment targets another user's message; the existing two-user isolation
suite still passes (spec US5 independent test / SC-007).

### Tests for User Story 5 (write FIRST; must FAIL before implementation) ⚠️

- [x] T027 [US5] Add two-user isolation test in `backend/tests/test_threads.py` (fake collection): user A and user B, same `source` + same sender + in-window arrival → each gets its own distinct `threadId`; neither thread contains the other user's messages; `resolve_and_stamp` is invoked with each user's own `user_id` (spec US5 acceptance / FR-006)
- [x] T028 [P] [US5] Add isolated-enrichment test in `backend/tests/test_context_ai.py`: a `context_updates` candidate whose source/target belongs to user B is dropped when processing user A (spec FR-014 + FR-009)

### Implementation for User Story 5

- [x] T029 [US5] Verify user scoping across all new code (no new code expected beyond confirmations): grep confirms `user_id` filters on every resolve (`backend/services/threads.py`), fetch, and update (`backend/services/ai/context.py`); confirm the existing `backend/tests/test_user_isolation.py` still passes (spec FR-006/SC-007)

**Acceptance Criteria**:
- Two-user isolation test passes; a thread or context revision can never span
  users across all new code paths.

**Checkpoint**: Isolation suites green; user scoping grep-verified.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Full-suite regression, manual quickstart pass, and constitution
Day 25 compliance.

- [x] T030 [P] Run the full backend suite `python -m pytest tests/ -q` (300s shell timeout) — all green incl. `test_threads.py` and `test_context_ai.py`, no regressions in `test_messages.py`, `test_webhooks.py`, `test_user_isolation.py` (spec SC-005/SC-007)
- [x] T031 [P] Execute the manual quickstart pass per `specs/016-agent-memory/quickstart.md`: (i) standalone message → card identical to today; (ii) "Can you send the report?" then "Need it before our meeting." → shared thread + explainable deadline update naming the follow-up; (iii) different sender → independent; (iv) trivial `ok` as a follow-up still links (data) with zero LLM; confirm MongoDB fields and no Dashboard nulls (spec SC-004/SC-005) — automated as `backend/tests/test_quickstart_day25.py` (fake collection + scripted 2-message flow, anchors the current-message-as-source contract)
- [x] T032 [P] Day 25 constitution re-check against final code: quality bar (labeled 30-pair = ≤ 5% false links, ≥ 80% recall); single-call preserved (provider-count test green); isolation intact; no memory framework (grep, greppable `messageId` present on 100%); explainability invariants; AGENTS.md already refreshed via `update-agent-context.ps1 -AgentType opencode` (spec SC-001..SC-008)

**Acceptance Criteria**:
- Full pytest suite green; manual quickstart pass complete; all eight SC's
  verified against final code.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — **BLOCKS all user stories**
- **User Story 1 (Phase 3)**: Depends on Foundational (uses `threads.py`, model fields, indexes)
- **User Story 2 (Phase 4)**: Depends on US1 (endpoint regression test T017 needs the identity wiring from T015)
- **User Story 3 (Phase 5)**: Depends on US1 (byte-compat + shape tests exercise the wired stores)
- **User Story 4 (Phase 6)**: Depends on US1 (uses `context.py` validation/application)
- **User Story 5 (Phase 7)**: Depends on US1 (uses `threads.py` + `context.py` scoping)
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)** — MVP: the full link + context + enrichment slice
- **US2 (P1)**: after US1 — asserts the negative path of US1's link
- **US3 (P1)**: after US1 — asserts zero regression from US1's wiring
- **US4 (P2)**: after US1 — hardens US1's enrichment with validation/explainability
- **US5 (P1)**: after US1 — proves US1's link/context is isolation-safe

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models/modules before wiring; context module before orchestrator wiring
- Core implementation before integration/redirects
- Story complete and independently testable before the next priority

### Parallel Opportunities

- Setup: T001, T002 run in parallel
- Foundational: T003, T004, T005, T006 run in parallel (different files)
- US1: tests T007, T008, T009, T010 run in parallel (T007/T008 share `test_threads.py` — coordinate or split modules); implementation T011 (context.py), T012 (providers), T013 (analyzer.py), T015 (ingest wiring) run in parallel; T014 (orchestrate.py) AFTER T011+T012+T013; T015 is independent of the context chain and can run in parallel
- US2: T016, T017 run in parallel (`test_threads.py` vs `test_messages.py`)
- US3: T019, T020, T021 run in parallel (`test_context_ai.py` vs `test_webhooks.py` vs `test_messages.py`)
- US4: T023, T024, T025 run in parallel (shared `test_context_ai.py` — coordinate)
- US5: T027, T028 run in parallel
- Polish: T030, T031, T032 run in parallel
- After Foundational, US2–US5 may run in parallel by different team members after US1's wiring (T014/T015) lands

---

## Parallel Example: User Story 1

```bash
# Launch the four test groups together (coordinate the two touching test_threads.py):
Task: "Link-rule unit tests in backend/tests/test_threads.py"
Task: "Labeled 30-pair accuracy test in backend/tests/test_threads.py"
Task: "Context fetch/injection tests in backend/tests/test_context_ai.py"
Task: "Single-call + enrich tests in backend/tests/test_context_ai.py"

# Launch the implementation modules together:
Task: "Create backend/services/ai/context.py"
Task: "Extend provider prompt in backend/services/ai/providers/groq.py"
Task: "Extend analyze_message in backend/services/ai/analyzer.py"
```

## Parallel Example: User Story 4

```bash
# Launch the three validation/explainability test groups together:
Task: "Validation-drop tests in backend/tests/test_context_ai.py"
Task: "Cross-thread/user scoping test in backend/tests/test_context_ai.py"
Task: "Explainability (reason-named, additive) test in backend/tests/test_context_ai.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1 (link + bounded context + enrich)
4. **STOP and VALIDATE**: test_threads.py + test_context_ai.py link/context/enrich suites green
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → identity model, indexes, deterministic link module
2. US1 → pair linkage + context inside the single call + validated anchor
   enrichment (MVP core)
3. US2 → unrelated messages provably independent
4. US3 → zero regression for standalone messages + Dashboard contract
5. US4 → enrichment explainable, validated, dismissible
6. US5 → isolation proven across every new path
7. Polish → full suite green + manual quickstart pass + constitution re-check

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: US1 (context.py, providers, analyzer, orchestrate.py, ingest wiring) — the shared spine
   - Developer B: US2/US3 test stories after US1 wiring (touch `test_threads.py`/`test_messages.py`/`test_webhooks.py`)
   - Developer C: US4→US5 after US1 (share `test_context_ai.py` and rely on context.py — run sequentially with A's US1)
3. Stories complete and integrate independently; `context.py`, `providers`, and `analyzer.py` edits are strictly sequential across stories

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps each task to a user story for traceability
- Each user story is independently completable and testable
- Tests per story are written first and verified failing before implementation
- Commit after each task or logical group
- Stop at any checkpoint to validate the story independently
- Coordination notes: `backend/services/ai/context.py` is edited in US1 (T011)
  and US4 (T026) — sequential; `backend/services/ai/orchestrate.py` in US1 only;
  `backend/tests/test_context_ai.py` is shared across US1/US3/US4/US5 —
  coordinate additions or split per story
- Avoid: vague tasks, same-file parallel conflicts, cross-story dependencies
  that break independence