---
id: phr-014-whatsapp-webhook-spec-001
title: Day 23 Real WhatsApp Webhook Spec
stage: spec
date: 2026-08-28
surface: cli
model: opencode/big-pickle
feature: whatsapp-webhook
branch: 014-whatsapp-webhook
user: user
command: /sp.specify
labels: [spec, day23, whatsapp-webhook, normalization, ingestion]
links:
  spec: specs/014-whatsapp-webhook/spec.md
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - specs/014-whatsapp-webhook/spec.md
  - specs/014-whatsapp-webhook/checklists/requirements.md
tests:
  - N/A
---

## Prompt

Create a clear and focused specification for Day 23 – Real WhatsApp Webhook.

### Context
- Project: Communication AI
- Day 22 setup is complete (Meta App, ngrok, webhook verified)
- We currently have a fake WhatsApp endpoint
- Now we need to receive real messages from WhatsApp Business Cloud API

### Goal:
When a real WhatsApp message is sent to the test number, it should:
1. Arrive at our webhook
2. Be validated
3. Be converted into a normalized format
4. Be saved in MongoDB
5. Go through the AI pipeline
6. Appear on the Dashboard

### Normalized Message Format (Very Important):
{
  "userId": "...",
  "source": "whatsapp",
  "sender": "Ali",
  "content": "Send me the slides tonight.",
  "receivedAt": "...",
  "externalMessageId": "..."
}

### Requirements:
- Support both GET (verification) and POST (incoming messages)
- Validate the request properly
- Extract useful data from Meta's webhook payload
- Prevent duplicate messages using externalMessageId
- Keep the fake simulation still working
- Only save messages for the correct user

### Please include in the specification:
1. Feature Overview
2. Incoming message flow
3. Normalized data format
4. Validation rules
5. Acceptance Criteria
6. Edge cases (duplicate messages, invalid payload, etc.)

Keep it practical and clean for a university FYP.

## Response snapshot

Created spec on branch `014-whatsapp-webhook` with:
- specs/014-whatsapp-webhook/spec.md — Feature Overview (goal + flow),
  Incoming Message Flow (7-step pipeline), Normalized Message Format (JSON +
  field table), Validation Rules (6 rules), 5 prioritized User Stories with
  acceptance scenarios, 12 Edge Cases, 15 Functional Requirements, Key
  Entities, 8 measurable Success Criteria, Assumptions, Out of Scope.
- specs/014-whatsapp-webhook/checklists/requirements.md — Quality checklist
  with all items PASS.
- No [NEEDS CLARIFICATION] markers required.
- Branch and prompts directory created by create-new-feature.ps1 (PowerShell
  5.1 Join-Path failure on the multi-child history path worked around by
  creating history/prompts/014-whatsapp-webhook/ manually).

## Outcome

- ✅ Impact: Full Day 23 spec written; source-agnosticity is the anchoring
  principle (normalized format first, provider-specific parsing confined to
  the webhook boundary).
- 🧪 Tests: N/A (specification stage)
- 📁 Files: specs/014-whatsapp-webhook/spec.md,
  specs/014-whatsapp-webhook/checklists/requirements.md
- 🔁 Next prompts: /sp.plan for whatsapp-webhook
- 🧠 Reflection: Aligned the spec one-to-one with the Day 23 constitution
  section (signature-first validation, dedup on externalMessageId,
  respond-fast-then-process-async, server-side user resolution, simulation
  parity). Story priorities keep the MVP slice independently demoable.

## Evaluation notes (flywheel)

- Failure modes observed: Create-new-feature.ps1 failed on PowerShell 5.1
  `Join-Path` with 3+ child paths after branch creation; worked around
  manually (spec + prompts dir).
- Graders run and results (PASS/FAIL): PASS — no placeholders, no trailing
  whitespace, all mandatory sections present, checklist fully marked
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A