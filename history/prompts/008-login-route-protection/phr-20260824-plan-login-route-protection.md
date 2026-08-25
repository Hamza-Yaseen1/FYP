---
id: phr-20260824-plan-login-route-protection
title: Login Route Protection Implementation Plan
stage: plan
date: 2026-08-24
surface: cli
model: big-pickle
feature: 008-login-route-protection
branch: 008-login-route-protection
user: user
command: /sp.plan
labels: [plan, authentication, login, jwt, route-protection, ui-ux, dark-theme]
links:
  spec: specs/008-login-route-protection/spec.md
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - specs/008-login-route-protection/plan.md
  - specs/008-login-route-protection/research.md
  - specs/008-login-route-protection/data-model.md
  - specs/008-login-route-protection/contracts/auth.yaml
  - specs/008-login-route-protection/quickstart.md
  - AGENTS.md
tests:
  - backend/tests/test_auth.py (existing suites must stay green)
---

## Prompt

Create a practical technical implementation plan for Day 16 and Day 17:

1. Login
2. Protect Routes
3. Beautiful Login & Signup pages

### Context
- Project: Communication AI
- Frontend: Next.js + TypeScript + Tailwind + shadcn/ui
- Backend: FastAPI + MongoDB
- Signup is already working
- Now we need full authentication

### Goals:
- Working Login (POST /auth/login)
- JWT-based authentication
- GET /auth/me endpoint
- Protect frontend routes (/dashboard, /inbox, /tasks, etc.)
- Protect backend APIs
- User isolation (each user only sees their own data)
- Make Login and Signup pages look beautiful and modern (dark theme)

### Please include in the plan:
1. Goal of this phase
2. Technical approach (JWT recommended)
3. Files that need to be created or updated
4. How Login will work (step-by-step)
5. How route protection will work (Frontend + Backend)
6. How to make Auth pages beautiful
7. Implementation steps in order
8. Testing plan
9. Definition of Done

Follow Simplicity First + Security principles.
Save the plan in the appropriate location.

## Response snapshot

Ran setup-plan.ps1 → branch 008-login-route-protection, plan.md initialized. **Critical audit finding woven into the plan**: Day 16/17 backend and route protection ALREADY EXIST and are tested (auth.py has register/login/me/logout with bcrypt+HS256 JWT `cai_token` httpOnly cookie; get_current_user dependency guards messages/tasks/webhooks routes with user_id scoping; middleware.ts guards all six workspace prefixes and bounces authed users off auth pages; test_auth.py covers contracts/isolation/protected-surface). The genuine remaining work = auth UI dark-theme polish + end-to-end verification audit. Plan contains all nine requested sections: goal, technical approach (as-built JWT confirmed in research R4 — no refresh tokens per Simplicity First), concrete file list (CREATE components/auth/password-input.tsx; UPDATE app/(auth)/layout.tsx via `.dark` wrapper div exploiting existing Tailwind v4 token variant, login/page.tsx, signup/page.tsx parity polish; EXTEND tests only if audit finds gaps), login step-by-step, dual-layer route protection explanation, beauty approach (scoped dark tokens, gradient backdrop, toggle, focus rings, spacing scale), ordered phases A/B/C, layered testing table, and a 7-point DoD. Constitution Check gate table: all PASS, Complexity Tracking empty. Phase 0 research.md resolves six decisions (scope reality-check R1, auth-scoped vs global dark theme R2 → wrapper div keeping dashboard untouched, toggle pattern R3, session mechanism confirmation R4, no-new-test-framework stance R5, test-extension criteria R6). Phase 1 produced data-model.md (zero schema changes; session lifecycle documented), contracts/auth.yaml (valid OpenAPI 3.0 as-built auth surface incl. cookieAuth scheme), quickstart.md (setup + AC-matrix walkthrough sections A/B/C + DoD checklist + production notes e.g. secure=True behind HTTPS). Agent context updated via update-agent-context.ps1 -AgentType opencode (AGENTS.md refreshed). Post-design constitution re-check: no violations.

## Outcome

- ✅ Impact: Feature reframed honestly from "build auth" to "polish + verify auth" — prevents redundant rebuild of tested code; implementation-ready plan with resolved decisions
- 🧪 Tests: N/A yet (planning); quickstart.md defines the authoritative manual verification matrix; pytest suites designated as regression guard
- 📁 Files: plan.md, research.md, data-model.md, contracts/auth.yaml, quickstart.md, AGENTS.md (agent context)
- 🔁 Next prompts: /sp.tasks for 008-login-route-protection to generate the task breakdown, then /sp.red//sp.green for implementation
- 🧠 Reflection: The audit-first move was the highest-value step — the spec assumed greenfield but the repo already had the backend from 007's green phases; planning against reality kept the slice simple (4 files) instead of ~15. Dark-theme decision deliberately scopes to (auth) group to avoid out-of-scope dashboard regressions.

## Evaluation notes (flywheel)

- Failure modes observed: None this run (create-phr.sh absent — manual fallback used again)
- Graders run and results (PASS/FAIL): OpenAPI YAML hand-fixed after initial draft contained an invalid placeholder section (caught by self-review before finalizing) PASS; constitution gates all PASS
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): add create-phr.sh equivalent PowerShell script to .specify/scripts/powershell/
