# Tasks: Task Management

**Input**: Design documents from `/specs/012-task-management/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Not explicitly requested - omitted per task generation rules.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- Paths shown below assume web app structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No setup tasks needed - project already exists with authentication and user isolation.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T001 Update TaskResponse model to include snoozed_until field in backend/models/task.py
- [X] T002 Add MongoDB index for priority-based sorting in backend/routes/tasks.py
- [X] T003 [P] Create base TaskCard component in frontend/src/components/tasks/TaskCard.tsx
- [X] T004 [P] Create TaskList component in frontend/src/components/tasks/TaskList.tsx
- [X] T005 [P] Create priority mapping utility in frontend/src/lib/priority.ts

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - View My Tasks (Priority: P1) 🎯 MVP

**Goal**: Display all extracted tasks for the logged-in user with priority indicators and deadlines

**Independent Test**: Log in and verify the tasks page shows only current user's tasks with correct priority indicators and deadlines

### Implementation for User Story 1

- [X] T006 [US1] Extend GET /tasks endpoint with priority sorting in backend/routes/tasks.py
- [X] T007 [US1] Create tasks page route in frontend/src/app/(dashboard)/tasks/page.tsx
- [X] T008 [US1] Implement TaskList component with priority sorting in frontend/src/components/tasks/TaskList.tsx
- [X] T009 [US1] Implement TaskCard component with priority indicator display in frontend/src/components/tasks/TaskCard.tsx
- [X] T010 [US1] Add empty state "No tasks found" message in frontend/src/components/tasks/TaskList.tsx
- [X] T011 [US1] Add loading skeleton state in frontend/src/components/tasks/TaskList.tsx
- [X] T012 [US1] Test user isolation - verify only own tasks are displayed
- [X] T013 [US1] Test priority sorting - urgent first, then important, then normal
- [X] T014 [US1] Test responsive design on mobile and desktop widths

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Complete a Task (Priority: P2)

**Goal**: Allow users to mark tasks as complete, removing them from the active list

**Independent Test**: Mark a task as complete and verify it disappears from the active list

### Implementation for User Story 2

- [X] T015 [P] [US2] Add Complete button to TaskCard component in frontend/src/components/tasks/TaskCard.tsx
- [X] T016 [US2] Implement completeTask function in frontend/src/services/taskService.ts
- [X] T017 [US2] Add visual confirmation when task is completed in frontend/src/components/tasks/TaskCard.tsx
- [X] T018 [US2] Test complete action - task disappears from active list
- [X] T019 [US2] Test visual confirmation appears after completion
- [X] T020 [US2] Test refresh - completed task remains hidden

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Snooze a Task (Priority: P3)

**Goal**: Allow users to snooze tasks for defined periods (1 hour, tomorrow, next week)

**Independent Test**: Snooze a task and verify it disappears temporarily, then reappears after snooze period

### Implementation for User Story 3

- [X] T021 [US3] Create PUT /tasks/{task_id}/snooze endpoint in backend/routes/tasks.py
- [X] T022 [US3] Implement snooze duration calculation in backend/routes/tasks.py
- [X] T023 [P] [US3] Add Snooze dropdown to TaskCard component in frontend/src/components/tasks/TaskCard.tsx
- [X] T024 [US3] Implement snoozeTask function in frontend/src/services/taskService.ts
- [X] T025 [US3] Test snooze action - task disappears from active list
- [X] T026 [US3] Test snooze expiration - task reappears after duration
- [X] T027 [US3] Test different snooze durations (1 hour, tomorrow, next week)

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently

---

## Phase 6: User Story 4 - View Original Message (Priority: P4)

**Goal**: Allow users to view the original message that created a task

**Independent Test**: Click "View message" and verify the original message is displayed

### Implementation for User Story 4

- [X] T028 [US4] Create GET /tasks/{task_id}/message endpoint in backend/routes/tasks.py
- [X] T029 [US4] Implement getMessageForTask function in backend/routes/tasks.py
- [X] T030 [P] [US4] Add View Message button to TaskCard component in frontend/src/components/tasks/TaskCard.tsx
- [X] T031 [US4] Implement viewMessage function in frontend/src/services/taskService.ts
- [X] T032 [US4] Test view message action - navigates to message detail
- [X] T033 [US4] Test return navigation - can return to tasks list
- [X] T034 [US4] Test missing message handling - graceful error when message deleted

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T035 [P] Add keyboard navigation for task actions in frontend/src/components/tasks/TaskCard.tsx
- [X] T036 [P] Add accessibility labels for task actions in frontend/src/components/tasks/TaskCard.tsx
- [X] T037 Performance optimization - ensure task list loads in <1 second
- [X] T038 Security audit - verify user isolation for all task actions
- [X] T039 Run quickstart.md validation checklist
- [X] T040 Code cleanup and refactoring

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately (but no tasks needed)
- **Foundational (Phase 2)**: No dependencies - can start immediately
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3 → P4)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - May integrate with US1/US2/US3 but should be independently testable

### Within Each User Story

- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all models for User Story 1 together:
Task: "Update TaskResponse model in backend/models/task.py"
Task: "Add MongoDB index in backend/routes/tasks.py"

# Launch all frontend components for User Story 1 together:
Task: "Create tasks page route in frontend/src/app/(dashboard)/tasks/page.tsx"
Task: "Implement TaskList component in frontend/src/components/tasks/TaskList.tsx"
Task: "Implement TaskCard component in frontend/src/components/tasks/TaskCard.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (no tasks needed)
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
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
   - Developer D: User Story 4
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence