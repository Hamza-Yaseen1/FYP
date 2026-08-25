---
id: phr-constitution-day19-001
title: Day 19 Connection Architecture Constitution
stage: constitution
date: 2026-08-25
surface: cli
model: opencode/big-pickle
feature: connection-architecture
branch: main
user: user
command: constitution
labels: [constitution, day19, connection-architecture, security, isolation]
links:
  spec: N/A
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - .specify/memory/constitution.md
tests:
  - N/A
---

## Prompt

Create a focused constitution for Day 19 – Connection Architecture.

### Context
- Project: Communication AI (FYP)
- Authentication and User Isolation are already working
- Now we are building the foundation for connecting external accounts

### Goal of Day 19:
Create a Connections page and database structure so users can later connect WhatsApp, Gmail, etc.

Page should look like:
Connected Accounts
- WhatsApp   [ Connect ]
- Gmail      [ Connect ]
- LinkedIn   [ Coming Soon ]

Database collection: `connections`
Fields:
- userId
- provider
- status
- accessToken
- refreshToken
- createdAt

Important: Sensitive tokens must be protected and should never be exposed to the frontend.

### Please create a short constitution that covers:
1. Purpose of the Connections feature
2. Security principles for storing tokens
3. Rules for user isolation (connections also belong to a userId)
4. What should be shown on the frontend vs what must stay in backend
5. Quality bar for this feature

Keep it practical and security-focused.

## Response snapshot

Updated `.specify/memory/constitution.md` with:
- New Day 19 Connection Architecture section
- Version bump 1.6.0 → 1.7.0 (MINOR)
- Last Amended date: 2026-08-25
- Sync Impact Report added at top
- Compliance checklist expanded with 7 connection-specific checks

## Outcome

- ✅ Impact: Constitution updated with connection architecture rules
- 🧪 Tests: N/A (constitution documentation)
- 📁 Files: .specify/memory/constitution.md
- 🔁 Next prompts: spec, plan, tasks for connection-architecture feature
- 🧠 Reflection: Day 19 constitution focuses on token security and user isolation for connections

## Evaluation notes (flybook)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
