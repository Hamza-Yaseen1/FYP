---
id: phr-tasks-day18-user-isolation
title: "Day 18 User Isolation Tasks"
stage: tasks
date: 2026-08-25
surface: cli
model: big-pickle
feature: 009-user-isolation
branch: 009-user-isolation
user: user
command: /sp.tasks
labels: [tasks, security, user-isolation, day-18]
links:
  spec: specs/009-user-isolation/spec.md
  ticket: ""
  adr: ""
  pr: ""
files:
  - specs/009-user-isolation/tasks.md
tests:
  - backend/tests/test_user_isolation.py
---

## Prompt

Create a clear and actionable task list for Day 18 – User Isolation.

Context: Communication AI project. Authentication already working. Need to enforce strict per-user data isolation. Every message and task must have a userId. All fetch APIs must only return data for the current user. User A must never see User B's messages or tasks.

Focus areas: Add userId to messages and tasks, update message creation to include current userId, update all GET endpoints to filter by userId, update frontend to work with authenticated user data only, test with two different users.

Requirements: Break work into small clear executable tasks, group logically (Database, Backend, Frontend, Testing), write tasks in action language, include acceptance criteria for important tasks, this is a security-critical feature.

Design documents loaded: plan.md, spec.md, data-model.md, research.md, contracts/api.md. Generated 41 tasks across 10 phases organized by 6 user stories.

## Response snapshot

Generated tasks.md with 41 tasks across 10 phases:

- Phase 1 (Setup): 2 tasks — MongoDB indexes on messages.user_id and tasks.user_id
- Phase 2 (Foundational): 5 tasks — Fix analyzer bug (add user_id param, include in task docs, guard for None), update route handlers
- Phase 3 (US1 - Messages P1): 5 tasks — Verify all message endpoints enforce user_id
- Phase 4 (US2 - Tasks P1): 3 tasks — Verify all task endpoints enforce user_id
- Phase 5 (US3 - AI Analysis P1): 2 tasks — Verify analysis stays with owner
- Phase 6 (US4 - Webhooks P2): 2 tasks — Verify webhook messages scoped to owner
- Phase 7 (US5 - Dashboard P2): 2 tasks — Verify frontend fetches authenticated data
- Phase 8 (US6 - Logout P2): 2 tasks — Verify logout clears all state
- Phase 9 (Tests): 15 tasks — Comprehensive two-user isolation tests
- Phase 10 (Polish): 3 tasks — Final verification

Parallel opportunities: T001/T002 (indexes), T006/T007 (route handlers), T025-T036 (test methods), US4-US6 after P1 stories.

## Outcome

- ✅ Impact: HIGH — Security-critical task list for user data isolation
- 🧪 Tests: 15 new test tasks in test_user_isolation.py
- 📁 Files: specs/009-user-isolation/tasks.md (created)
- 🔁 Next prompts: /sp.execute (implement tasks), or start with T001
- 🧠 Reflection: Task organization by user story enables independent testing. Foundational phase (analyzer fix) is the critical path — blocks all user story work. Most existing endpoints already have user_id filtering — verification tasks are lightweight. The real work is in the analyzer fix (T003-T007) and comprehensive tests (T024-T038).

## Evaluation notes (flywheel)

- Failure modes observed: None — template-driven generation
- Graders run and results: N/A
- Prompt variant: Standard /sp.tasks with user-provided context
- Next experiment: Execute tasks starting with T001-T007 (foundational work)
