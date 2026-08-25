---
id: phr-20260821-tasks-user-auth
title: Week 3 Auth Task List
stage: tasks
date: 2026-08-21
surface: cli
model: big-pickle
feature: 007-user-auth
branch: 007-user-auth
user: user
command: /sp.tasks
labels: [tasks, authentication, signup, isolation, week-3]
links:
  spec: specs/007-user-auth/spec.md
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - specs/007-user-auth/tasks.md
tests:
  - backend/tests/test_auth.py (planned by T006/T007)
---

## Prompt

Create a clear and actionable task list for Week 3 – Authentication (starting with Day 15 – Signup).

### Context
- Project: Communication AI
- Frontend: Next.js + TypeScript + Tailwind + shadcn/ui
- Backend: FastAPI + MongoDB
- AI pipeline is already working
- Now we need real user authentication

### Day 15 Focus – Signup:
- Create /signup page with fields: Name, Email, Password, Confirm Password
- Backend endpoint: POST /auth/register
- Password must be securely hashed
- Save user in MongoDB users collection

### Also prepare for the rest of Week 3:
- Login
- JWT authentication
- Protected routes
- User isolation (userId on messages and tasks)

### Requirements for the task list:
- Break work into small, clear, executable tasks
- Group tasks logically (Backend Auth, Frontend Signup Page, Validation, Testing)
- Write tasks in action language
- Include acceptance criteria for important tasks
- Follow Simplicity First + Security principles
- Start with Signup first (Day 15)

Save the file in the appropriate location.

## Response snapshot

Ran check-prerequisites.ps1 (FEATURE_DIR confirmed) and generated specs/007-user-auth/tasks.md with 34 strictly-formatted checklist tasks across 7 phases: Setup (T001-T002 deps+secret), Foundational (T003-T005 users_collection, security.py hash/JWT service, lib/api.ts fetch wrapper), US1 Signup P1/Day15 MVP (T006-T014: failing contract+unit tests first, UserCreate model with EmailStr and 8..72 password, POST /auth/register with lowercase normalization + bcrypt + httpOnly SameSite=Lax cookie, startup unique index, /signup form with mirrored client validation, presence-only middleware), US2 Login P2 (T015-T020: generic-error login contract tests, get_current_user dependency, /auth/me + logout, login page), US3 Isolation P3 (T021-T027: two-user cross-access 404 tests, user_id stamping + owner-scoped queries in messages/tasks/webhooks routers, frontend fetch switch, legacy-data script), US4 Protected Access P4 (T028-T031: anonymous-surface 401 tests, allowlist audit, back-button verification), Polish (T032-T034 navbar logout chip, expiry UX, full suite + constitution compliance review). Acceptance criteria embedded under key implementation tasks; tests mandatory per constitution Quality Bar; dependencies graph and parallel opportunities documented; MVP scope = Phase 1+2+3 (Day 15).

## Outcome

- ✅ Impact: Executable task list ready — each task self-contained with exact file paths
- 🧪 Tests: Test-first tasks embedded per story (T006/T007, T015, T021, T028); format validation passed 34/34
- 📁 Files: specs/007-user-auth/tasks.md
- 🔁 Next prompts: begin implementation at T001 (or /sp.implement flow); Day 15 = T001–T014
- 🧠 Reflection: get_current_user placed in US2 (needed by /auth/me) so US3 scoping consumes it naturally; middleware kept in US1 because Day 15 DoD requires the redirect

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): checklist-format validation PASS (regex over all 34 task lines)
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
