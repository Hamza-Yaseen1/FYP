# Task List: Priority Agent

**Feature**: 2-priority-agent | **Date**: 2026-08-19 | **Spec**: [spec.md](spec.md)

## User Stories

| ID | Story | Priority | Status |
|----|-------|----------|--------|
| US1 | Automatic Priority Classification | P1 | Complete |
| US2 | Priority Override | P2 | Complete |
| US3 | Confidence Visibility | P3 | Complete |

---

## Phase 1: Setup

> Goal: Ensure project is ready for Priority Agent development
> Independent Test: Backend starts without errors

- [x] T001 Install openai package in backend/requirements.txt
- [x] T002 Verify OPENAI_API_KEY environment variable is set
- [x] T003 Verify MongoDB connection works with existing database.py

---

## Phase 2: Foundational

> Goal: Core AI infrastructure ready for priority classification
> Independent Test: analyze_message() returns valid priority result

- [x] T004 Add explanation field to AIAnalysisResult in backend/services/ai/providers/base.py
- [x] T005 Add explanation field to AIAnalysis in backend/models/message.py
- [x] T006 Update backend/services/ai/analyzer.py to include explanation in return dict

---

## Phase 3: US1 - Automatic Priority Classification

> Goal: Messages automatically classified into URGENT/IMPORTANT/NORMAL/LOW
> Independent Test: POST message returns response with priority, confidence, and explanation

### Prompt

- [x] T007 [US1] Rewrite priority prompt in backend/services/ai/prompts/priority.txt per Priority Agent constitution
- [x] T008 [US1] Update backend/services/ai/providers/openai.py to use priority-focused prompt

### Backend

- [x] T009 [US1] Verify POST /messages triggers AI analysis and returns priority
- [x] T010 [US1] Verify priority defaults to "normal" when AI fails (status: "pending")

### Frontend

- [x] T011 [US1] Create PriorityBadge component in app/components/priority-badge.tsx
- [x] T012 [US1] Add priority badge to MessageCard component in app/components/message-card.tsx
- [x] T013 [US1] Sort messages by priority in app/(dashboard)/page.tsx (URGENT > IMPORTANT > NORMAL > LOW)

---

## Phase 4: US2 - Priority Override

> Goal: Users can change priority of any message
> Independent Test: PUT /messages/{id}/priority updates priority and persists

### Backend

- [x] T014 [US2] Add PUT /messages/{id}/priority endpoint in backend/routes/messages.py
- [x] T015 [US2] Validate priority is one of: urgent, important, normal, low
- [x] T016 [US2] Set confidence to 1.0 and explanation to "User override" on manual change

### Frontend

- [x] T017 [US2] Add priority dropdown to MessageCard in app/components/message-card.tsx
- [x] T018 [US2] Call PUT /messages/{id}/priority on user selection
- [x] T019 [US2] Update priority badge immediately after override

---

## Phase 5: US3 - Confidence Visibility

> Goal: Users see confidence level and low-confidence items are flagged
> Independent Test: Messages with confidence < 50% show "Needs review" flag

### Frontend

- [x] T020 [US3] Add confidence indicator to PriorityBadge in app/components/priority-badge.tsx
- [x] T021 [US3] Show "Needs review" flag when confidence < 0.5
- [x] T022 [US3] Show "Review recommended" flag when confidence 0.5 - 0.79
- [x] T023 [US3] Add explanation tooltip on priority badge hover

---

## Phase 6: Polish & Testing

> Goal: Edge cases handled, manual testing complete
> Independent Test: All manual testing checklist items pass

### Edge Cases

- [x] T024 Test message with deadline today returns URGENT
- [x] T025 Test message with deadline this week returns IMPORTANT
- [x] T026 Test casual message returns NORMAL
- [x] T027 Test automated message returns LOW
- [x] T028 Test empty/short message returns NORMAL with low confidence
- [x] T029 Test very long message (>2000 chars) is truncated for analysis

### Integration

- [x] T030 Test POST /messages with WhatsApp source
- [x] T031 Test POST /messages with Gmail source
- [x] T032 Test POST /messages with Simulated source
- [x] T033 Test priority override persists after page refresh
- [x] T034 Test dashboard auto-polls and shows new priorities

### Definition of Done

- [x] T035 Verify 80% accuracy on test set of 50 messages
- [x] T036 Verify response time < 2 seconds for messages under 1000 chars
- [x] T037 Verify no crashes on AI failure (graceful fallback to NORMAL)

---

## Dependencies

```
T001-T003 (Setup)
    ↓
T004-T006 (Foundational)
    ↓
T007-T013 (US1: Auto Classification) ← MVP
    ↓
T014-T019 (US2: Override)
    ↓
T020-T023 (US3: Confidence)
    ↓
T024-T037 (Polish & Testing)
```

## Parallel Opportunities

| Task Group | Can Parallel With |
|------------|-------------------|
| T007-T008 (Prompt) | T009-T010 (Backend verify) |
| T011-T013 (Frontend US1) | T014-T016 (Backend US2) |
| T017-T019 (Frontend US2) | T020-T023 (Frontend US3) |

## MVP Scope

**Minimum Viable Product**: T001-T013 (Setup + Foundational + US1)

This delivers:
- Messages classified into 4 priority levels
- Priority shown on dashboard
- AI failure gracefully handled

**Total Tasks**: 37
**MVP Tasks**: 13
**Estimated Time**: 2-3 hours for MVP
