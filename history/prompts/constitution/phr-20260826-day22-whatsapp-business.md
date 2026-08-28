---
id: phr-constitution-day22-001
title: Day 22 WhatsApp Business Integration Constitution
stage: constitution
date: 2026-08-26
surface: cli
model: opencode/big-pickle
feature: whatsapp-business-integration
branch: main
user: user
command: constitution
labels: [constitution, day22, whatsapp-business, cloud-api, security, research]
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

Create a focused constitution for Day 22 – WhatsApp Business Integration Research + Setup.

### Context
- Project: Communication AI (FYP)
- We currently have a fake WhatsApp webhook
- Now we are moving toward real WhatsApp Business Platform integration

### Goal of Day 22:
Research and set up the official WhatsApp Business integration using Meta Developer Platform.

Important rules:
- Do NOT try to read personal WhatsApp notifications
- Only use official WhatsApp Business Platform (Cloud API)
- This is a research + setup day (not full implementation yet)

### Please create a short constitution that covers:
1. Purpose of real WhatsApp integration
2. Official & allowed approach only
3. Security and privacy principles
4. What we should set up today (Meta Developer, Webhook, Credentials)
5. What we should NOT do
6. Quality bar for this phase

Keep it practical, clear, and security-focused.

## Response snapshot

Updated `.specify/memory/constitution.md` with:
- New Day 22 WhatsApp Business Integration Research + Setup section
- Version bump 1.9.0 → 1.10.0 (MINOR)
- Last Amended date: 2026-08-26
- Sync Impact Report updated at top
- Sections: purpose, official approach, security/privacy, setup scope table, prohibitions, quality bar

## Outcome

- ✅ Impact: Constitution updated with WhatsApp Business integration rules
- 🧪 Tests: N/A (constitution documentation)
- 📁 Files: .specify/memory/constitution.md
- 🔁 Next prompts: spec, plan, tasks for whatsapp-business-integration feature
- 🧠 Reflection: Day 22 constitution emphasizes official Cloud API only, credential security, webhook verification, and clear scope boundaries for research day

## Evaluation notes (flybook)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
