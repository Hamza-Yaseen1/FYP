# Tasks: AI Orchestrator (Day 24)

**Input**: Design documents from `specs/015-ai-orchestrator/`
**Prerequisites**: plan.md (required), spec.md (user stories), research.md,
data-model.md, contracts/ai-analysis-contract.md, quickstart.md
**Tests**: Included — the plan (Steps 5–6) specifies a pytest matrix, and the
spec mandates testable user scenarios (`## User Scenarios & Testing`). Tests
are written FIRST per story and must FAIL before implementation.
**Organization**: Tasks are grouped by user story to enable independent
implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US5)
- Include exact file paths in descriptions

## Contract → User Story Mapping

| Contract element | Served by |
|---|---|
| `RoutingDecision` + `decide_routing(content, message_type)` (pure rules) | US1 |
| `RoutingRecord` model + `AIAnalysis.routing` declared field | US5 (+ Foundational) |
| `orchestrate.process_message(...)` single entry point | US2 |
| `ai_analysis.routing` record contents (run/skip/reason/llm flag) | US5 |
| Trivial/skipped deterministic stub shapes (`status` completed/skipped) | US4 |
| Combined-result shape preserved for the Dashboard | US3 |
| `POST /messages`, webhook/simulate ingest → Orchestrator (one path) | US2, US3 |

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify the baseline — Day 24 adds NO new dependencies, so setup is
verification only.

- [x] T001 [P] Confirm the working branch is `015-ai-orchestrator` (`git branch --show-current`) and re-read the Day 24 design: `specs/015-ai-orchestrator/plan.md`, `specs/015-ai-orchestrator/spec.md`, `specs/015-ai-orchestrator/data-model.md`
- [x] T002 [P] Confirm `GROQ_API_KEY` and `GROQ_MODEL` are present in `backend/.env` (already set in earlier days); Day 24 introduces no new environment variables and no new runtime dependencies (routing uses stdlib `re` + `unicodedata` only)

**Acceptance Criteria**:
- Branch is `015-ai-orchestrator`; `backend/.env` already provides the Groq
  credentials; no dependency or env changes needed for this feature.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The shared response-model addition every story's stored record
depends on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T003 [P] Add `RoutingRecord` BaseModel and declare `routing: Optional[RoutingRecord] = None` on `AIAnalysis` in `backend/models/message.py`: fields `agents_run: list[str]`, `agents_skipped: list[str]`, `skip_reason: str = ""`, `triggers: list[str] = []`, `llm_call_used: bool = False`, `decided_at: datetime` (Pydantic 2 `extra='ignore'` drops undeclared keys, so without the declared field `routing` silently vanishes from `MessageResponse.ai_analysis`)

**Checkpoint**: `AIAnalysis(**{"priority": "normal", "routing": {...}})` parses
`routing`; legacy documents without the key serialize `routing: None`.

---

## Phase 3: User Story 1 - Every Message Gets Exactly the Analysis It Needs (Priority: P1) 🎯 MVP

**Goal**: `decide_routing` selects the smallest sufficient agent subset per
message (trivial → no tasks/deadline; action request → task extraction; time
expression → deadline; ambiguous/Arabic → full), and the analyzer gates both
outputs and task persistence to match.

**Independent Test**: `python -m pytest backend/tests/test_orchestrator.py -k routing` —
the decision-table suite sends greetings, action-without-deadline, action +
"tonight", long FYI, empty/media, and Arabic messages and asserts each routes
to exactly the expected subset (matches spec US1 independent test).

### Tests for User Story 1 (write FIRST; must FAIL before implementation) ⚠️

- [x] T004 [P] [US1] Add decision-table unit tests for `decide_routing` in `backend/tests/test_orchestrator.py`: `"ok"`/`"hi"` → trivial (`needs_llm=False`, task & deadline off); `"Please call me"` → task on, deadline off; `"The meeting is tomorrow"` → deadline on, task off; `"Send me the slides tonight."` → all five agents on; long FYI with no triggers → priority+summary only; `"أرسل الملفات"` → full default; `""`, `"   "`, and `message_type="media"` → `needs_analysis=False` (import `decide_routing` from `backend/services/ai/routing.py`)
- [x] T005 [P] [US1] Add routing-accuracy test `test_routing_accuracy_labeled_set` in `backend/tests/test_orchestrator.py`: run `decide_routing` over a labeled fixture of 50 messages (split across trivial/task-only/deadline-only/full/Arabic/empty classes) and assert ≥ 90% match the label (spec SC-002)
- [x] T006 [P] [US1] Add gating tests in `backend/tests/test_orchestrator.py` with a fake `AIAnalysisResult`: when Task Extraction is skipped `tasks_extracted=[]`, `deadlines=[]`, `recommended_action=""` after `_gate_outputs`, attention reflects the gated state, and `tasks_collection` receives ZERO inserts when `run_tasks=False` is passed through `analyze_message`

### Implementation for User Story 1

- [x] T007 [US1] Create `backend/services/ai/routing.py`: signal constants (`TASK_TRIGGER_KEYWORDS`, `TIME_EXPRESSION_KEYWORDS` overlapping `attention.NEAR_TERM_KEYWORDS`, `TRIVIAL_PHRASES`), helpers `has_trigger(content, keywords)`, `has_non_latin_script(content)` (via `unicodedata`), `looks_trivial(content, task_triggers, time_triggers)` (exact phrase match, OR ≤ 20 chars with no triggers), `RoutingDecision` dataclass, and `decide_routing(content, message_type="text") -> RoutingDecision` implementing the table with full-analysis fallback for ambiguous/unknown-language input (no I/O, stdlib only)
- [x] T008 [P] [US1] Extend `analyze_message(content, message_id, user_id, run_tasks=True)` in `backend/services/ai/analyzer.py`: gate the `tasks_collection.insert_many` block behind `if run_tasks and result.tasks_extracted:` so a skipped Task Extraction never persists task documents (spec FR-005 / SC-006)
- [x] T009 [US1] Add `_gate_outputs(analysis, routing) -> dict` in `backend/services/ai/analyzer.py`: clear `tasks_extracted`, `deadlines`, `recommended_action` (and `summary` when `run_summary` false) per `RoutingDecision`; call `evaluate_attention(analysis)` AFTER gating so `needs_attention`/`attention_reason` reflect the stored state

**Checkpoint**: Decision table + accuracy + gating suites green; task
persistence provably gated; existing analyzer behavior unchanged with the
defaults (`run_tasks=True`, full routing).

---

## Phase 4: User Story 2 - A Single Clear Orchestration Layer (Priority: P1)

**Goal**: `orchestrate.process_message` becomes the ONLY caller of the AI
pipeline; both ingestion paths (`_analyze_and_store`, `create_message`) and
the module exports route through it, proving a single auditable path.

**Independent Test**: `python -m pytest backend/tests/test_orchestrator.py -k call` plus
code inspection: every incoming message awaits `process_message` exactly once,
and `grep get_provider / analyze_message` finds no call sites outside the
Orchestrator and tests (spec US2 independent test).

### Tests for User Story 2 (write FIRST; must FAIL before implementation) ⚠️

- [x] T010 [US2] Add single-call test `test_process_message_single_provider_call` in `backend/tests/test_orchestrator.py`: monkeypatch the provider with an invocation counter and assert a rich message awaits provider `analyze` exactly once (spec FR-011 / SC-004)
- [x] T011 [P] [US2] Add entry-point test in `backend/tests/test_webhooks.py`: an ingested simulate message triggers `orchestrate.process_message` (spy) and NOT a direct `analyze_message` call
- [x] T012 [P] [US2] Add entry-point test in `backend/tests/test_messages.py`: `POST /messages` calls `orchestrate.process_message` (spy) and returns the stored message with the existing response shape

### Implementation for User Story 2

- [x] T013 [US2] Create `backend/services/ai/orchestrate.py`: `async process_message(content, message_id=None, user_id=None, message_type="text") -> dict` — `decide_routing` → when `needs_analysis` `await analyze_message(..., run_tasks=routing.run_task_extraction)` → `_gate_outputs(result)` → attach `analysis["routing"]` (`agents_run`, `agents_skipped`, `skip_reason`, `triggers`, `llm_call_used`, `decided_at`) → return the final dict
- [x] T014 [US2] Redirect `_analyze_and_store` in `backend/services/webhook_ingest.py` to call `process_message(content, message_id, user_id)` from `backend/services/ai/orchestrate.py` (persistence block unchanged)
- [x] T015 [P] [US2] Redirect `create_message` in `backend/routes/messages.py` to call `process_message(payload.content, message_id, user_id)` from `backend/services/ai/orchestrate.py` (response construction unchanged)
- [x] T016 [P] [US2] Export `process_message` from `backend/services/ai/__init__.py` (keep the `analyze_message` export for existing tests/scripts)
- [x] T017 [US2] Verify no bypass paths: `grep -rn "analyze_message" backend/routes backend/services` shows only `orchestrate.py`, `analyzer.py` and tests; add a completion log line in `process_message` recording one routing decision per message (spec FR-001 / FR-013 / SC-001)

**Checkpoint**: US2 suites green; every path funnels through one Orchestrator;
grep-verified no direct agent calls remain.

---

## Phase 5: User Story 3 - Final Result Is Unchanged for the Dashboard (Priority: P1)

**Goal**: The stored combined result keeps its existing shape and the Dashboard
keeps rendering from stored data only — zero frontend changes, zero behavior
drift.

**Independent Test**: `python -m pytest backend/tests/test_messages.py backend/tests/test_webhooks.py` —
a message created via `POST /messages` and one ingested via simulate both
return/store `ai_analysis` with all legacy fields plus the additive `routing`;
cards render identically (spec US3 independent test).

### Tests for User Story 3 (write FIRST; must FAIL before implementation) ⚠️

- [x] T018 [US3] Add test in `backend/tests/test_messages.py`: `POST /messages` response `ai_analysis` retains every existing field (`priority`, `confidence`, `explanation`, `summary`, `recommended_action`, `recommended_actions`, `tasks_extracted`, `deadlines`, `needs_attention`, `attention_reason`, `provider`, `analyzed_at`, `status`) and includes `routing` as an optional additive field (spec FR-010 / FR-012 / SC-005)
- [x] T019 [P] [US3] Add test in `backend/tests/test_webhooks.py`: a simulate ingestion background task persists `ai_analysis` (incl. `routing`) on the stored document so the Dashboard endpoint renders it (spec FR-015 / SC-008)

### Implementation for User Story 3

- [x] T020 [US3] Verify the Dashboard contract (no code change expected): confirm `git status --short -- frontend components` is clean, the stored result keeps the existing shape when all agents run, and no service/endpoint/component reads the Orchestrator at render time — only stored `ai_analysis` (spec FR-012)

**Checkpoint**: Dashboard rendering unchanged; response/stored shapes verified
additive-only; US3 tests green.

---

## Phase 6: User Story 4 - Trivial Messages Cost Almost Nothing (Priority: P2)

**Goal**: Trivial and no-content messages short-circuit `process_message` into
deterministic defaults with ZERO AI calls while still rendering on the
Dashboard.

**Independent Test**: `python -m pytest backend/tests/test_orchestrator.py -k trivial` — send
`"ok"`, `"hi"`, `""`, and a media message and assert `routing.llm_call_used`
is `false` and the provider `analyze` is never awaited, while a `completed`
deterministic result (or `skipped` stub) is returned (spec US4 independent
test / SC-007).

### Tests for User Story 4 (write FIRST; must FAIL before implementation) ⚠️

- [x] T021 [US4] Add test `test_trivial_message_zero_ai_calls` in `backend/tests/test_orchestrator.py`: for `"ok"`/`"hi"`/`"thanks"` assert `routing.llm_call_used is False`, provider `analyze` is never awaited, the deterministic result has priority `normal`, empty `tasks`/`deadlines`, and `status="completed"` (spec FR-011 / SC-004 / SC-007)
- [x] T022 [P] [US4] Add test `test_no_content_skipped_stub` in `backend/tests/test_orchestrator.py`: `""`, whitespace-only, and `message_type="media"` produce a stub with `status="skipped"`, priority `normal` (so `get_filter_counts` stays correct), and `routing.skip_reason="no analyzable content"` (spec FR-002 / EC-01 / EC-02)

### Implementation for User Story 4

- [x] T023 [US4] Add `_deterministic_defaults(routing, message_type) -> dict` and short-circuits in `backend/services/ai/orchestrate.py`: when `not routing.needs_analysis` return the `skipped` stub; when `needs_analysis` but `not routing.needs_llm` return the `completed` deterministic defaults (priority `normal`, confidence `0.5`, honest explanation `"Trivial message — deep analysis skipped by orchestrator."`, summary = content or `None`, empty tasks/deadlines/recs, `provider="rule-based"`) — both attach the routing record with `llm_call_used=False`

**Checkpoint**: Trivial + no-content suites green; zero AI spend on trivial
paths; Dashboard renders the stubs without blank/missing-state errors.

---

## Phase 7: User Story 5 - Routing Decisions Are Explainable (Priority: P2)

**Goal**: Every processed message carries an inspectable record naming the
agents run and skipped (with reason) and whether an AI call was used; failed
agents are distinguishable from deliberately skipped ones.

**Independent Test**: `python -m pytest backend/tests/test_orchestrator.py -k routing_record` —
inspect any stored/returned record and confirm agents run/skipped, reason, and
the AI-call flag; a forced provider failure yields `status="pending"` with
`llm_call_used=True`, distinct from a skip (spec US5 independent test /
FR-009).

### Tests for User Story 5 (write FIRST; must FAIL before implementation) ⚠️

- [x] T024 [US5] Add test `test_routing_record_complete` in `backend/tests/test_orchestrator.py`: for an analyzed message assert `agents_run ∪ agents_skipped = {priority, summary, task_extraction, deadline_detection, recommended_action}`, `priority ∈ agents_run`, `skip_reason`/`triggers` populated, and `routing` present on every path (full, trivial, skipped) (spec FR-009 / SC-003)
- [x] T025 [P] [US5] Add test `test_failure_distinct_from_skip` in `backend/tests/test_orchestrator.py`: force the provider to raise → returned dict has `status="pending"`, `routing.llm_call_used=True`, and `skip_reason` still explains the decision — assert pending (failed) and trivial (skipped) are distinguishable by `status` + `llm_call_used` (spec FR-009 / EC-08)

### Implementation for User Story 5

- [x] T026 [US5] Ensure the `routing` record is attached on ALL paths in `backend/services/ai/orchestrate.py` including the provider-failure fallback: wrap the `analyze_message` await so a raised/fallback `status="pending"` result still carries its routing record (`llm_call_used=True`) before being returned

**Checkpoint**: US5 suites green; explainability invariant holds on every path;
failure ≠ skip in the stored record.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Full-suite regression, standalone script validation, manual
Dashboard pass, and constitution compliance.

- [x] T027 [P] Full backend suite `python -m pytest tests/ -q` — **125 passed** in ~113s, no regressions, only pre-existing `utcnow` DeprecationWarnings (spec SC-008)
- [x] T028 [P] Standalone scripts w/ `PYTHONUTF8=1`: `test_ai_analysis.py` → **PASS** live (3/3, real Groq). `test_task_extraction.py` → 12 passed, 1 pre-existing stale fail (`test_tasks_stored_in_db_after_analysis` expects an insert without `user_id`; Day 18 isolation commit `20573d4` made it mandatory — predates orchestrator). `test_attention_pipeline.py` → 9/9 unit tests PASS; live dedup portion blocked-by-design in shared Atlas (one real connected WA owner exists, so a fresh test user never sees webhook messages); dedup proven directly: **2 deliveries → exactly 1 doc per `wamid.dup.*`**. `test_priority_integration.py` → era-stale (predates auth-gating; every request 401). Scripts left as-is per decision. Backend confirmed on **MongoDB Atlas**: `server_info 8.0.29`, `DB_NAME=communication_ai`, `MONGO_URI` from `backend/.env`
- [x] T029 Manual validation executed (steps 1–4): CLI routing table correct (`Send me the slides tonight.` full/triggers visible; `ok` trivial no LLM; `The meeting is tomorrow` deadline+task off; `أرسل الملفات` full); `process_message('hi')` → `completed`, `provider="rule-based"`, `routing.llm_call_used=false`. Live vs Atlas backend (throwaway script, 23/23): trivial `hi` → completed/trivial/`[priority, summary]`/no LLM; rich → full, all five agents, triggers `["send","tonight"]`, LLM used; long FYI → `[priority, summary]` only + **zero** `tasks` inserts; Arabic → `non_latin_script` full; empty → `skipped` stub w/ `skip_reason="no analyzable content"`; dashboard card contract intact (14 fields incl `routing`); `ai_analysis.routing` persisted in MongoDB
- [x] T030 Day 24 constitution items all verified against final code: single AI call preserved (one `provider.analyze()`/message; orchestrator adds zero round-trips); Priority never skipped (`agents_run` always started w/ priority); minimal agent subset (decision table + 50/50 accuracy test); trivial cheap (`needs_llm=False`, deterministic/`skipped` stub); explainable routing record (every path incl `pending` failures); no bypass paths (routes/services call `process_message`, grep-verified; only standalone debug scripts call `analyze_message`); fail toward full analysis (non-Latin/ambiguous → full; failure → `pending`); user isolation + Day 23 webhook rules unchanged (isolation/webhook suites green)

**Acceptance Criteria**:
- Full pytest suite green; standalone scripts green; quickstart manual pass
  complete; constitution Day 24 items all comply.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — **BLOCKS all user stories**
- **User Story 1 (Phase 3)**: Depends on Foundational (routing model not needed by `routing.py`, but the record-based response surface is)
- **User Story 2 (Phase 4)**: Depends on US1 (uses `decide_routing`, `_gate_outputs`, `run_tasks`)
- **User Story 3 (Phase 5)**: Depends on US2 (redirects land the routing-shaped results in responses/storage)
- **User Story 4 (Phase 6)**: Depends on US2 (edits `process_message` in `orchestrate.py`)
- **User Story 5 (Phase 7)**: Depends on US2 + US4 (record attach spans full/trivial/failure paths)
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: After Foundational — no dependency on other stories
- **US2 (P1)**: After US1 — needs the routing + gating primitives
- **US3 (P1)**: After US2 — needs the orchestrator-driven responses/storage
- **US4 (P2)**: After US2 — can run parallel to US3 (different tests; both touch orchestrate.py only in US4)
- **US5 (P2)**: After US2 (+ US4 for the failure-vs-skip interplay)

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models before services; core implementation before integration/redirects
- Story complete and independently testable before the next priority

### Parallel Opportunities

- Setup: T001, T002 run in parallel
- Foundational: single task (T003)
- US1: T004, T005, T006 run in parallel (all `test_orchestrator.py` — coordinate additions or split modules); T008 (`analyzer.py`) runs parallel to T007 (`routing.py`)
- US2: T011 + T012 run in parallel (`test_webhooks.py` vs `test_messages.py`); T015 + T016 run in parallel (`routes/messages.py` vs `ai/__init__.py`)
- US3: T018 + T019 run in parallel (`test_messages.py` vs `test_webhooks.py`)
- US4: T021 + T022 run in parallel (`test_orchestrator.py` additions)
- US5: T024 + T025 run in parallel (`test_orchestrator.py` additions)
- Polish: T027, T028 run in parallel
- Different user stories can be worked in parallel by different team members
  after Foundational completes (US2/US3 partly share `orchestrate.py`/redirects — coordinate)

---

## Parallel Example: User Story 2

```bash
# Launch the two entry-point tests together (different files, no deps):
Task: "Add process_message entry test in backend/tests/test_webhooks.py"
Task: "Add process_message entry test in backend/tests/test_messages.py"

# Launch the two export/redirect wiring tasks together:
Task: "Redirect create_message in backend/routes/messages.py"
Task: "Export process_message in backend/services/ai/__init__.py"
```

## Parallel Example: User Story 1

```bash
# Launch the three routing/gating test groups together:
Task: "Decision-table tests in backend/tests/test_orchestrator.py"
Task: "50-message labeled-accuracy test in backend/tests/test_orchestrator.py"
Task: "Gating + task-persistence-gate tests in backend/tests/test_orchestrator.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1 (routing correctness — the feature's core)
4. **STOP and VALIDATE**: decision-table + accuracy + gating suites green
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → response model ready for the record
2. US1 → correct routing + gating decisions (MVP core)
3. US2 → a single auditable orchestration layer
4. US3 → Dashboard verified unchanged, zero frontend drift
5. US4 → trivial/messages cost almost nothing
6. US5 → every routing decision explainable, failure ≠ skip
7. Polish → full suite green + manual Dashboard pass + constitution re-check

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: US1 → US2 (routing + orchestration layer, shared files)
   - Developer B: US3 (shape/regression verification) after US2's redirects
   - Developer C: US4 → US5 after US2 (edit `orchestrate.py` sequentially —
     not in parallel with A's US2 on the same file)
3. Stories complete and integrate independently; `orchestrate.py` edits
   (US2/US4/US5) are strictly sequential

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps each task to a user story for traceability
- Each user story is independently completable and testable
- Tests per story are written first and verified failing before implementation
- Commit after each task or logical group
- Stop at any checkpoint to validate the story independently
- Coordination notes: `backend/services/ai/orchestrate.py` is edited in US2
  (T013), US4 (T023), US5 (T026) — run these stories sequentially; the rest of
  each phase is parallelizable
- Avoid: vague tasks, same-file parallel conflicts, cross-story dependencies
  that break independence