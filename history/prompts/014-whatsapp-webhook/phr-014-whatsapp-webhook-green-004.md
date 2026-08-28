---
id: phr-014-whatsapp-webhook-green-004
title: US3 Simulation Parity Slice
stage: green
date: 2026-08-28
surface: cli
model: opencode/big-pickle
feature: whatsapp-webhook
branch: 014-whatsapp-webhook
user: user
command: /sp.green
labels: [green, day23, whatsapp-webhook, simulate, parity]
links:
  spec: specs/014-whatsapp-webhook/spec.md
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - backend/routes/webhooks.py
  - backend/services/webhook_ingest.py
  - backend/models/message.py
  - backend/tests/test_webhooks.py
  - components/SimulateMessage.tsx
  - specs/014-whatsapp-webhook/tasks.md
tests:
  - backend/tests/test_webhooks.py (3 new US3 tests, 12 total green)
  - backend/tests/ (full suite 78 passed / 7 pre-existing-deferred)
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

Implemented the User Story 3 slice (T018-T022) after user confirmation —
simulation parity: the debug endpoint now runs the identical normalize→ingest→
AI pipeline as real traffic, but authenticated and tagged `source="simulate"`.

- T018/T019/T020 (RED first): added `_simulate_post` and three tests:
  ingress-with-source, 401 anonymous, and parity (simulated vs signed real
  message with the same text → identical `ai_analysis`). RED confirmed on the
  missing route (404).
- T021 (GREEN): added `SimulateMessageRequest {sender, message}` to
  `backend/models/message.py` and authenticated `POST /webhooks/simulate` in
  `backend/routes/webhooks.py` (`Depends(get_current_user)`), calling the same
  `ingest_message(user_id, source="simulate", ...)` and returning the stored
  message response via `message_doc_to_response`.
- **Bug found + fixed while writing T020**: the webhook ingest path scheduled
  `analyze_message` as a background task but never persisted its result to the
  message document — the dashboard would have had ZERO AI summaries/priorities
  for webhook messages. Added `_analyze_and_store` in
  `backend/services/webhook_ingest.py` that awaits `analyze_message` (which
  still creates extracted tasks internally) and `$set`s `ai_analysis` on the
  message, mirroring how `POST /messages` persists it.
- T022: `components/SimulateMessage.tsx` now POSTs to `/webhooks/simulate`;
  `npx eslint` clean, `npx tsc` shows only pre-existing test-file errors.

Verification: `tests/test_webhooks.py` → 12/12 green; full suite → 78 passed /
7 failed (all deferred User Story 5 `test_user_isolation.py` items). Zero new
failures.

## Outcome

- ✅ Impact: The simulate flow is now a faithful stand-in for real WhatsApp —
  parity proven by test — with 401 auth, `source="simulate"` tagging, and a
  working AI pipeline that actually persists results to stored messages.
- 🧪 Tests: 3 new US3 tests RED→GREEN; 12/12 webhook tests; full regression
  78 passed / 7 deferred.
- 📁 Files: backend/routes/webhooks.py (+/simulate), backend/services/webhook_
  ingest.py (_analyze_and_store), backend/models/message.py (+SimulateMessage
  Request), backend/tests/test_webhooks.py (+3), components/SimulateMessage.tsx
  (target), tasks.md (T018-T022 [X]).
- 🔁 Next prompts: after confirmation, User Story 4 (sample dashboard rows);
  US5 will re-verify ownership edge cases and rework the 7 remaining isolation
  tests.
- 🧠 Reflection: the parity test surfaced a real functional gap (analysis never
  persisted) that the earlier smoke tests missed because they only checked
  storage/acks. Writing the opposing-path parity test was the cheap safety net;
  a future iteration could assert the full `ai_analysis` body equality, not just
  priority/summary.

## Evaluation notes (flywheel)

- Failure modes observed: T020's failed assertion was the stub returning without
  persisting — the stub is faithful only if it mimics the real pipeline's DB
  write, which the wrapper now owns.
- Graders run and results (PASS/FAIL): PASS — 3/3 US3 tests RED→GREEN (1 debug
  run needed), 12/12 webhook, 78 passed / 7 deferred, eslint clean, tsc
  unchanged, tasks T018-T022 [X].
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): User Story 4 (sample dashboard
  rows) after user confirmation.