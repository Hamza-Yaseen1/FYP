---
id: phr-spec-day18-user-isolation
title: "Day 18 User Isolation Spec"
stage: spec
date: 2026-08-25
surface: cli
model: big-pickle
feature: 009-user-isolation
branch: 009-user-isolation
user: user
command: /sp.specify
labels: [spec, security, isolation, day-18]
links:
  spec: specs/009-user-isolation/spec.md
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - specs/009-user-isolation/spec.md
  - specs/009-user-isolation/checklists/requirements.md
tests:
  - All 17 acceptance scenarios are independently testable
  - Checklist: 16/16 items pass
---

## Prompt

Create a clear and focused specification for Day 18 – User Isolation.

### Context
- Project: Communication AI
- Authentication (Signup, Login, Protected Routes) is already working
- Now we must make sure every user only sees their own data

### Critical Goal:
- User A has Message A
- User B has Message B
- User A must **never** receive or see Message B
- Every message, task, and AI analysis must belong to a specific `userId`

### Requirements:
1. Every document in `messages`, `tasks`, and related collections must have a `userId` field
2. When creating a message (via webhook or simulate), it must be saved under the currently logged-in user
3. When fetching messages or tasks, only return data that belongs to the current user
4. Backend APIs must filter by the authenticated user's ID
5. Frontend should only display the current user's data

### Please include in the specification:
1. Feature Overview
2. User Stories
3. Data ownership rules
4. API changes required
5. Acceptance Criteria
6. Security rules
7. Edge cases (e.g. what happens if userId is missing)

This is a critical security feature. Be strict and clear.

## Response snapshot

Created branch `009-user-isolation` and wrote `specs/009-user-isolation/spec.md`
with 6 user stories (P1: messages, tasks, analysis isolation; P2: webhooks,
dashboard, logout state), 17 acceptance scenarios, 17 functional requirements,
8 edge cases, data ownership rules, API change inventory, security rules, and
assumptions. Quality checklist: 16/16 items pass. Primary bug identified: AI
analyzer creates tasks without user_id.

Key findings from codebase exploration:
- Messages already have `user_id` set correctly in route handlers
- Tasks are created by the AI analyzer WITHOUT `user_id` — this is the
  primary bug to fix
- No MongoDB indexes on `user_id` fields — performance concern
- `ai_analysis_collection` and `connections_collection` defined but unused

## Outcome

- ✅ Impact: Complete feature specification for Day 18 User Isolation with
  6 user stories, 17 acceptance scenarios, 17 functional requirements,
  and 8 edge cases.
- 🧪 Tests: Checklist 16/16 pass. All acceptance scenarios independently
  testable.
- 📁 Files: specs/009-user-isolation/spec.md,
  specs/009-user-isolation/checklists/requirements.md
- 🔁 Next prompts: /sp.plan (implementation planning)
- 🧠 Reflection: The spec correctly identifies the primary isolation bug
  (tasks without user_id) and defines strict behavioral contracts for all
  API endpoints. The 404-not-403 rule is critical for preventing resource
  existence leakage.

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): PASS — all checklist items pass,
  no NEEDS CLARIFICATION markers, requirements testable and unambiguous
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
