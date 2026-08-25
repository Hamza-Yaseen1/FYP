---
id: phr-20260821-plan-user-auth
title: Week 3 Auth Implementation Plan
stage: plan
date: 2026-08-21
surface: cli
model: big-pickle
feature: 007-user-auth
branch: 007-user-auth
user: user
command: /sp.plan
labels: [plan, authentication, signup, jwt, bcrypt, week-3]
links:
  spec: specs/007-user-auth/spec.md
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - specs/007-user-auth/plan.md
  - specs/007-user-auth/research.md
  - specs/007-user-auth/data-model.md
  - specs/007-user-auth/contracts/auth-api.md
  - specs/007-user-auth/quickstart.md
  - AGENTS.md
tests: []
---

## Prompt

Create a practical technical implementation plan for Week 3 – Authentication (starting with Day 15 – Signup).

### Context
- Project: Communication AI
- Frontend: Next.js + TypeScript + Tailwind + shadcn/ui
- Backend: FastAPI + MongoDB
- AI pipeline is already working
- Now we need real multi-user authentication

### Day 15 Goal – Signup:
- Create /signup page
- Fields: Name, Email, Password, Confirm Password
- Backend: POST /auth/register
- Password must be hashed (bcrypt or passlib)
- Save user in MongoDB

### Overall Week 3 Goals:
- Signup + Login
- JWT authentication (or secure cookies)
- Protected routes
- User isolation (every message/task belongs to a userId)

### Please include in the plan:
1. Goal of this phase
2. Technical approach (keep it simple and secure)
3. Files that need to be created or updated
4. User data model
5. How password hashing will work
6. How JWT authentication will work
7. Implementation steps in order (start with Signup)
8. Testing plan
9. Definition of Done for Day 15

Follow the principles: Simplicity First + Security & Privacy.
Save the plan in the appropriate location.

## Response snapshot

Ran setup-plan.ps1 (branch 007-user-auth), wrote plan.md with full Technical Context, a 12-gate Constitution Check (all PASS, no complexity violations), concrete file tree (backend: routes/auth.py, services/security.py, dependencies.py, models/user.py; frontend: middleware.ts, lib/api.ts, rewritten (auth)/signup page), a 5-slice implementation sequence starting with the Day 15 signup vertical slice, testing plan (pytest unit/integration/isolation + manual quickstart), and an explicit Day 15 Definition of Done. Phase 0 research.md resolved all decisions: direct `bcrypt` package over unmaintained passlib; PyJWT over python-jose; JWT in httpOnly SameSite=Lax cookie (`cai_token`, 7d, HS256); two-layer protection (Next.js edge middleware = presence-only redirect, FastAPI get_current_user = real enforcement); EmailStr + lowercase normalization + unique index for race-proof email uniqueness; webhooks/simulate require auth in Week 3 (documented decision); legacy-data assignment script; pytest + httpx against a dedicated test DB. Phase 1 produced data-model.md (User entity + user_id ownership on messages/tasks + session token claims + isolation invariant), contracts/auth-api.md (register/login/logout/me with exact status codes and error model, 404-not-403 cross-user rule), quickstart.md (per-slice manual verification walkthroughs), and updated AGENTS.md via update-agent-context.ps1.

## Outcome

- ✅ Impact: Complete Phase 0 + Phase 1 planning artifacts ready for /sp.tasks
- 🧪 Tests: N/A (planning); testing plan defined (pytest suites + manual quickstart)
- 📁 Files: plan.md, research.md, data-model.md, contracts/auth-api.md, quickstart.md, AGENTS.md (agent context)
- 🔁 Next prompts: /sp.tasks for 007-user-auth, then implement Slice 1 (Day 15 signup)
- 🧠 Reflection: Chose direct bcrypt over passlib due to passlib's bcrypt-4.x breakage; kept middleware presence-only so real authorization stays server-side per constitution rule 3

## Evaluation notes (flywheel)

- Failure modes observed: update-agent-context.ps1 parsed multi-line Technical Context values slightly truncated (cosmetic)
- Graders run and results (PASS/FAIL): Constitution Check 12/12 gates PASS post-design
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
