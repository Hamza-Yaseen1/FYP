---
id: phr-tasks-001
title: Better Inbox Task Generation
stage: tasks
date: 2026-08-26
surface: cli
model: big-pickle
feature: 011-better-inbox
branch: 011-better-inbox
user: user
command: tasks
labels: [tasks, inbox, filtering, search, fyp]
links:
  spec: specs/011-better-inbox/spec.md
  plan: specs/011-better-inbox/plan.md
  tasks: specs/011-better-inbox/tasks.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/011-better-inbox/tasks.md
tests: []
---

## Prompt

# Day 20 – Better Inbox Tasks

Generate a clear, ordered task list for implementing the approved Day 20 – Better Inbox plan.

Break the work into small, actionable tasks covering:

1. Backend/API support for:

   * Search
   * Source filtering
   * Priority filtering
   * Date filtering
   * Sender filtering
   * Combined filters
   * Current-user isolation

2. Frontend Inbox updates:

   * All, Urgent, Important, Normal, Unread tabs
   * Search input with `Search communications...`
   * Source, Priority, Date, and Sender filters
   * Active filter/reset functionality
   * Loading, empty, and error states

3. Testing:

   * Individual filters
   * Search
   * Combined filters
   * Reset behavior
   * User isolation
   * Existing Inbox functionality

Requirements:

* Follow the approved specification and implementation plan.
* Reuse the existing project structure and components.
* Keep tasks small and independently understandable.
* Order tasks based on dependencies.
* Include the relevant files/components when they can be identified from the existing project.
* Do not add unrelated features.

## Response snapshot

Generated complete task list for Day 20 Better Inbox implementation.

### Task Structure

**Total Tasks**: 53 tasks across 9 phases

**Phase Breakdown**:
- Phase 1 (Setup): 2 tasks
- Phase 2 (Foundational): 6 tasks
- Phase 3 (US1 - Priority Tabs): 7 tasks 🎯 MVP
- Phase 4 (US2 - Source/Priority Filters): 7 tasks
- Phase 5 (US3 - Date/Sender Filters): 5 tasks
- Phase 6 (US4 - Search): 5 tasks
- Phase 7 (US5 - Combined Filtering): 4 tasks
- Phase 8 (US6 - Empty/Loading States): 5 tasks
- Phase 9 (Polish): 12 tasks

**User Stories Covered**:
1. US1: Priority Tab Filtering (P1) - 7 tasks
2. US2: Source and Priority Filtering (P2) - 7 tasks
3. US3: Date and Sender Filtering (P3) - 5 tasks
4. US4: Search Functionality (P4) - 5 tasks
5. US5: Combined Filtering (P5) - 4 tasks
6. US6: Empty and Loading States (P6) - 5 tasks

**Parallel Opportunities**:
- 2 tasks in Setup phase can run in parallel
- 6 tasks in Foundational phase can run in parallel
- US1, US2, US3, US4, US6 can all start in parallel after Foundational
- 2 tasks in US1 can run in parallel
- 1 task in US2 can run in parallel
- 2 tasks in US3 can run in parallel
- 1 task in US4 can run in parallel
- 1 task in US6 can run in parallel

**MVP Scope**: User Story 1 (Priority Tab Filtering) - 7 tasks

**Key Files Identified**:
- `backend/main.py` - MongoDB text index
- `backend/routes/messages.py` - API endpoints
- `backend/tests/test_messages.py` - Backend tests
- `components/InboxTabs.tsx` - Priority tabs
- `components/FilterBar.tsx` - Filter controls
- `components/SearchBar.tsx` - Search input
- `components/EmptyState.tsx` - Empty state
- `components/LoadingSkeleton.tsx` - Loading state
- `app/(dashboard)/inbox/page.tsx` - Inbox page
- `components/__tests__/*.test.tsx` - Frontend tests
- `app/(dashboard)/inbox/__tests__/page.test.tsx` - Integration tests

### Task Format Validation

All tasks follow the required format:
- ✅ Checkbox: `- [ ]`
- ✅ Task ID: T001, T002, etc.
- ✅ [P] marker for parallelizable tasks
- ✅ [Story] label for user story tasks (US1-US6)
- ✅ Description with exact file paths

## Outcome

- Impact: Complete task list for Day 20 Better Inbox implementation
- Tests: Backend API tests and frontend component tests included
- Files: specs/011-better-inbox/tasks.md
- Next prompts: Implementation can begin with Phase 1 (Setup)
- Reflection: Tasks organized by user story for independent implementation and testing

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results: N/A
- Prompt variant: N/A
- Next experiment: N/A