---
id: phr-014-whatsapp-webhook-tasks-001
title: Day 23 WhatsApp Webhook Tasks
stage: tasks
date: 2026-08-28
surface: cli
model: opencode/big-pickle
feature: whatsapp-webhook
branch: 014-whatsapp-webhook
user: user
command: /sp.tasks
labels: [tasks, day23, whatsapp-webhook, ingestion, deduplication]
links:
  spec: specs/014-whatsapp-webhook/spec.md
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - specs/014-whatsapp-webhook/tasks.md
tests:
  - N/A (test tasks codified; none run at plan/tasks stage)
---

## Prompt

Create a clear and actionable task list for Day 23 – Real WhatsApp Webhook.

### Context
- Project: Communication AI
- Day 22 setup is complete (Meta, ngrok, webhook verified)
- Fake WhatsApp endpoint already exists
- Now we need to receive real messages from WhatsApp Business Cloud API

### Goal:
When a real WhatsApp message arrives:
WhatsApp → Webhook → FastAPI → Validate → Normalize → MongoDB → AI → Dashboard

### Important:
- Convert Meta payload into normalized format
- Prevent duplicate messages using externalMessageId
- Keep fake simulation still working
- Messages must belong to the correct user

### Focus Areas:
- Update webhook to handle real Meta POST payload
- Extract sender, message text, and message ID
- Normalize the data
- Save to MongoDB
- Trigger existing AI pipeline
- Test with real WhatsApp message

### Requirements for the task list:
- Break work into small, clear, executable tasks
- Group tasks logically (Webhook, Normalization, Database, Testing)
- Write tasks in action language
- Include acceptance criteria
- Keep it simple and reliable

Save the file in the appropriate location.

## Response snapshot

Created `specs/014-whatsapp-webhook/tasks.md` on branch `014-whatsapp-webhook`:

- 34 tasks in 8 phases: Setup (2), Foundational (3), one phase per user story
  (US2 P1=6, US1 P1=6, US3 P2=5, US4 P2=3, US5 P2=4), Polish (4).
- Organized by the 5 spec user stories; each story has Goal, Independent
  Test, tests-first FAIL checklist, implementation tasks, and a checkpoint.
- Contract→story mapping table (GET/POST webhook→US2/US1, simulate→US3,
  dedup→US4, ownership→US5).
- Foundational phase (Phase 2) = shared `services/webhook_ingest.py`
  + partial unique index on `external_message_id` + MessageResponse optional
  fields — blocks all stories.
- All task lines validated against the strict format via regex:
  34/34 match `- [ ] T\d{3} [P?] [US?] Description with file path`, IDs unique
  and sequential 1-34, and every line includes an exact file path.
- Decision logged: US2 (security gate) precedes US1 (MVP journey) in the
  execution order; same-file coordination note for `backend/routes/webhooks.py`
  (do not parallelize within it); [P] flags only on genuinely different files.

## Outcome

- ✅ Impact: Immediately executable task list mapped 1:1 to the spec's user
  stories and plan.md's 10 implementation steps, with MVP scope = Setup +
  Foundational + US2 + US1 and per-phase acceptance criteria.
- 🧪 Tests: Test tasks included (spec mandates testable scenarios; plan Step
  8-9 specifies the pytest matrix) — 13 test tasks written-first across the
  five stories; not run yet (tasks stage).
- 📁 Files: specs/014-whatsapp-webhook/tasks.md
- 🔁 Next prompts: /sp.red for User Story 2 tests → implementation, then the
  remaining stories in priority order.
- 🧠 Reflection: Keeping US1 (parse/store) separable from US2 (verify) while
  sharing one route file required a deliberate sequencing rule (US2 before
  US1, same file not parallelized). Duplicate-inside-ingest and the auth
  audit (`test_auth.py` PUBLIC_ROUTES) are captured as explicit tasks so the
  security invariant cannot silently regress.

## Evaluation notes (flywheel)

- Failure modes observed: No create-phr script exists on Windows (bash+ps1
  variants absent) — PHR written agent-natively per the fallback path in the
  outline, matching the spec/plan PHR conventions already in the feature dir.
- Graders run and results (PASS/FAIL): PASS — 34/34 tasks pass the strict
  checklist regex (checkbox, sequential unique ID, optional [P], required
  [USn] for story phases, description with file path); no placeholders.
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A