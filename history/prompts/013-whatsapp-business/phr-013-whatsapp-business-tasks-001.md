---
id: phr-013-whatsapp-business-tasks-001
title: WhatsApp Business Integration Tasks
stage: tasks
date: 2026-08-26
surface: cli
model: opencode/big-pickle
feature: 013-whatsapp-business
branch: 013-whatsapp-business
user: user
command: tasks
labels: [tasks, whatsapp-business, cloud-api, day22, setup, research]
links:
  spec: ../specs/013-whatsapp-business/spec.md
  plan: ../specs/013-whatsapp-business/plan.md
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - specs/013-whatsapp-business/tasks.md
tests:
  - N/A
---

## Prompt

Create a clear and actionable task list for Day 22 – WhatsApp Business Integration Research + Setup.

### Context
- Project: Communication AI
- We currently use a fake WhatsApp webhook
- Now we are preparing for real WhatsApp Business Cloud API

### Goal of Day 22:
This is mainly a setup day. Focus on research and configuration, not full message receiving yet.

### Main Tasks should cover:
- Create Meta Developer App
- Add WhatsApp product
- Collect Phone Number ID, Access Token, and Business Account ID
- Install and run ngrok
- Configure webhook in Meta Developer
- Verify webhook successfully
- Store credentials securely in .env
- Document the required values

### Requirements for the task list:
- Break work into small, clear, executable tasks
- Separate Manual Setup tasks and Code/Config tasks
- Write tasks in action language
- Include acceptance criteria
- Keep it practical for a university FYP

Save the file in the appropriate location.

## Response snapshot

Generated `specs/013-whatsapp-business/tasks.md` with:
- 37 tasks organized across 6 phases
- Phase 1: Setup (13 manual browser tasks — Meta portal, credentials, ngrok)
- Phase 2: Foundational (3 code tasks — GET verification endpoint)
- Phase 3: US3 Webhook Verification (6 tasks — portal config + test message)
- Phase 4: US4 Credential Security (4 tasks — gitignore, hardcoded search, runtime check)
- Phase 5: US5 Message Flow Docs (7 tasks — research documentation)
- Phase 6: Polish (4 tasks — test suite, code review, log audit)
- MVP scope: Phase 1 → Phase 2 → Phase 3 (webhook verified, test message received)
- Dependencies documented; parallel opportunities identified

## Outcome

- ✅ Impact: Complete task list ready for execution
- 🧪 Tests: N/A (setup + research day; no test tasks requested)
- 📁 Files: specs/013-whatsapp-business/tasks.md
- 🔁 Next prompts: Execute tasks, then `/sp.green` or continue to Day 23
- 🧠 Reflection: Most Day 22 tasks are manual (browser-based) — limited automation possible. Code tasks are minimal: one GET endpoint + credential storage.

## Evaluation notes (flybook)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
