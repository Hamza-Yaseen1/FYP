---
description: "Task list for Communication AI Baseline implementation"
---

# Tasks: Communication AI Baseline

**Input**: Design documents from `/specs/1-baseline-spec/`
**Prerequisites**: plan.md (✅), spec.md (✅), research.md (✅), data-model.md (✅), contracts/ (✅)

**Tests**: Tests are OPTIONAL - only included if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/` for API, `app/` for Next.js frontend
- Tasks reference actual project structure

---

## Phase 1: Setup (Shared Infrastructure) ✅ COMPLETED

**Purpose**: Project initialization and basic structure

- [x] T001 Create project structure (backend/ and app/ directories)
- [x] T002 Initialize Python FastAPI project with dependencies
- [x] T003 [P] Initialize Next.js frontend with TypeScript
- [x] T004 [P] Configure MongoDB connection in backend/database.py
- [x] T005 [P] Configure shadcn/ui and Tailwind CSS

**Status**: ✅ Complete - Basic infrastructure exists

---

## Phase 2: Foundational (Blocking Prerequisites) ✅ COMPLETED

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 Setup MongoDB collections (messages, users, ai_analysis, tasks, connections)
- [x] T007 [P] Create Message model in backend/models/message.py
- [x] T008 [P] Create message routes in backend/routes/messages.py
- [x] T009 [P] Create webhook routes in backend/routes/webhooks.py
- [x] T010 Configure CORS middleware in backend/main.py
- [x] T011 Setup environment configuration (.env with MONGO_URI, DB_NAME)
- [x] T012 [P] Create AI provider abstraction in backend/services/ai/providers/base.py
- [x] T013 [P] Implement OpenAI provider in backend/services/ai/providers/openai.py
- [x] T014 Create AI analyzer in backend/services/ai/analyzer.py

**Checkpoint**: ✅ Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - View Message Dashboard (Priority: P1) 🎯 MVP

**Goal**: Display all user messages in a chronological dashboard view

**Independent Test**: Send simulated message → Verify it appears on dashboard with sender, content, timestamp, and source

### Implementation for User Story 1

- [x] T015 [P] [US1] Create dashboard page in app/(dashboard)/dashboard/page.tsx
- [x] T016 [P] [US1] Create MessageList component in components/MessageList.tsx
- [x] T017 [US1] Implement GET /messages endpoint to fetch all messages
- [x] T018 [US1] Add auto-poll refresh mechanism (10 second interval) in MessageList
- [x] T019 [US1] Display empty state when no messages exist
- [x] T020 [US1] Add source badge styling for WhatsApp/Gmail

**Checkpoint**: ✅ At this point, User Story 1 is fully functional - messages appear on dashboard

---

## Phase 4: User Story 2 - Simulate Incoming Messages (Priority: P1) 🎯 MVP

**Goal**: Accept simulated messages from different channels via API

**Independent Test**: Submit simulated message via form → Verify it appears in database and on dashboard

### Implementation for User Story 2

- [x] T021 [P] [US2] Create WhatsApp webhook endpoint in backend/routes/webhooks.py
- [x] T022 [P] [US2] Create SimulateMessage form component in components/SimulateMessage.tsx
- [x] T023 [US2] Integrate SimulateMessage form with dashboard page
- [x] T024 [US2] Add channel attribution (WhatsApp, Gmail) to messages
- [x] T025 [US2] Test simulation with multiple messages in sequence

**Checkpoint**: ✅ At this point, User Stories 1 AND 2 work together - simulate and view flow complete

---

## Phase 5: User Story 3 - AI Priority Classification (Priority: P2) 🔄 IN PROGRESS

**Goal**: Automatically classify messages into priority levels (Urgent, Important, Normal, Low)

**Independent Test**: Send message with deadline → Verify priority is assigned and displayed

### Implementation for User Story 3

- [x] T026 [P] [US3] Create priority classification prompt in backend/services/ai/prompts/priority.txt
- [x] T027 [US3] Update analyzer to use priority prompt
- [x] T028 [US3] Integrate AI analysis in POST /messages endpoint
- [x] T029 [US3] Integrate AI analysis in webhook endpoint
- [ ] T030 [US3] Add priority badge to MessageCard component
- [ ] T031 [US3] Add priority color indicators (red, yellow, green, gray)
- [ ] T032 [US3] Display confidence level with "Needs review" flag for low confidence (<0.7)
- [ ] T033 [US3] Test with various message types (urgent deadline, casual, automated)

**Checkpoint**: At this point, messages are automatically prioritized with visible indicators

---

## Phase 6: User Story 4 - AI Task Extraction (Priority: P2)

**Goal**: Extract actionable tasks from messages with deadlines

**Independent Test**: Send message "Please send report by Friday" → Verify task is extracted with deadline

### Implementation for User Story 4

- [x] T034 [P] [US4] Create task extraction prompt in backend/services/ai/prompts/tasks.txt
- [ ] T035 [P] [US4] Create Task model in backend/models/task.py
- [ ] T036 [US4] Implement task extraction in AI analyzer
- [ ] T037 [US4] Create task routes in backend/routes/tasks.py (GET, PUT, DELETE)
- [ ] T038 [US4] Store extracted tasks in tasks_collection with message reference
- [ ] T039 [P] [US4] Create TaskList component in components/TaskList.tsx
- [ ] T040 [US4] Add task display to dashboard with status, deadline, source message link
- [ ] T041 [US4] Implement mark task as complete functionality
- [ ] T042 [US4] Add task deletion functionality
- [ ] T043 [US4] Test with messages containing clear vs. unclear action items

**Checkpoint**: At this point, tasks are automatically extracted and manageable

---

## Phase 7: User Story 5 - AI Message Summary (Priority: P3)

**Goal**: Generate concise summaries for long messages

**Independent Test**: Send 500+ character message → Verify summary appears (under 100 words)

### Implementation for User Story 5

- [x] T044 [P] [US5] Create summary generation prompt in backend/services/ai/prompts/summary.txt
- [ ] T045 [US5] Implement summary generation in AI analyzer (only for messages >200 chars)
- [ ] T046 [US5] Update MessageCard to show summary with expand/collapse
- [ ] T047 [US5] Add "Read more" functionality for full message view
- [ ] T048 [US5] Test with messages of varying lengths (short, medium, long)

**Checkpoint**: At this point, long messages show helpful summaries

---

## Phase 8: User Story 6 - Recommended Actions (Priority: P3)

**Goal**: Suggest appropriate next actions for each message

**Independent Test**: Send meeting request → Verify "Schedule" action is suggested

### Implementation for User Story 6

- [x] T049 [P] [US6] Create recommended actions prompt in backend/services/ai/prompts/actions.txt
- [ ] T050 [US6] Implement action recommendation in AI analyzer
- [ ] T051 [US6] Update MessageCard to show recommended action buttons
- [ ] T052 [US6] Style actions as suggestion chips (not primary CTAs)
- [ ] T053 [US6] Test with different message types (request, meeting, FYI, question)

**Checkpoint**: At this point, messages show helpful action suggestions

---

## Phase 9: User Story 7 - Task Management (Priority: P3)

**Goal**: View, complete, and manage extracted tasks

**Independent Test**: Extract task → Mark complete → Verify status updates and moves to completed section

### Implementation for User Story 7

- [ ] T054 [US7] Add task status field (pending/completed) to Task model
- [ ] T055 [US7] Implement PUT /tasks/{id} endpoint for status updates
- [ ] T056 [US7] Add task edit functionality (description, deadline)
- [ ] T057 [US7] Implement DELETE /tasks/{id} endpoint
- [ ] T058 [US7] Create completed tasks section in TaskList component
- [ ] T059 [US7] Add filter/sort options (by deadline, by priority)
- [ ] T060 [US7] Test full task lifecycle (create → edit → complete → delete)

**Checkpoint**: At this point, full task management workflow is complete

---

## Phase 10: User Story 8 - User Authentication (Priority: P4) 🔜 FUTURE

**Goal**: Isolate user data with authentication

**Independent Test**: Create account → Login → Verify only user's own messages visible

### Implementation for User Story 8 (DEFERRED - Single user dev mode sufficient for FYP)

- [ ] T061 [P] [US8] Create User model with password hashing
- [ ] T062 [P] [US8] Implement JWT authentication in backend
- [ ] T063 [US8] Create registration endpoint
- [ ] T064 [US8] Create login endpoint
- [ ] T065 [US8] Add authentication middleware to protected routes
- [ ] T066 [P] [US8] Create login page in frontend
- [ ] T067 [P] [US8] Create registration page in frontend
- [ ] T068 [US8] Add user_id to all message queries for data isolation
- [ ] T069 [US8] Test with multiple users

**Checkpoint**: At this point, multi-user support is complete

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T070 [P] Update dashboard summary cards to use real AI analysis data
- [ ] T071 [P] Update "Needs Your Attention" section to show real urgent/important messages
- [ ] T072 [P] Add AI status indicator component (analyzing/completed/failed)
- [ ] T073 Add error handling for AI service unavailability
- [ ] T074 Add fallback UI for when AI analysis fails
- [ ] T075 [P] Add loading states for AI analysis in progress
- [ ] T076 Implement graceful degradation when LLM API is down
- [ ] T077 [P] Add confidence level display for all AI outputs
- [ ] T078 Documentation: Update quickstart.md with OpenAI API key setup
- [ ] T079 Code cleanup and refactoring
- [ ] T080 Performance optimization: Add caching for AI analysis
- [ ] T081 Security: Validate all environment variables on startup
- [ ] T082 Run full integration test suite

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: ✅ Complete - No dependencies
- **Foundational (Phase 2)**: ✅ Complete - Depends on Setup
- **User Stories (Phase 3-10)**: All depend on Foundational phase completion
  - US1 & US2: ✅ Complete (MVP ready)
  - US3: 🔄 In Progress (AI integration active)
  - US4-8: 🔜 Ready to start in parallel or sequentially

### Current Status

**✅ COMPLETED:**
- Phase 1: Setup
- Phase 2: Foundation
- Phase 3: User Story 1 - Dashboard
- Phase 4: User Story 2 - Simulation
- Partial Phase 5: AI Infrastructure

**🔄 IN PROGRESS:**
- Phase 5: User Story 3 - AI Priority Classification (backend done, frontend pending)

**🔜 NEXT UP:**
- Complete US3 frontend (T030-T033)
- Start US4: Task Extraction (T035-T043)
- Start US5: Summaries (T045-T048)

### Parallel Opportunities

Once US3 frontend is complete:
- US4 (Task Extraction) can be built independently
- US5 (Summaries) can be built independently
- US6 (Actions) can be built independently
- All can proceed in parallel if desired

---

## Implementation Strategy

### MVP Status (Current) ✅

1. ✅ Setup complete
2. ✅ Foundational infrastructure complete
3. ✅ User Story 1 (Dashboard) complete
4. ✅ User Story 2 (Simulation) complete
5. 🔄 User Story 3 (AI Priority) - Backend complete, frontend pending

**CURRENT MVP**: Users can simulate messages, see them on dashboard, and AI analyzes them in the background.

### Next Milestone: AI-Enhanced Dashboard

**Goal**: Complete US3 frontend + dashboard polish
**Tasks**: T030-T033, T070-T072
**Outcome**: Full AI priority classification visible on dashboard

### Future Milestones

- **Milestone 2**: Task extraction and management (US4 + US7)
- **Milestone 3**: Enhanced AI features (US5 + US6)
- **Milestone 4**: Multi-user support (US8)

---

## Notes

- [P] tasks = different files, no dependencies, can run in parallel
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- ✅ Completed tasks marked with [x]
- 🔄 Current focus: Complete AI integration frontend
- 🔜 Next priority: Task extraction (high value for FYP demo)
