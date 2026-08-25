---
id: phr-plan-day18-user-isolation
title: "Day 18 User Isolation Plan"
stage: plan
date: 2026-08-25
surface: cli
model: big-pickle
feature: 009-user-isolation
branch: 009-user-isolation
user: user
command: /sp.plan
labels: [plan, security, isolation, day-18]
links:
  spec: specs/009-user-isolation/spec.md
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - specs/009-user-isolation/plan.md
  - specs/009-user-isolation/research.md
  - specs/009-user-isolation/data-model.md
  - specs/009-user-isolation/quickstart.md
  - specs/009-user-isolation/contracts/api.md
tests:
  - 27 existing backend tests must pass
  - New test_user_isolation.py must pass
  - Two-user isolation test: register A+B, create messages+tasks, verify separation
---

## Prompt

Create a practical technical implementation plan for Day 18 – User Isolation.

### Context
- Project: Communication AI
- Authentication (Signup, Login, Protected Routes) is already working
- Now we must enforce strict data isolation between users

### Critical Goal:
- Every message, task, and AI analysis must belong to a specific userId
- User A must never see User B's data
- When a message is created (via simulate or webhook), it must be linked to the currently logged-in user
- All GET APIs must only return data that belongs to the authenticated user

### Please include in the plan:
1. Goal of this phase
2. Technical approach
3. Files / collections that need to be updated
4. How userId will be added to messages and tasks
5. How backend APIs will filter data by userId
6. How the frontend will work with the current user
7. Implementation steps in order
8. Testing plan (important: test with two different users)
9. Definition of Done

This is a critical security feature. Keep it simple but strict.
Follow the principle: Security & Privacy is mandatory.

## Response snapshot

Created implementation plan with 5 steps, research.md with 4 decisions,
data-model.md with ownership model, contracts/api.md with endpoint
inventory, and quickstart.md with manual verification steps.

Primary fix identified: `analyze_message()` in `backend/services/ai/analyzer.py`
creates tasks via `insert_many()` without `user_id`. Fix: add `user_id`
parameter, pass it from route handlers, include in every task doc.

Secondary work: add MongoDB compound indexes on `messages.user_id` and
`tasks.user_id`, write comprehensive two-user isolation tests.

Constitution check: ALL 7 principles PASS. No violations.

## Outcome

- ✅ Impact: Complete implementation plan with 5 ordered steps, 4 research
  decisions, data model, API contracts, quickstart guide, and 8-item
  Definition of Done.
- 🧪 Tests: Plan specifies new test_user_isolation.py with comprehensive
  two-user isolation coverage across all endpoints.
- 📁 Files: plan.md, research.md, data-model.md, quickstart.md,
  contracts/api.md
- 🔁 Next prompts: /sp.tasks (task breakdown)
- 🧠 Reflection: The plan is intentionally minimal — one parameter change,
  one index addition, one test file. The simplicity principle is preserved.
  The primary bug (tasks without user_id) is a one-line fix that has
  outsized security impact.

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): PASS — constitution check all green,
  no unresolved clarifications, plan is complete and actionable
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
