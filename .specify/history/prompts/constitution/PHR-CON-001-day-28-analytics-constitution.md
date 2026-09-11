---
id: PHR-CON-001
title: Day 28 Analytics Constitution
stage: constitution
date: 2026-09-11
surface: cli
model: opencode/big-pickle
feature: 019-analytics
branch: main
user: user
command: constitution
labels: [constitution, analytics, day-28, minor-bump]
links:
  spec: TODO
  ticket: TODO
  adr: N/A
  pr: TODO
files:
  - .specify/memory/constitution.md
tests: []
---

## Prompt

Create a focused constitution for Day 28 – Analytics.

### Context
- Project: Communication AI (FYP)
- Dashboard, Inbox, Tasks, and Cross-Platform views are already working
- Messages come from WhatsApp and Gmail with AI priority analysis
- Now we want to add a professional Analytics section

### Goal of Day 28:
Add a clean Analytics / Communication Overview section.

Example:
Communication Overview – This Week

Total Communications       247
Urgent                      12
Important                   38
Normal                     151
Low Priority                46

Charts:
- Communications by source (WhatsApp vs Gmail)
- Priority distribution
- Tasks completed
- Response / attention trends

### Principles:
- Keep analytics simple and useful
- Only show data of the logged-in user
- Numbers must be accurate and based on real data
- Design should stay clean (no unnecessary complexity)
- Make the FYP look more professional

### Please create a short constitution that covers:
1. Purpose of the Analytics feature
2. Core principles for good analytics
3. What metrics should be shown
4. Rules for data accuracy and privacy
5. Quality bar for this feature

Keep it practical and suitable for a university FYP.

## Response snapshot

Updated `.specify/memory/constitution.md` from v1.16.0 to v1.17.0 (MINOR). Added a
complete Day 28 Analytics section covering: purpose, 5 core analytics principles,
metrics definitions (summary cards + 4 chart types), Analytics API contract with
JSON schema, 7 MUST-NOT prohibitions, and a 9-point quality bar. Added 4 compliance
checklist items. Updated Sync Impact Report and version footer.

## Outcome

- ✅ Impact: MINOR version bump (1.16.0 → 1.17.0) — new section added
- 🧪 Tests: N/A (constitution only)
- 📁 Files: `.specify/memory/constitution.md`
- 🔁 Next prompts: spec, plan, tasks for 019-analytics
- 🧠 Reflection: Analytics constitution follows established pattern — purpose, principles, contract, MUST-NOT, quality bar — consistent with Days 22–27 sections

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
