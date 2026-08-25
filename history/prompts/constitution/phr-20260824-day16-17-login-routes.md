---
id: phr-20260824-day16-17-login-routes
title: Login Route Protection Auth UI Constitution
stage: constitution
date: 2026-08-24
surface: cli
model: big-pickle
feature: N/A
branch: 007-user-auth
user: user
command: /sp.constitution
labels: [constitution, authentication, login, jwt, route-protection, ui-ux, day-16, day-17]
links:
  spec: N/A
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - .specify/memory/constitution.md
tests: []
---

## Prompt

Create a focused constitution for Day 16 and Day 17:

1. Login
2. Protect Routes
3. Beautiful Login & Signup pages

### Context
- Project: Communication AI (FYP)
- Signup is already working
- Now we need Login + Route Protection + better looking Auth pages

### Goals:

**Day 16 – Login:**
- Create POST /auth/login
- Use secure authentication (JWT recommended)
- After login, user (e.g. Hamza) should only see his own dashboard, messages, tasks, and connections

**Day 17 – Protect Routes:**
- Nobody should access /dashboard, /inbox, /tasks, etc. without login
- Create GET /auth/me endpoint
- Protect all important backend APIs
- Redirect unauthenticated users to /login

**UI Goal:**
- Make both Login and Signup pages look beautiful, modern, and professional (dark theme preferred)
- Clean layout, good spacing, nice inputs, and clear buttons

### Please create a short constitution that covers:
1. Purpose of Login and Route Protection
2. Security principles
3. User isolation rules
4. UI/UX principles for Auth pages
5. Quality bar for this phase

Keep it practical, secure, and aligned with Simplicity First + Security & Privacy.

## Response snapshot

Amended constitution to v1.5.0 (MINOR bump) by extending the existing Authentication & Multi-User System section with three new subsections covering all five requested areas: **Day 16 Login Contract** (POST /auth/login → 200 with user object + JWT in HttpOnly/Secure/SameSite cookie; any failure → 401 generic "Invalid email or password"; token carries user_id as sub with expiry, never localStorage; bcrypt-library verification mandatory; post-login redirect to the user's own dashboard with Hamza example), **Day 17 Route Protection Contract** (GET /auth/me returns {id, name, email} from verified cookie only, 401 otherwise; one shared FastAPI dependency on every data endpoint — endpoint without it does not ship; Next.js middleware redirects logged-out visits on protected pages to /login and logged-in visits on /login//signup to /dashboard; complete public allowlist = /login, /signup, health checks; server-side enforcement is authoritative, React hiding is cosmetic), and **Auth Pages UI/UX Principles** (six rules: dark theme default, centered ~400px card layout, professional inputs with labels/toggles/focus rings/server-authoritative validation, single full-width primary button with spinner + double-click protection, honest inline errors using exact generic wording, consistency over decoration). Security principles and user isolation rules reuse the existing Core Security Principles and User Isolation Rules sections rather than duplicating them. Quality Bar extended with six new criteria (login end-to-end, generic invalid-credential error, /auth/me behavior, auth-page redirect, dark-theme states verified desktop+mobile); Compliance Checklist extended with five new checks. Templates verified compatible — no changes needed (plan gates derive from constitution file; no commands dir exists).

## Outcome

- ✅ Impact: Constitution now governs Days 16–17 concretely; signup-era auth rules upgraded into full login/session/route-protection/UI governance without touching existing principles
- 🧪 Tests: N/A (constitution update); validation confirmed zero bracket tokens, ISO dates, version line matches report
- 📁 Files: .specify/memory/constitution.md
- 🔁 Next prompts: /sp.spec or /sp.plan for "login-route-protection" feature (Days 16–17), then /sp.tasks
- 🧠 Reflection: MINOR bump correct — new subsections materially expand an existing section; no principles removed or redefined. Reused existing isolation/password sections instead of duplicating to keep the document DRY per Simplicity First.

## Evaluation notes (flywheel)

- Failure modes observed: create-phr.sh unavailable (PowerShell-only repo) — used manual template fallback
- Graders run and results (PASS/FAIL): placeholder scan PASS; version/date format PASS
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
