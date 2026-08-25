---

description: "Task list for Better Inbox implementation"
---

# Tasks: Better Inbox

**Input**: Design documents from `/specs/011-better-inbox/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Backend API tests and frontend component tests are included as they are critical for verifying filtering, search, and user isolation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/`, `frontend/` (existing project structure)
- Paths follow existing project conventions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add MongoDB text index and ensure backend can support filtering

- [x] T001 [P] Add MongoDB text index on sender, content, and ai_analysis.summary fields in backend/main.py
- [x] T002 [P] Create backend/tests/test_messages.py file with basic test structure

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Backend API endpoints that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 Extend GET /messages endpoint with query parameters (tab, source, priority, start_date, end_date, sender, search, limit, offset) in backend/routes/messages.py
- [x] T004 Add GET /messages/counts endpoint for filter counts in backend/routes/messages.py
- [x] T005 Add GET /messages/senders endpoint for unique senders in backend/routes/messages.py
- [x] T006 Add GET /messages/sources endpoint for unique sources in backend/routes/messages.py
- [x] T007 Add backend API tests for GET /messages with each filter parameter in backend/tests/test_messages.py
- [x] T008 Add backend API tests for user isolation (User A cannot see User B's messages) in backend/tests/test_messages.py

**Checkpoint**: Backend API ready - frontend implementation can now begin

---

## Phase 3: User Story 1 - Priority Tab Filtering (Priority: P1) 🎯 MVP

**Goal**: Users can filter messages by priority tabs (All, Urgent, Important, Normal, Unread)

**Independent Test**: Click each tab and verify only matching messages appear. Can be fully tested independently.

### Implementation for User Story 1

- [x] T009 [P] [US1] Create InboxTabs component in components/InboxTabs.tsx
- [x] T010 [P] [US1] Create EmptyState component in components/EmptyState.tsx
- [x] T011 [US1] Update inbox page to use InboxTabs component in app/(dashboard)/inbox/page.tsx
- [x] T012 [US1] Add tab filter state management to inbox page in app/(dashboard)/inbox/page.tsx
- [x] T013 [US1] Fetch messages with tab filter from backend in app/(dashboard)/inbox/page.tsx
- [x] T014 [US1] Display loading state while messages load in app/(dashboard)/inbox/page.tsx
- [x] T015 [US1] Display empty state when no messages match tab in app/(dashboard)/inbox/page.tsx

**Checkpoint**: Priority tabs fully functional - users can switch between All, Urgent, Important, Normal, Unread

---

## Phase 4: User Story 2 - Source and Priority Filtering (Priority: P2)

**Goal**: Users can filter messages by source (WhatsApp, Gmail, etc.) and priority using dropdown filters

**Independent Test**: Select source/priority filters and verify only matching messages appear. Can be tested independently after US1.

### Implementation for User Story 2

- [x] T016 [P] [US2] Create FilterBar component in components/FilterBar.tsx
- [x] T017 [US2] Add source filter to FilterBar component in components/FilterBar.tsx
- [x] T018 [US2] Add priority filter to FilterBar component in components/FilterBar.tsx
- [x] T019 [US2] Update inbox page to use FilterBar component in app/(dashboard)/inbox/page.tsx
- [x] T020 [US2] Add source/priority filter state management to inbox page in app/(dashboard)/inbox/page.tsx
- [x] T021 [US2] Fetch messages with source/priority filters from backend in app/(dashboard)/inbox/page.tsx
- [x] T022 [US2] Add clear source/priority filter functionality in app/(dashboard)/inbox/page.tsx

**Checkpoint**: Source and priority filters fully functional - users can filter by communication channel and priority level

---

## Phase 5: User Story 3 - Date and Sender Filtering (Priority: P3)

**Goal**: Users can filter messages by date range and by sender

**Independent Test**: Select date range and sender filters and verify only matching messages appear. Can be tested independently after US1.

### Implementation for User Story 3

- [x] T023 [P] [US3] Add date range filter to FilterBar component in components/FilterBar.tsx
- [x] T024 [P] [US3] Add sender filter to FilterBar component in components/FilterBar.tsx
- [x] T025 [US3] Add date/sender filter state management to inbox page in app/(dashboard)/inbox/page.tsx
- [x] T026 [US3] Fetch messages with date/sender filters from backend in app/(dashboard)/inbox/page.tsx
- [x] T027 [US3] Add clear date/sender filter functionality in app/(dashboard)/inbox/page.tsx

**Checkpoint**: Date and sender filters fully functional - users can filter by time period and contact

---

## Phase 6: User Story 4 - Search Functionality (Priority: P4)

**Goal**: Users can search for messages using a search bar

**Independent Test**: Enter search terms and verify matching messages appear. Can be tested independently after US1.

### Implementation for User Story 4

- [x] T028 [P] [US4] Create SearchBar component in components/SearchBar.tsx
- [x] T029 [US4] Add search state management to inbox page in app/(dashboard)/inbox/page.tsx
- [x] T030 [US4] Fetch messages with search query from backend in app/(dashboard)/inbox/page.tsx
- [x] T031 [US4] Add debounced search (300ms delay) in components/SearchBar.tsx
- [x] T032 [US4] Add clear search functionality in components/SearchBar.tsx

**Checkpoint**: Search functionality fully functional - users can find messages by keywords

---

## Phase 7: User Story 5 - Combined Filtering (Priority: P5)

**Goal**: Users can combine multiple filters (tabs, source, priority, date, sender, search)

**Independent Test**: Apply multiple filters simultaneously and verify only messages matching all criteria appear. Can be tested independently after US1-US4.

### Implementation for User Story 5

- [x] T033 [US5] Add combined filter state management to inbox page in app/(dashboard)/inbox/page.tsx
- [x] T034 [US5] Fetch messages with all combined filters from backend in app/(dashboard)/inbox/page.tsx
- [x] T035 [US5] Add "Clear All" button to reset all filters and search in app/(dashboard)/inbox/page.tsx
- [x] T036 [US5] Add filter count badges to InboxTabs component in components/InboxTabs.tsx

**Checkpoint**: Combined filtering fully functional - users can apply multiple filters together

---

## Phase 8: User Story 6 - Empty and Loading States (Priority: P6)

**Goal**: Users see appropriate loading states while messages are fetched and clear empty states when no messages match

**Independent Test**: Observe interface during loading and when no results match. Can be tested independently after US1.

### Implementation for User Story 6

- [x] T037 [P] [US6] Add loading skeleton component in components/LoadingSkeleton.tsx
- [x] T038 [US6] Add loading state to inbox page while messages load in app/(dashboard)/inbox/page.tsx
- [x] T039 [US6] Add error state handling for API failures in app/(dashboard)/inbox/page.tsx
- [x] T040 [US6] Add empty state when no messages match filters in app/(dashboard)/inbox/page.tsx
- [x] T041 [US6] Add "Clear all filters" link in empty state component in components/EmptyState.tsx

**Checkpoint**: Loading, empty, and error states fully functional - users understand system state at all times

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final testing, optimization, and cleanup

- [x] T042 Add backend API tests for combined filters in backend/tests/test_messages.py
- [x] T043 Add backend API tests for search functionality in backend/tests/test_messages.py
- [x] T044 Add backend API tests for date range filtering in backend/tests/test_messages.py
- [x] T045 Add frontend component tests for InboxTabs in components/__tests__/InboxTabs.test.tsx
- [x] T046 Add frontend component tests for FilterBar in components/__tests__/FilterBar.test.tsx
- [x] T047 Add frontend component tests for SearchBar in components/__tests__/SearchBar.test.tsx
- [x] T048 Add frontend component tests for EmptyState in components/__tests__/EmptyState.test.tsx
- [x] T049 Add integration tests for inbox page in app/(dashboard)/inbox/__tests__/page.test.tsx
- [ ] T050 Run manual testing of all filters and search
- [ ] T051 Verify user isolation with combined filters
- [ ] T052 Test performance with large number of messages
- [ ] T053 Clean up any unused code or components

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-8)**: All depend on Foundational phase completion
  - User Story 1 (P1) should be completed first as it's the MVP
  - User Stories 2-4 can proceed in parallel after US1
  - User Story 5 depends on US1-US4 (combined filtering)
  - User Story 6 can proceed in parallel with US2-US5
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 5 (P5)**: Depends on US1-US4 (needs all filters implemented for combined testing)
- **User Story 6 (P6)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable

### Within Each User Story

- Components before page integration
- State management before API calls
- Individual filters before combined filters
- Core implementation before testing

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks can run in parallel (within Phase 2)
- Once Foundational phase completes:
  - US1, US2, US3, US4, US6 can all start in parallel
  - US5 must wait for US1-US4
- Within each user story, tasks marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tasks for User Story 1 together:
Task: "Create InboxTabs component in components/InboxTabs.tsx"
Task: "Create EmptyState component in components/EmptyState.tsx"

# Then sequential tasks:
Task: "Update inbox page to use InboxTabs component"
Task: "Add tab filter state management"
Task: "Fetch messages with tab filter"
Task: "Display loading state"
Task: "Display empty state"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add User Story 4 → Test independently → Deploy/Demo
6. Add User Story 5 → Test independently → Deploy/Demo
7. Add User Story 6 → Test independently → Deploy/Demo
8. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Priority Tabs)
   - Developer B: User Story 2 (Source/Priority Filters)
   - Developer C: User Story 3 (Date/Sender Filters)
   - Developer D: User Story 4 (Search)
   - Developer E: User Story 6 (Loading/Empty States)
3. After US1-US4 complete, Developer A works on User Story 5 (Combined Filtering)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests pass before implementing (TDD approach)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- All filtering and search MUST be backend-side (FR-020 compliance)
- User isolation MUST be maintained at query level for all filters