---
id: phr-20260821-week3-auth
title: Week 3 Auth Constitution Amendment
stage: constitution
date: 2026-08-21
surface: cli
model: big-pickle
feature: N/A
branch: N/A
user: user
command: /sp.constitution
labels: [constitution, authentication, multi-user, security, week-3, day-15]
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

Create a focused constitution for Week 3 – Authentication & Multi-user system (starting with Day 15 – Signup).

### Context
- Project: Communication AI (FYP)
- Week 1 & Week 2 (AI Pipeline) are completed
- Now we are turning the project into a real multi-user SaaS application

### Goals of Week 3:
- Users can Sign Up and Login
- Each user only sees their own messages and tasks
- Proper password hashing
- Protected routes (Dashboard, etc. should not be accessible without login)
- User isolation (very important)

### Day 15 Focus – Signup:
- Page: /signup
- Fields: Name, Email, Password, Confirm Password
- Backend: POST /auth/register
- Password must be securely hashed

### Please create a short constitution that covers:
1. Purpose of Authentication in this project
2. Core Security Principles
3. User Isolation rules (one user must never see another user's data)
4. Password handling rules
5. What should be protected
6. Quality bar for authentication

Keep it practical, secure, and aligned with the main project constitution (Simplicity First + Security & Privacy).

## Response snapshot

Amended constitution to v1.4.0 (MINOR bump) with new "Authentication & Multi-User System" section covering all six requested areas: purpose of authentication (multi-user SaaS conversion; success = two users coexist without seeing each other's data), five core security principles (deny by default, never trust the client, server-side enforcement, fail closed, minimal exposure), five user isolation rules (mandatory server-set user_id on every document, user-filtered queries only, 404 not 403 for cross-user access, ownership model before first write, two-user isolation test), five password handling rules (bcrypt/argon2id hashing, 8-char minimum, unique email index, generic login errors, no plaintext anywhere), explicit protected surface list (protected pages/APIs vs public allowlist vs webhook auth decisions), Day 15 signup contract (/signup page with Name/Email/Password/Confirm Password → POST /auth/register → hashed storage + session cookie), and an eight-point authentication quality bar. Added 5 new compliance review checks. Templates verified compatible, no changes needed.

## Outcome

- ✅ Impact: Constitution extended with Week 3 authentication governance; project formally transitions to multi-user SaaS rules
- 🧪 Tests: N/A (constitution update); validation confirmed no bracket tokens remain, version/date format correct
- 📁 Files: .specify/memory/constitution.md
- 🔁 Next prompts: /sp.spec or /sp.plan for the signup feature (Day 15), then /sp.tasks
- 🧠 Reflection: MINOR bump correct — new section added, no existing principles redefined; isolation written as MUST-level rules because it is the stated highest-priority requirement of Week 3

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
