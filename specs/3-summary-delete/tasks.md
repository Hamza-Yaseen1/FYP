# Tasks: Summary Agent & Delete Message

**Feature Branch**: `3-summary-delete` | **Date**: 2026-08-20
**Spec**: `specs/3-summary-delete/spec.md` | **Plan**: `specs/3-summary-delete/plan.md`

## User Stories

| ID | User Story | Priority | Status |
|----|------------|----------|--------|
| US1 | Automatic Summary Generation | P1 | Pending |
| US2 | Delete Message | P2 | Pending |
| US3 | Summary Display | P3 | Pending |

---

## Phase 1: Foundational Tasks

Tasks that must complete before user stories.

- [X] T001 Update AIAnalysis model to include summary field in `backend/models/message.py`
  - Add `summary: Optional[str] = None` to AIAnalysis class

- [X] T002 Verify AIAnalysis model works with new summary field by importing and creating test instance

---

## Phase 2: User Story 1 - Summary Generation (P1)

**Goal**: Generate a short, clear summary of the message.
**Independent Test**: Send a message, verify summary is generated and stored.

- [X] T003 [US1] Create summary prompt template at `backend/services/ai/prompts/summary.txt`
  - Prompt should request 1-2 sentence summary under 30 words
  - Include rules: preserve action items, never invent information, remove greetings

- [ ] T004 [US1] Test prompt with a sample message to verify output quality
  - Use a sample message like: "Hey bro, just wanted to remind you that the teacher said we have to submit the final documentation before tomorrow's meeting."
  - Expected output: "Final documentation must be submitted before tomorrow's meeting."

- [X] T005 [US1] Update GroqProvider in `backend/services/ai/providers/groq.py` to add summary method
  - Add `generate_summary(message_content: str) -> Optional[str]` method
  - Use summary.txt prompt template
  - Return null on failure

- [X] T006 [US1] Test GroqProvider summary method with a sample message
  - Verify it returns a string summary
  - Verify it returns null on error

- [X] T007 [US1] Update analyzer in `backend/services/ai/analyzer.py` to generate summary after priority
  - Call summary method after priority classification
  - Store summary in ai_analysis field
  - Handle failure gracefully (set summary to null)

- [X] T008 [US1] Test full flow: POST message → verify summary in response
  - Send message via POST /messages
  - Verify response contains ai_analysis.summary

- [X] T009 [US1] Verify summary is stored in MongoDB
  - Check database directly or via GET /messages
  - Verify ai_analysis.summary field exists

---

## Phase 3: User Story 2 - Delete Message (P2)

**Goal**: Allow users to permanently delete messages from the dashboard.
**Independent Test**: Delete a message, verify it is removed from MongoDB.

- [X] T010 [US2] Add DELETE /messages/{id} endpoint in `backend/routes/messages.py`
  - Remove message from MongoDB by ID
  - Return 204 No Content on success
  - Return 404 if message not found

- [X] T011 [US2] Test DELETE endpoint with valid message ID
  - Create a message, then delete it
  - Verify 204 response
  - Verify message is gone from database

- [X] T012 [US2] Test DELETE endpoint with invalid message ID
  - Use a non-existent ID
  - Verify 404 response

- [X] T013 [US2] Add delete button to MessageList component in `components/MessageList.tsx`
  - Add trash icon button on each message card
  - Style it red or subtle to match UI

- [X] T014 [US2] Add confirmation dialog when delete button is clicked
  - Show "Are you sure you want to delete this message?" dialog
  - Include Confirm and Cancel buttons

- [X] T015 [US2] Implement delete handler in MessageList component
  - On confirm: call DELETE /messages/{id}
  - On success: remove message from local state
  - On error: show error message

- [X] T016 [US2] Test delete flow in browser
  - Click delete button
  - Verify confirmation appears
  - Confirm deletion
  - Verify message disappears from list

- [X] T017 [US2] Test delete flow with network error
  - Simulate network error (disconnect or block request)
  - Verify error message is shown
  - Verify message remains in list

---

## Phase 4: User Story 3 - Summary Display (P3)

**Goal**: Show summaries on the dashboard under each message.
**Independent Test**: View dashboard, verify summaries are displayed.

- [X] T018 [US3] Update Message interface in `components/MessageList.tsx` to include summary field
  - Add `summary?: string` to Message type

- [X] T019 [US3] Add summary display below message content in MessageList component
  - Show summary in gray text below main content
  - Only show if summary is not null

- [X] T020 [US3] Style summary text to be visually distinct from main content
  - Use smaller font size
  - Use lighter color (gray-500 or similar)

- [X] T021 [US3] Test summary display in browser
  - Send message with summary
  - Verify summary appears below message content
  - Verify null summary does not show empty space

- [X] T022 [US3] Test summary display for long messages
  - Send message with 500+ characters
  - Verify summary is concise and displayed correctly

---

## Phase 5: Polish & Cross-Cutting Concerns

- [X] T023 Add error handling for summary generation failure
  - Test with invalid API key
  - Verify null summary is returned
  - Verify message still appears on dashboard

- [X] T024 Add error handling for delete operation failure
  - Test with database connection issue
  - Verify user-friendly error message

- [X] T025 Verify all functionality works end-to-end
  - Create message → verify summary generated → delete message → verified removed

- [X] T026 Manual testing checklist
  - [X] Send long message, verify summary generated
  - [X] Send short message, verify summary reflects content
  - [X] Click delete button, verify confirmation appears
  - [X] Confirm deletion, verify message disappears
  - [X] Cancel deletion, verify message remains
  - [X] Test with AI unavailable, verify no summary shown

---

## Task Dependencies

```
T001, T002 (Foundation)
    ↓
T003, T004, T005, T006, T007, T008, T009 (US1 - Summary)
    ↓
T010, T011, T012, T013, T014, T015, T016, T017 (US2 - Delete)
    ↓
T018, T019, T020, T021, T022 (US3 - Display)
    ↓
T023, T024, T025, T026 (Polish)
```

## Parallel Execution

- T003 and T010 can run in parallel (different files)
- T005 and T013 can run in parallel (backend vs frontend)
- T018 and T019 can run in parallel (interface vs display)

## Task Summary

| Phase | Tasks | Count |
|-------|-------|-------|
| Foundation | T001, T002 | 2 |
| US1 - Summary | T003-T009 | 7 |
| US2 - Delete | T010-T017 | 8 |
| US3 - Display | T018-T022 | 5 |
| Polish | T023-T026 | 4 |
| **Total** | | **26** |

## Suggested MVP

**MVP Scope**: T001-T009 (Summary Agent only)
- Gets summary generation working end-to-end
- Can add delete and display features later
