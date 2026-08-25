---
id: phr-20260821-spec-user-auth
title: Week 3 Auth Signup Specification
stage: spec
date: 2026-08-21
surface: cli
model: big-pickle
feature: 007-user-auth
branch: 007-user-auth
user: user
command: /sp.specify
labels: [spec, authentication, signup, multi-user, security, week-3]
links:
  spec: specs/007-user-auth/spec.md
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - specs/007-user-auth/spec.md
  - specs/007-user-auth/checklists/requirements.md
tests: []
---

## Prompt

Create a clear and focused specification for Week 3 – Authentication (starting with Day 15 – Signup).

### Context
- Project: Communication AI
- AI Pipeline is already working
- Now we need to make it a real multi-user application

### Day 15 – Signup Requirements:
- Frontend page: /signup
- Fields:
  - Name
  - Email
  - Password
  - Confirm Password
- Backend endpoint: POST /auth/register
- Password must be securely hashed (e.g. bcrypt)
- Basic validation (email format, password match, etc.)

### Overall Authentication Goals for Week 3:
- Users can register and login
- JWT or secure cookie-based authentication
- Protected routes (Dashboard, Inbox, Tasks, etc.)
- Strong user isolation (User A must never see User B's messages or tasks)
- Each message and task must belong to a specific user

### Please include in the specification:
1. Feature Overview
2. User Stories (Signup, Login, Protected Access, User Isolation)
3. Data Model for User
4. API Endpoints needed
5. Acceptance Criteria for Signup
6. Security Rules
7. Edge cases (duplicate email, weak password, etc.)

Keep it simple, secure, and practical for a university FYP.

## Response snapshot

Created branch 007-user-auth and wrote specs/007-user-auth/spec.md following the repo spec pattern (matching 006-complete-ai-pipeline). Feature Overview frames the multi-user conversion; four prioritized user stories — Signup (P1, five acceptance scenarios covering all field validations), Login (P2, generic-error anti-enumeration), User Isolation (P3, cross-user access returns not-found; UI + direct-request verification), Protected Access (P4, redirect/401/back-button scenarios); eight edge cases (concurrent duplicate email, casing normalization, whitespace names, session expiry, forged credentials, client-supplied user id ignored, unicode passwords, legacy demo data ownership). Sixteen functional requirements grouped into Registration / Login & Session / Protected Surface / User Isolation, plus capability-level API endpoint table (register/login/logout/me + scoped existing endpoints), Signup Acceptance Criteria summary table (AC-1..AC-7), eight security rules aligned with constitution v1.4.0, Key Entities (User, Session Credential, Owned Record with server-set user_id), seven measurable success criteria (SC-001..SC-007 including zero-leakage two-user test), Assumptions (no OAuth/email verification, 8-char minimum, 7-day session), and Out of Scope. Zero NEEDS CLARIFICATION markers — all defaults documented. Quality checklist created at checklists/requirements.md, PASS on first iteration.

## Outcome

- ✅ Impact: Complete Draft spec for Week 3 authentication ready for planning
- 🧪 Tests: N/A (specification); quality checklist PASS (16/16 items)
- 📁 Files: specs/007-user-auth/spec.md, specs/007-user-auth/checklists/requirements.md
- 🔁 Next prompts: /sp.clarify (optional) or /sp.plan for 007-user-auth
- 🧠 Reflection: Isolation ranked P3 below Login only for build order but flagged as the highest-stakes guarantee; technology references kept because the user explicitly requested them and constitution v1.4.0 already fixed them

## Evaluation notes (flywheel)

- Failure modes observed: create-new-feature.ps1 Join-Path multi-arg call fails on Windows PowerShell 5.1 (branch + spec file still created; prompts dir created manually)
- Graders run and results (PASS/FAIL): spec quality checklist PASS
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
