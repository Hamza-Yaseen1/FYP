---
id: phr-20260824-tasks-login-route-protection
title: Login Route Protection Task Breakdown
stage: tasks
date: 2026-08-24
surface: cli
model: big-pickle
feature: 008-login-route-protection
branch: 008-login-route-protection
user: user
command: /sp.tasks
labels: [tasks, authentication, login, route-protection, ui-ux]
links:
  spec: specs/008-login-route-protection/spec.md
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - specs/008-login-route-protection/tasks.md
tests:
  - backend/tests/test_auth.py (regression baseline + conditional extension T011)
---

## Prompt

Create a clear and actionable task list for Day 16 and Day 17:

1. Login
2. Protect Routes
3. Beautiful Login & Signup pages

### Context
- Project: Communication AI
- Signup is already working
- Frontend: Next.js + TypeScript + Tailwind + shadcn/ui
- Backend: FastAPI + MongoDB
- Keep everything simple and secure

### Focus Areas:

**Login:**
- Create /login page
- Create POST /auth/login endpoint
- Use JWT authentication
- Store token securely
- Redirect to Dashboard after login

**Protect Routes:**
- Create GET /auth/me endpoint
- Protect frontend pages (/dashboard, /inbox, /tasks, etc.)
- Protect backend APIs
- Redirect unauthenticated users to /login
- Keep session working after refresh

**UI:**
- Make Login and Signup pages beautiful, modern, and professional (dark theme)
- Clean form design, good spacing, clear errors

### Requirements for the task list:
- Break work into small, clear, executable tasks
- Group tasks logically (Backend Auth, Frontend Pages, Protection, UI Design, Testing)
- Write tasks in action language
- Include acceptance criteria for important tasks
- Follow Simplicity First + Security principles

Save the file in the appropriate location.

## Response snapshot

check-prerequisites.ps1 confirmed FEATURE_DIR and full doc set; generated specs/008-login-route-protection/tasks.md with 20 checklist-format tasks across 6 phases, organized by spec user stories rather than the user's suggested grouping (documented why: plan audit proved Backend Auth/Protection are built+tested, so those become verification phases instead of build phases). Phase 1 Setup: baseline pytest + lint/tsc ([P] pair). Phase 2 Foundational: curl-audit auth surface against contracts/auth.yaml (T003) + conditional minimal fix (T004). Phase 3 US1 Login (P1): browser execution of quickstart section A incl. client-blocked validation, identical generic errors, HttpOnly cookie checks (T005–T006). Phase 4 US2 Locked Workspace (P2): six-prefix redirect matrix, endpoint 401 curls, refresh persistence, tampered-cookie bounce, logout/back-button, two-user isolation re-check, conditional test-extension guard T011 wired to plan decision R6 (T007–T011). Phase 5 US3 UI Polish (P3) = ~70% of real work: CREATE components/auth/password-input.tsx ∥ restyle app/(auth)/layout.tsx `.dark` shell → polish login/page.tsx then signup/page.tsx with byte-frozen behavior → optional globals.css utility only if Tailwind utilities insufficient (T012–T016). Phase 6 Polish: responsive 360/768/1280, keyboard/focus pass, stopped-backend error path, final DoD sweep tying back to T001 baselines and quickstart checklist (T017–T020). Includes dependencies graph, parallel examples, MVP-first strategy, and honest completed-as-N/A convention for conditional tasks. Format validated: every task has checkbox + ID + correct [P]/[Story] usage + file/command paths.

## Outcome

- ✅ Impact: Feature is now fully specified→planned→tasked; executable without extra context thanks to quickstart cross-references and exact file paths
- 🧪 Tests: No new automated tests mandated (spec did not request them); pytest designated regression bar; manual quickstart matrix authoritative per constitution
- 📁 Files: specs/008-login-route-protection/tasks.md
- 🔁 Next prompts: /sp.red or begin green implementation starting with T001–T002 baselines
- 🧠 Reflection: Reorganizing the requested logical groups into story-phases preserved the user's intent while respecting the audit reality — verification-as-story kept US1/US2 honest instead of pretending to rebuild tested code; conditional-task convention prevents speculative churn

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): task format self-validation PASS (20/20 checklist-compliant)
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
