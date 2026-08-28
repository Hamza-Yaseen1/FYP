---
id: phr-014-whatsapp-webhook-green-005
title: US4 Duplicate-Guard Slice
stage: green
date: 2026-08-28
surface: cli
model: opencode/big-pickle
feature: whatsapp-webhook
branch: 014-whatsapp-webhook
user: user
command: /sp.green
labels: [green, day23, whatsapp-webhook, dedup, external-message-id]
links:
  spec: specs/014-whatsapp-webhook/spec.md
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - backend/tests/test_webhooks.py
  - backend/test_attention_pipeline.py
  - specs/014-whatsapp-webhook/tasks.md
tests:
  - backend/tests/test_webhooks.py (2 new US4 tests, 14 total green)
  - backend/test_attention_pipeline.py (unit part 9/9 green; integration part signed)
  - backend/tests/ (full suite 80 passed / 7 pre-existing-deferred)
---

## Prompt

Start implementing the tasks for Day 23 – Real WhatsApp Webhook.

Follow the tasks.md file.

Focus on:
- Updating the webhook to receive real messages from Meta (WhatsApp Cloud API)
- Validating the incoming payload
- Converting it into the normalized message format
- Saving it to MongoDB with userId and externalMessageId
- Preventing duplicate messages
- Triggering the existing AI pipeline
- Keeping the fake simulation still working

Keep everything simple and reliable.
Implement one vertical slice at a time.
After finishing the current group of tasks, stop and wait for my confirmation.

## Response snapshot

Implemented the User Story 4 slice (T023-T026) after user confirmation —
duplicate deliveries collapse to one document and never re-analyze.

- T023: `test_post_duplicate_external_id_single_document` — the same signed
  Meta payload delivered twice → both 200 `{"status":"ok"}` and exactly one
  doc for `external_message_id="wamid.DUP1"`. Green immediately (regression
  lock: dedup was already implemented by the ingest service in T003 and used
  through US1/US3).
- T024: `test_duplicate_does_not_reanalyze` — a capture-spy on
  `services.webhook_ingest.analyze_message` asserts exactly ONE call across
  two deliveries of the same `messages[].id` (the duplicate branch returns the
  existing id before `background_tasks.add_task` is reached).
- T025: rewrote the standalone `backend/test_attention_pipeline.py` duplicate-
  guard integration test from the obsolete `{sender, message, timestamp}`
  double-POST into two **signed** Meta envelopes sharing the same
  `messages[].id`, plus the new contract: register a throwaway user (session
  cookie), deliver twice, `GET /messages` filtered by `external_message_id`,
  assert a single document with `ai_analysis.status == "completed"`. It now
  refuses to run with a clear RuntimeError if `WHATSAPP_APP_SECRET` /
  `WHATSAPP_PHONE_NUMBER_ID` are not configured.
- T026: verified (no code needed) — `webhook_ingest.py` `DuplicateKeyError`
  path returns the existing id and never schedules `analyze_message`;
  duplicates are 200-acknowledged and logged in `webhooks.py`.

Verification: `tests/test_webhooks.py` → 14/14 green; unit part of
`test_attention_pipeline.py` → 9/9 (integration part runs live after the user
pastes the App Secret); full suite → 80 passed / 7 failed (all deferred US5
isolation items). Zero new failures.

## Outcome

- ✅ Impact: Meta's at-least-once delivery semantics are safe — a duplicate
  resend (same wamid) cannot create ghost messages or burn LLM quota by re-
  analyzing. Proven at the signed-flow level, not just the old fake path.
- 🧪 Tests: 2 new US4 tests (locked green), 14/14 webhook, 80 passed / 7
  deferred.
- 📁 Files: backend/tests/test_webhooks.py (+2), backend/test_attention_pipeline
  .py (signed contract), tasks.md (T023-T026 [X]).
- 🔁 Next prompts: after confirmation, User Story 5 (ownership + security
  hardening) — which will also rework the 7 remaining isolation failures.
- 🧠 Reflection: T025's earlier `{sender, message, timestamp}` shape was a
  Day-14 artifact that the signature gate would 403; the rewrite keeps the
  manual integration script meaningful and directly exercises the dedup index
  under real signed traffic. The already-in-place dedup meant T023/T024 were
  lock-in tests rather than RED→GREEN — honest note on that in the evaluation
  below.

## Evaluation notes (flywheel)

- Failure modes observed: none new. `test_attention_pipeline.py` imports were
  missing `json` (added); its integration path is intentionally latent until
  the user configures the App Secret.
- Graders run and results (PASS/FAIL): PASS — 2/2 US4 tests green, 14/14
  webhook tests, unit part 9/9, syntax ok, full regression 80 passed / 7
  deferred, tasks T023-T026 [X]. (T023/T024 were green-on-first-run regression
  locks, since dedup shipped earlier in the slice plan.)
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): User Story 5 (ownership +
  security, incl. the 7 isolation reworks) after user confirmation.