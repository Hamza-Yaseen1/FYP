# Tasks: Task Extraction & Deadline Detection

**Input**: Design documents from `/specs/004-task-extraction-deadline/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), data-model.md, contracts/

**Tests**: Tests are included per user request.

**Organization**: Tasks are grouped by user story. US1 (Task Extraction) and
US2 (Deadline Detection) are combined into one phase because they are tightly
coupled and both P1 — deadline detection is embedded in the extraction prompt.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Data models that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T001 Create ExtractedTask Pydantic model in `backend/models/task.py` with fields: description (str), deadline (str | None), priority_indicator (str | None), requires_action (bool). Add TaskResponse model with fields: id, description, deadline, priority_indicator, requires_action, status, source_message_id, source_message_preview, created_at. See `specs/004-task-extraction-deadline/data-model.md` for field types and validation rules.
- [x] T002 Update AIAnalysisResult in `backend/services/ai/providers/base.py`: change `tasks_extracted: list[str] = []` to `tasks_extracted: list[dict] = []` (list of ExtractedTask dicts). Import is not needed here since base.py uses plain dict lists for flexibility.
- [x] T003 Update AIAnalysis in `backend/models/message.py`: change `tasks_extracted: list[str] = []` to `tasks_extracted: list[dict] = []` and add `from models.task import ExtractedTask` import. Update `message_doc_to_response` to handle the new task structure.

**Checkpoint**: Models ready — user story implementation can now begin

---

## Phase 2: User Story 1 + 2 — Task Extraction & Deadline Detection (Priority: P1) 🎯 MVP

**Goal**: AI extracts tasks with deadlines from messages and stores them in MongoDB

**Independent Test**: Send messages with clear action items ("Send me the FYP slides tonight"), verify tasks are extracted with correct description, deadline, and priority indicator. Send informational messages, verify no tasks extracted. Send messages with no deadlines, verify deadline is null.

### Tests for User Story 1 + 2 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T004 [P] [US1] [US2] Create test file `backend/test_task_extraction.py` with test cases: (1) message with clear task → task extracted with description and deadline, (2) informational message → no tasks, (3) message with no deadline → deadline is null, (4) message with "ASAP" → deadline is "ASAP" and priority is urgent, (5) message with "I'll send you files" → no task (sender's promise), (6) AI failure → empty tasks array, status "pending". Use pytest with mocked Groq provider.

### Implementation for User Story 1 + 2

- [x] T005 [P] [US1] [US2] Update priority prompt in `backend/services/ai/prompts/priority.txt`: Add task extraction section after priority rules. Instruct model to return combined JSON with priority, confidence, explanation, tasks_extracted (array of objects with description, deadline, priority_indicator, requires_action), and deadlines (array of strings). Add CRITICAL RULES: only extract explicit tasks, preserve deadline wording exactly, null if no deadline, never invent tasks. Include 3 examples: "Send me the FYP slides tonight" → task with deadline "Tonight", "Can you review this?" → task with null deadline, "I'll send files tomorrow" → no tasks. See `specs/004-task-extraction-deadline/research.md` for prompt structure.
- [x] T006 [P] [US1] [US2] Update tasks prompt in `backend/services/ai/prompts/tasks.txt`: Add deadline detection rules. Add supported time expressions table: ASAP/right now → urgent, tonight/today → urgent, tomorrow → important, this week/by Friday → important, next week → normal, before the meeting → preserve original. Add rule: NEVER invent a specific date from relative expression. Add rule: preserve original wording when exact conversion unreliable.
- [x] T007 [US1] [US2] Update Groq provider in `backend/services/ai/providers/groq.py`: Modify `analyze()` method to parse `tasks_extracted` and `deadlines` from LLM JSON response. Map `tasks_extracted` array of objects to AIAnalysisResult. Map `deadlines` array of strings. Add validation: if tasks_extracted is not a list, default to empty list. If individual task missing description, skip it. Keep existing `normalize_priority()` and `clean_response()` functions.
- [x] T008 [US1] [US2] Update analyzer in `backend/services/ai/analyzer.py`: After getting AI analysis result, extract tasks from `result.tasks_extracted`. For each task with non-null description, insert into `tasks_collection` with source_message_id, source_message_preview (first 100 chars of message_content), status "pending", and created_at. Import `tasks_collection` from `database.py`. Handle insert failures gracefully (log error, continue — don't fail the whole analysis).
- [x] T009 [US1] [US2] Update message creation route in `backend/routes/messages.py`: Import `tasks_collection` from database. After `analyze_message()` call, the analyzer now handles task storage. No changes needed to the route itself if analyzer handles it — verify by reading analyzer.py after T008. If analyzer doesn't store tasks, add task storage logic here as fallback.
- [x] T010 [US1] [US2] Update webhook route in `backend/routes/webhooks.py`: Same as T009 — verify analyzer handles task storage after AI analysis. If not, add task storage logic after the `analyze_message()` call. Import `tasks_collection` if needed.
- [x] T011 [US1] [US2] Create task routes in `backend/routes/tasks.py`: Create FastAPI router with prefix "/tasks". Implement GET /tasks (list all tasks, optional ?status=pending|completed filter), PUT /tasks/{task_id}/status (update status, validate "pending" or "completed"), DELETE /tasks/{task_id} (delete task, return 204). Use `tasks_collection` from database.py. Import TaskResponse from models/task.py. Register router in `backend/main.py`.
- [x] T012 [US1] [US2] Register tasks router in `backend/main.py`: Import `tasks` router from `routes.tasks`. Add `app.include_router(tasks.router)` after existing message and webhook routers. Verify no import cycles.

**Checkpoint**: Task extraction works end-to-end — send message → AI extracts tasks → tasks stored in MongoDB → tasks accessible via GET /tasks

---

## Phase 3: User Story 3 — View Extracted Tasks on Dashboard (Priority: P2)

**Goal**: Users see task indicators on messages and can view all tasks on Tasks page

**Independent Test**: Send messages that produce tasks, verify dashboard shows task count badges on those message cards. Navigate to Tasks page, verify all tasks listed with description, deadline, status, and source message preview.

### Implementation for User Story 3

- [x] T013 [P] [US3] Update MessageList interface and display in `components/MessageList.tsx`: Add `tasks_extracted` and `deadlines` to the Message interface's ai_analysis type (array of objects with description, deadline, priority_indicator, requires_action). Add a task count badge next to the priority badge: show "N tasks" in a small badge (e.g., `bg-purple-500/15 text-purple-400`) when `tasks_extracted.length > 0`. Place it after the PriorityBadge in the message card header.
- [x] T014 [P] [US3] Create TaskList component in `components/TaskList.tsx`: Create a "use client" React component that fetches tasks from `http://localhost:8000/tasks`. Display each task as a card with: description, deadline (or "No deadline"), priority indicator, status badge (pending=yellow, completed=green), source message preview. Add a "Mark Complete" button that calls `PUT /tasks/{id}/status` with status "completed" and refreshes the list. Add a "Delete" button that calls `DELETE /tasks/{id}` and removes from list. Show empty state "No tasks yet" when no tasks exist. Show loading spinner while fetching.
- [x] T015 [US3] Replace tasks page placeholder in `app/(dashboard)/tasks/page.tsx`: Replace the current server component with a client component that renders the TaskList component. Import TaskList from `@/components/TaskList`. Keep the page header ("Tasks — Communication AI" metadata). Wrap in same layout div with p-6 spacing.
- [x] T016 [US3] Update dashboard page in `app/(dashboard)/dashboard/page.tsx`: Add a "Tasks" summary card to the grid alongside Urgent/Important/Normal cards. Fetch task count from `http://localhost:8000/tasks?status=pending` on mount. Display pending task count with a clipboard icon. Use `useEffect` + `useState` for client-side fetch. Style consistently with existing summary cards.

**Checkpoint**: Full vertical slice complete — message arrives → tasks extracted → dashboard shows badges → Tasks page lists all tasks → user can mark complete/delete

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: Testing, edge cases, documentation

- [x] T017 [P] Run test suite in `backend/test_task_extraction.py`: Execute `pytest backend/test_task_extraction.py -v`. Fix any failures. Add edge case tests: very long message (10,000+ chars), message with multiple tasks, message in non-English (should extract no tasks). Verify all tests pass.
- [x] T018 [P] Manual testing checklist: Send all 9 test messages from `specs/004-task-extraction-deadline/quickstart.md`. Verify each produces expected task extraction and deadline. Check dashboard shows task badges. Check Tasks page shows all tasks. Verify AI failure graceful fallback (stop backend, send message, verify no errors on frontend).
- [x] T019 Verify constitution compliance: Check against `specs/004-task-extraction-deadline/plan.md` Constitution Check table. Verify: no false positives (informational messages produce no tasks), no invented deadlines (deadline is null when not in message), single LLM call (monitor Groq API logs), graceful fallback (empty tasks on AI failure). Run linting: `npm run lint` for frontend, check Python style for backend.
- [x] T020 Update quickstart.md with any discovered issues: If test messages produce unexpected results, update the expected behavior table. If API contract changed during implementation, update contracts/messages-api.md. Ensure all examples in quickstart.md are accurate.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 1)**: No dependencies — can start immediately
- **US1+US2 (Phase 2)**: Depends on Phase 1 completion — BLOCKS Phase 3
- **US3 (Phase 3)**: Depends on Phase 2 completion (needs tasks in database to display)
- **Polish (Phase 4)**: Depends on Phase 3 completion

### Within Phase 2 (US1+US2)

- T004 (tests) should be written FIRST and verified to FAIL
- T005, T006 (prompts) can run in parallel [P]
- T007 (groq.py) depends on T005, T006 (needs updated prompts)
- T008 (analyzer.py) depends on T002, T003 (needs updated models)
- T009, T010 (routes) depend on T008 (needs analyzer to store tasks)
- T011 (task routes) can run in parallel with T007-T010 [P]
- T012 (main.py) depends on T011 (needs tasks router)

### Within Phase 3 (US3)

- T013 (MessageList badge) and T014 (TaskList component) can run in parallel [P]
- T015 (tasks page) depends on T014 (needs TaskList component)
- T016 (dashboard page) depends on T013 (needs updated MessageList types)

### Parallel Opportunities

- T005 + T006: Both prompt updates (different files, no dependencies)
- T011: Task routes can be built alongside prompt/provider work
- T013 + T014: MessageList badge and TaskList component (different files)
- T017 + T018: Automated tests and manual testing (independent)

---

## Implementation Strategy

### MVP First (US1+US2 Only)

1. Complete Phase 1: Foundational (models)
2. Complete Phase 2: US1+US2 (task extraction backend)
3. **STOP and VALIDATE**: Send messages, verify tasks extracted and stored
4. If extraction works, proceed to Phase 3

### Incremental Delivery

1. Phase 1 → Models ready → Foundation complete
2. Phase 2 → Backend extraction working → Send message → See tasks in DB (MVP!)
3. Phase 3 → Frontend visible → Dashboard badges + Tasks page (Full feature!)
4. Phase 4 → Polish → Tests pass, constitution compliant

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- US1 and US2 are combined because deadline detection is embedded in the extraction prompt
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
