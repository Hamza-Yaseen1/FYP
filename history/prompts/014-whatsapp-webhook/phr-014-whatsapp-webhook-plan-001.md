---
id: phr-014-whatsapp-webhook-plan-001
title: Day 23 Real WhatsApp Webhook Plan
stage: plan
date: 2026-08-28
surface: cli
model: opencode/big-pickle
feature: whatsapp-webhook
branch: 014-whatsapp-webhook
user: user
command: /sp.plan
labels: [plan, day23, whatsapp-webhook, ingestion, deduplication]
links:
  spec: specs/014-whatsapp-webhook/spec.md
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - specs/014-whatsapp-webhook/plan.md
  - specs/014-whatsapp-webhook/research.md
  - specs/014-whatsapp-webhook/data-model.md
  - specs/014-whatsapp-webhook/contracts/webhook-api.md
  - specs/014-whatsapp-webhook/quickstart.md
tests:
  - N/A
---

## Prompt

Create a technical implementation plan for Day 23 – Real WhatsApp Webhook.
Plan Phase only (not the implementation tasks).

### Please include in the plan:
1. Goal of this phase
2. Technical approach
3. How to handle Meta's real webhook payload
4. How to convert it into a normalized format
5. How to prevent duplicate messages
6. Files that need to be updated
7. Implementation steps in order
8. Testing plan (using real WhatsApp message)
9. Definition of Done

## Response snapshot

Created the Day 23 plan on branch `014-whatsapp-webhook`:

- specs/014-whatsapp-webhook/plan.md — Summary + architecture; Technical
  Context; Constitution Check gate (13 rows, all PASS); Project/Source
  structure; Structure Decision; Technical Approach (8 decisions); 10 ordered
  Implementation Steps with checkpoints; Testing Plan (pytest matrix + real
  WhatsApp runbook); Definition of Done (11 items). Design core: ONE shared
  ingest service (`services/webhook_ingest.py`) normalizes both real and
  simulated messages; `POST /webhooks/whatsapp` becomes public but
  signature-gated (X-Hub-Signature-256 vs WHATSAPP_APP_SECRET); dedup by
  partial unique index on `external_message_id`; ownership resolved from the
  connected whatsapp connection; AI moved to a background task; new authed
  `POST /webhooks/simulate` keeps simulation working.
- specs/014-whatsapp-webhook/research.md — Phase 0: Meta delivery mechanics,
  signature-verification approach, parse-then-normalize mapping, idempotence
  via partial unique index, ownership resolution, background AI, simulation
  migration; risks table with mitigations; no blockers.
- specs/014-whatsapp-webhook/data-model.md — Phase 1: normalized `messages`
  document (adds `message_type`, `external_message_id`, `received_at`),
  partial unique index DDL + rationale, response-surface changes (optional
  fields in MessageResponse), hard requirements.
- specs/014-whatsapp-webhook/contracts/webhook-api.md — Phase 1: GET verify
  (unchanged), POST delivery (signature 403, parse, phone_number_id filter,
  ownership, 200-ack, normalized mapping), new POST /webhooks/simulate,
  env vars, change log vs Day 22.
- specs/014-whatsapp-webhook/quickstart.md — Phase 1: App Secret setup,
  index creation, ngrok + portal re-verification, 8-step real-message test
  flow incl. signed PowerShell curl and dedup/idempotence checks,
  troubleshooting table.
- Ran `.specify/scripts/powershell/update-agent-context.ps1 -AgentType
  opencode`. Script no-oped (AGENTS.md lacked its `## Active Technologies`
  / `## Recent Changes` markers), so those sections were appended manually to
  AGENTS.md to match the template the script maintains.

## Outcome

- ✅ Impact: Plan answers all 9 requested items; design keeps the Day 22
  verification GET intact, makes the delivery POST idempotent and safe, and
  preserves simulation through the same normalized path.
- 🧡 Design decisions documented: signature-first 403; external_message_id
  partial unique index; server-side ownership from connections; respond-200
  then background AI; simulate → /webhooks/simulate; `message_type`
  text/media collapse; phone_number_id owner filter.
- 🧪 Tests: NOT executed — plan stage only (test matrix specified in Step 9
  and the real-message runbook).
- 📁 Files: 5 plan artifacts under specs/014-whatsapp-webhook/ (plan,
  research, data-model, contracts, quickstart) + AGENTS.md context sections.
- 🔁 Next prompts: /sp.tasks to convert Step 1-10 into the task list,
  then implementation.
- 🧠 Reflection: The pivotal discovery was that the current `POST
  /webhooks/whatsapp` is JWT-authed and expects the fake flat payload, so a
  naive swap would break simulation AND the meta delivery. Segregating
  simulate into its own authed route while sharing one ingest function is the
  minimal, testable answer. Environment audit surfaced the missing
  WHATSAPP_APP_SECRET — without it signature verification is impossible.

## Evaluation notes (flywheel)

- Failure modes observed: update-agent-context.ps1 reported success but
  wrote nothing because AGENTS.md contains only the nextjs block; detected via
  `git status`/`git diff` and fixed by appending the standard sections.
- Graders run and results (PASS/FAIL): PASS — plan filled (no template
  placeholders), Constitution Check all-PASS gate, Phase 0-1 artifacts
  present, agent context updated, PHR follows spec PHR conventions
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A