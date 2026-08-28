---
id: phr-constitution-day23-001
title: Day 23 Real WhatsApp Webhook Constitution
stage: constitution
date: 2026-08-28
surface: cli
model: opencode/big-pickle
feature: whatsapp-webhook
branch: 013-whatsapp-business
user: user
command: constitution
labels: [constitution, day23, whatsapp-webhook, normalization, security, ingestion]
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

Create a focused constitution for Day 23 – Real WhatsApp Webhook.

### Context
- Project: Communication AI (FYP)
- Day 22 setup is complete (Meta Developer, ngrok, webhook verified)
- We currently have a fake WhatsApp endpoint
- Now we will make the webhook receive real messages from WhatsApp Business
  Cloud API

### Goal of Day 23:
Turn the existing webhook into a real ingestion endpoint.

Architecture:
WhatsApp → Webhook → FastAPI → Validate → MongoDB → AI Pipeline → Dashboard

### Very Important Architecture Principle:
Create a normalized communication format so the AI does not care about the
source.

Example format:
{
  "userId": "...",
  "source": "whatsapp",
  "sender": "Ali",
  "content": "Send me the slides tonight.",
  "receivedAt": "...",
  "externalMessageId": "..."
}

### Please create a short constitution that covers:
1. Purpose of the Real WhatsApp Webhook
2. Normalized message format principle
3. Security & validation rules
4. What should happen when a real message arrives
5. Quality bar for this feature

Keep it practical, clean, and professional.

## Response snapshot

Updated `.specify/memory/constitution.md` with:
- New Day 23 Real WhatsApp Webhook section
- Version bump 1.10.0 → 1.11.0 (MINOR)
- Last Amended date: 2026-08-28
- Sync Impact Report updated at top
- Sections: purpose, normalized message format (source-agnosticity),
  security & validation rules, ingestion flow (7 steps), prohibitions,
  quality bar
- 8 new Compliance Checklist items added for Day 23 requirements

## Outcome

- ✅ Impact: Constitution updated with real WhatsApp webhook ingestion rules;
  normalized communication format principle defined so the AI core remains
  source-agnostic; compliance checklist expanded with 8 webhook-specific
  checks.
- 🧪 Tests: N/A (constitution documentation; no code changed)
- 📁 Files: .specify/memory/constitution.md
- 🔁 Next prompts: spec, plan, tasks for whatsapp-webhook (Day 23) feature
- 🧠 Reflection: The normalization principle is the architectural anchor —
  it shifts per-channel concerns to the ingestion boundary so the AI
  pipeline, storage, and dashboard stay provider-agnostic. Security rules
  (signature-first, idempotence on externalMessageId, respond-fast-then-
  process-async) directly address Meta webhook retry behavior. MINOR bump is
  appropriate because a new section was added with material new guidance.

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): PASS — no bracket tokens remaining,
  version matches report, dates ISO format, principles declarative/testable
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A