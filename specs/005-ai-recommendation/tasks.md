---
description: "Task list for AI Recommended Action feature (Day 13)"
---

# Tasks: AI Recommended Action

**Input**: Design documents from `/specs/005-ai-recommendation/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: No automated tests requested — manual testing only.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Foundational (Data Model Update)

**Purpose**: Extend the AIAnalysis model to include the new `recommended_action` field. This MUST be complete before any user story work.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T001 Add `recommended_action: str = ""` field to `AIAnalysis` Pydantic model in `backend/models/message.py`

**Checkpoint**: Model updated — backend can now serialize/deserialize the new field

---

## Phase 2: User Story 1 - Core Recommendation (Priority: P1) 🎯 MVP

**Goal**: Generate a single recommended action for each analyzed message and display it on the dashboard.

**Independent Test**: Send a test message with a clear action request (e.g., "Please send the report before 5 PM") and verify the recommended action appears on the dashboard below the summary.

### Implementation for User Story 1

- [x] T002 Rewrite `backend/services/ai/prompts/actions.txt` with a prompt that generates a single `recommended_action` string (verb-first, under 15 words, default to "Review this message")
- [x] T003 Add `generate_recommendation(message: str) -> str` async method to `GroqProvider` in `backend/services/ai/providers/groq.py` (load actions.txt, call Groq API, parse JSON response, return string, fallback to "" on error)
- [x] T004 Update `analyze_message()` in `backend/services/ai/analyzer.py` to call `provider.generate_recommendation(content)` after summary generation and add result to analysis dict as `recommended_action`
- [x] T005 Update `MessageList.tsx` in `components/MessageList.tsx` to display `recommended_action` as an italic line below the summary (only render if non-empty, style with distinct color)

**Checkpoint**: At this point, User Story 1 should be fully functional — messages get recommendations and dashboard displays them

---

## Phase 3: User Story 2 - Language Matching (Priority: P2)

**Goal**: Ensure the recommended action is always in the same language as the original message.

**Independent Test**: Send a message in Arabic and verify the recommended action is in Arabic. Send a message in English and verify it's in English.

### Implementation for User Story 2

- [x] T006 Update `actions.txt` prompt in `backend/services/ai/prompts/actions.txt` to explicitly instruct the AI to return the recommendation in the same language as the message content

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Deadline Context (Priority: P3)

**Goal**: Reference deadlines in the recommended action when the message includes time context.

**Independent Test**: Send a message with a deadline (e.g., "Send the report before Friday") and verify the recommendation references the deadline. Send a message without a deadline and verify the recommendation focuses on the action only.

### Implementation for User Story 3

- [x] T007 Update `actions.txt` prompt in `backend/services/ai/prompts/actions.txt` to instruct the AI to reference deadlines when present in the message (e.g., "Submit the form before Friday")

**Checkpoint**: All user stories should now be independently functional

---

## Phase 5: Polish & Manual Testing

**Purpose**: Validate the feature end-to-end and ensure code quality

- [x] T008 Send test message "Please send the report before 5 PM" via `POST /webhooks/whatsapp` and verify response includes `recommended_action` field
- [x] T009 Send informational message "The meeting is at 3 PM tomorrow" and verify `recommended_action` is "Review this message"
- [x] T010 Open dashboard at `http://localhost:3000/dashboard` and verify recommended action displays below summary for new messages
- [x] T011 Verify old messages (without `recommended_action`) still display correctly on dashboard
- [x] T012 Verify graceful fallback — if Groq API fails, message still displays with empty recommended action
- [x] T013 Review all modified files for code quality (PEP 8, ESLint conventions)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 1)**: No dependencies — can start immediately
- **User Story 1 (Phase 2)**: Depends on Phase 1 completion — BLOCKS all other stories
- **User Story 2 (Phase 3)**: Depends on Phase 1 completion — can run in parallel with US1
- **User Story 3 (Phase 4)**: Depends on Phase 1 completion — can run in parallel with US1/US2
- **Polish (Phase 5)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 1 — No dependencies on other stories
- **User Story 2 (P2)**: Can start after Phase 1 — Independent of US1 (prompt refinement only)
- **User Story 3 (P3)**: Can start after Phase 1 — Independent of US1/US2 (prompt refinement only)

### Within Each User Story

- Models before services
- Services before endpoints/UI
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Foundational tasks marked [P] can run in parallel
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- T002, T003 can run in parallel (different files)
- T006, T007 can run in parallel (both update actions.txt but different sections)

---

## Parallel Example: User Story 1

```bash
# Launch prompt and provider tasks together (different files):
Task: "T002 Rewrite actions.txt prompt"
Task: "T003 Add generate_recommendation() to GroqProvider"

# Then sequentially:
Task: "T004 Update analyzer.py to call recommendation"
Task: "T005 Update MessageList.tsx to display recommendation"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Foundational (model update)
2. Complete Phase 2: User Story 1 (core recommendation)
3. **STOP and VALIDATE**: Test by sending a message and checking dashboard
4. Deploy/demo if ready

### Incremental Delivery

1. Complete Foundational → Model ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test language matching → Deploy/Demo
4. Add User Story 3 → Test deadline context → Deploy/Demo
5. Each story adds value without breaking previous stories

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- All prompt changes (T002, T006, T007) target the same file `actions.txt` — coordinate to avoid merge conflicts
