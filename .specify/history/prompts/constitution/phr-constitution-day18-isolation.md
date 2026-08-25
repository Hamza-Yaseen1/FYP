---
id: phr-constitution-day18-isolation
title: "Day 18 User Isolation Constitution"
stage: constitution
date: 2026-08-25
surface: cli
model: big-pickle
feature: user-isolation
branch: main
user: user
command: /sp.constitution
labels: [constitution, security, isolation, day-18]
links:
  spec: N/A
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - .specify/memory/constitution.md
tests:
  - backend/tests/test_auth.py (27/27 passed)
  - app/api/auth/logout/route.test.ts (4/4 passed)
---

## Prompt

Create a focused constitution for Day 18 – User Isolation.

### Context
- Project: Communication AI (FYP)
- Login, Signup, and Route Protection are already working
- Now we must enforce strong data isolation between users

### Goal of Day 18:
Every message, task, and analysis must belong to a specific user.

Rules:
- User A has Message A
- User B has Message B
- User A must **never** see Message B
- User B must **never** see Message A

Every communication, task, and related data must be linked to a `userId`.

### Please create a short constitution that covers:
1. Purpose of User Isolation
2. Core Privacy & Security Principles
3. Strict rules for data ownership
4. What must never happen
5. Quality bar for user isolation

This is a critical security feature. Keep the language clear and strict.
Align with the main project constitution (Security & Privacy is mandatory).

## Response snapshot

Updated `.specify/memory/constitution.md` from v1.5.0 to v1.6.0 (MINOR bump).

Changes made:
1. Added "Day 18 User Isolation Contract" section after Day 17 Route Protection
   Contract, containing: Purpose of User Isolation, Core Privacy & Security
   Principles (6 rules), Strict Rules for Data Ownership (table + 5 rules),
   What Must NEVER Happen (8 absolute prohibitions), Quality Bar for User
   Isolation (7 verification criteria).
2. Strengthened existing "User Isolation Rules" from 5 rules to 11, adding:
   aggregation pipeline filtering, error response sanitization, frontend state
   clearing, index requirements, webhook ownership, and list endpoint filtering.
3. Added 6 new Compliance Checklist items for Day 18 isolation requirements.
4. Updated Sync Impact Report at top of file.
5. Updated version footer to 1.6.0 with date 2026-08-25.

## Outcome

- ✅ Impact: Constitution updated with focused Day 18 User Isolation section;
  compliance checklist expanded with 6 new isolation-specific checks.
- 🧪 Tests: 27/27 backend tests passed; 4/4 frontend tests passed; next build
  clean.
- 📁 Files: .specify/memory/constitution.md (single file modified)
- 🔁 Next prompts: N/A
- 🧠 Reflection: The existing User Isolation Rules (5 items) were too brief for
  a critical security feature. The Day 18 section provides the depth needed:
  ownership tables, absolute prohibitions, and concrete verification criteria.
  The MINOR bump is appropriate because a new section was added with material
  new guidance, not just clarifications.

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): PASS — all bracket tokens resolved,
  version matches report, dates ISO format, principles declarative and testable
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
