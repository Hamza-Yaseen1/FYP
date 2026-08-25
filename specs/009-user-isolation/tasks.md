# Tasks: Day 18 – User Isolation

**Input**: Design documents from /specs/009-user-isolation/
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/api.md

**Tests**: YES — user requested comprehensive two-user isolation tests.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: [ID] [P?] [Story] Description

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Database indexes that ALL user stories depend on

- [x] T001 Add MongoDB compound index on messages.user_id and messages.created_at in backend/main.py lifespan
- [x] T002 [P] Add MongoDB compound index on tasks.user_id and tasks.created_at in backend/main.py lifespan

**Checkpoint**: Database indexes ready — all queries will use them efficiently

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Fix the critical analyzer bug that prevents task isolation

> CRITICAL: No user story work can begin until this phase is complete

- [x] T003 Add user_id parameter to analyze_message() in backend/services/ai/analyzer.py
- [x] T004 Include user_id in every task document created by analyze_message() in backend/services/ai/analyzer.py
- [x] T005 Add guard: if user_id is None, log warning and skip task creation in backend/services/ai/analyzer.py
- [x] T006 [P] Pass user_id=str(current_user[_id]) to analyze_message() in backend/routes/messages.py
- [x] T007 [P] Pass user_id=uid to analyze_message() in backend/routes/webhooks.py

**Checkpoint**: Analyzer bug fixed — tasks now carry user_id. Route handlers pass it through.

---

## Phase 3: User Story 1 — Messages Are Private (Priority: P1) MVP

**Goal**: Every message belongs exclusively to the creating user. Cross-user access returns 404.

**Independent Test**: Register two users (A and B). User A creates a message. User A sees it. User B's GET /messages returns zero messages from A. User B's GET /messages/{A_id} returns 404.

**Acceptance Criteria**:
- POST /messages saves with the authenticated user's user_id
- GET /messages returns only the authenticated user's messages
- GET /messages/{id} returns 404 for another user's message
- PUT /messages/{id} returns 404 for another user's message
- DELETE /messages/{id} returns 404 for another user's message

### Implementation for User Story 1

- [x] T008 [US1] Verify POST /messages in backend/routes/messages.py sets user_id from current_user — read create_message() and confirm user_id is from authenticated user not request body
- [x] T009 [US1] Verify GET /messages in backend/routes/messages.py filters on {user_id: uid} — read get_messages() and confirm MongoDB query includes user_id
- [x] T010 [US1] Verify GET /messages/{id} in backend/routes/messages.py includes user_id in query filter — confirm cross-user lookups return 404
- [x] T011 [US1] Verify PUT /messages/{id} in backend/routes/messages.py includes user_id in query filter — confirm cross-user updates are rejected
- [x] T012 [US1] Verify DELETE /messages/{id} in backend/routes/messages.py includes user_id in query filter — confirm cross-user deletes are rejected

**Checkpoint**: Message isolation verified — all message endpoints enforce user_id ownership.

---

## Phase 4: User Story 2 — Tasks Are Private (Priority: P1)

**Goal**: Every task extracted from a message belongs exclusively to the message owner.

**Independent Test**: Register two users (A and B). User A sends a message with actionable content. AI extracts a task. User A sees it on GET /tasks. User B's GET /tasks returns zero tasks from A.

**Acceptance Criteria**:
- AI analyzer creates task documents with user_id
- GET /tasks returns only the authenticated user's tasks
- PUT /tasks/{id}/status returns 404 for another user's task
- DELETE /tasks/{id} returns 404 for another user's task

### Implementation for User Story 2

- [x] T013 [US2] Verify GET /tasks in backend/routes/tasks.py filters on {user_id: uid} — read get_tasks() and confirm MongoDB query includes user_id
- [x] T014 [US2] Verify PUT /tasks/{id}/status in backend/routes/tasks.py includes user_id in query filter — confirm cross-user status updates are rejected
- [x] T015 [US2] Verify DELETE /tasks/{id} in backend/routes/tasks.py includes user_id in query filter — confirm cross-user task deletes are rejected

**Checkpoint**: Task isolation verified — all task endpoints enforce user_id ownership.

---

## Phase 5: User Story 3 — AI Analysis Stays With Owner (Priority: P1)

**Goal**: AI analysis data (priority, summary, recommendation) is never visible to any user other than the message owner.

**Independent Test**: Register two users (A and B). User A sends a message. AI analysis completes. User B calls GET /messages — zero entries. User B calls GET /messages/{A_id} — 404.

**Acceptance Criteria**:
- AI analysis is embedded inside the message document, not a separate collection
- Cross-user message access returns 404 with no analysis data leaked
- AI analysis data is never exposed through task endpoints

### Implementation for User Story 3

- [x] T016 [US3] Verify ai_analysis is embedded inside the message document in backend/services/ai/analyzer.py — confirm the analysis dict is stored on the message not in a separate collection
- [x] T017 [US3] Verify GET /messages response in backend/routes/messages.py does not include ai_analysis from other users — confirm ai_analysis is only returned for authenticated user messages

**Checkpoint**: AI analysis isolation confirmed — analysis data is never leaked across users.

---

## Phase 6: User Story 4 — Webhook Messages Are Scoped to Owner (Priority: P2)

**Goal**: Messages arriving through webhooks are automatically assigned to the authenticating user.

**Independent Test**: User A authenticates a webhook. Message arrives via POST /webhooks/whatsapp. User A sees it. User B's GET /messages returns zero entries from A's webhook.

**Acceptance Criteria**:
- Webhook endpoint sets user_id from the authenticated user's JWT session
- Webhook messages are scoped to the authenticating user
- AI tasks extracted from webhook messages carry the correct user_id

### Implementation for User Story 4

- [x] T018 [US4] Verify POST /webhooks/whatsapp in backend/routes/webhooks.py resolves user_id from authenticated session — confirm uid is set from JWT token not query parameters or headers
- [x] T019 [US4] Verify webhook-processed messages appear only on authenticating user GET /messages — read message creation flow in backend/routes/webhooks.py and confirm user_id is set from session

**Checkpoint**: Webhook isolation verified — incoming messages are scoped to the authenticating user.

---

## Phase 7: User Story 5 — Dashboard Shows Only My Data (Priority: P2)

**Goal**: The frontend dashboard displays only the authenticated user's messages, tasks, and priorities.

**Independent Test**: Register two users with different messages and tasks. Each opens /dashboard. User A sees only A data. User B sees only B data.

**Acceptance Criteria**:
- Dashboard fetches data from authenticated API endpoints
- No cross-user data is cached or rendered in the UI
- Frontend reads data from the user session context only

### Implementation for User Story 5

- [x] T020 [US5] Read dashboard page in app/dashboard/page.tsx — confirm it fetches from authenticated API endpoints rather than directly from the backend
- [x] T021 [US5] Read messages and tasks components — confirm they read from user session context and do not hardcode user IDs or pass user IDs from the URL

**Checkpoint**: Frontend isolation confirmed — dashboard renders only authenticated user data.

---

## Phase 8: User Story 6 — Logout Clears All Cross-User State (Priority: P2)

**Goal**: After logout, all client-side state is cleared before the next user session.

**Independent Test**: User A logs in, views messages, then logs out. User B logs in on same browser. User B dashboard shows zero messages from A.

**Acceptance Criteria**:
- Logout clears the cai_token cookie
- Logout redirects to /login using window.location.replace (full page reload)
- No stale React state survives across login sessions

### Implementation for User Story 6

- [x] T022 [US6] Verify handleLogout in components/Navbar.tsx calls POST /api/auth/logout and uses window.location.replace to /login for a full page reload
- [x] T023 [US6] Verify app/api/auth/logout/route.ts clears the cai_token cookie by setting it with maxAge: 0

**Checkpoint**: Logout isolation verified — browser state is clean between sessions.

---

## Phase 9: Comprehensive Isolation Tests

**Purpose**: End-to-end two-user isolation tests covering ALL endpoints

- [x] T024 Create backend/tests/test_user_isolation.py with TestUserIsolation class that registers two users (User A and User B) and creates sessions for each
- [x] T025 [P] [US1] Test: GET /messages with User A returns only A messages — create messages for both users verify count and content
- [x] T026 [P] [US1] Test: GET /messages with User B returns only B messages — create messages for both users verify count and content
- [x] T027 [P] [US1] Test: GET /messages/{A_id} with User B session returns 404
- [x] T028 [P] [US1] Test: PUT /messages/{A_id} with User B session returns 404 and A message unchanged
- [x] T029 [P] [US1] Test: DELETE /messages/{A_id} with User B session returns 404 and A message still exists
- [x] T030 [P] [US2] Test: GET /tasks with User A returns only A tasks — create tasks via actionable messages for both users
- [x] T031 [P] [US2] Test: GET /tasks with User B returns only B tasks — verify zero A tasks
- [x] T032 [P] [US2] Test: PUT /tasks/{A_task_id} with User B session returns 404 and A task unchanged
- [x] T033 [P] [US2] Test: DELETE /tasks/{A_task_id} with User B session returns 404 and A task still exists
- [x] T034 [P] [US3] Test: Verify AI analysis fields are absent from cross-user message responses
- [x] T035 [P] [US4] Test: POST /webhooks/whatsapp as User A — message appears only on User A GET /messages not on User B
- [x] T036 [P] [US2] Test: Verify task documents in DB have user_id set — query MongoDB directly and confirm no user_id-less tasks exist
- [x] T037 Run all existing tests python -m pytest tests/ -v and verify 27+ tests pass
- [x] T038 Run new isolation tests python -m pytest tests/test_user_isolation.py -v and verify all pass

**Checkpoint**: All isolation tests pass — full two-user separation confirmed.

---

## Phase 10: Polish and Cross-Cutting Concerns

**Purpose**: Final verification and cleanup

- [x] T039 Run quickstart.md validation scenarios manually
- [x] T040 Run frontend tests npx vitest run and verify all pass
- [x] T041 Run npm run build and verify clean build

---

## Dependencies and Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — BLOCKS all user stories
- **Phase 3-8 (User Stories)**: Depend on Phase 2 completion
  - US1, US2, US3 (P1) can proceed sequentially
  - US4, US5, US6 (P2) can proceed after P1 stories
- **Phase 9 (Tests)**: Depends on Phases 1-8
- **Phase 10 (Polish)**: Depends on Phase 9

### Within Each User Story

- Tests first (if included) — ensure they FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- T001 and T002 (indexes) can run in parallel
- T006 and T007 (route handler updates) can run in parallel
- T025-T036 (individual test methods) can all run in parallel
- US4, US5, US6 can proceed in parallel after P1 stories are complete

---

## Implementation Strategy

### MVP First (US1 Only)

1. Complete Phase 1: Setup (indexes)
2. Complete Phase 2: Foundational (analyzer fix + route handlers)
3. Complete Phase 3: User Story 1 (message isolation)
4. STOP and VALIDATE: Test message isolation independently
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Analyzer bug fixed
2. Add US1 → Verify message isolation → Demo
3. Add US2 → Verify task isolation → Demo
4. Add US3-6 → Full isolation coverage
5. Each story adds value without breaking previous stories

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
