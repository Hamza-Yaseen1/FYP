---
id: phr-014-whatsapp-webhook-green-003
title: US1 Real Message Ingestion Slice
stage: green
date: 2026-08-28
surface: cli
model: opencode/big-pickle
feature: whatsapp-webhook
branch: 014-whatsapp-webhook
user: user
command: /sp.green
labels: [green, day23, whatsapp-webhook, ingestion, normalization]
links:
  spec: specs/014-whatsapp-webhook/spec.md
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - backend/routes/webhooks.py
  - backend/tests/test_webhooks.py
  - backend/tests/conftest.py
  - specs/014-whatsapp-webhook/tasks.md
tests:
  - backend/tests/test_webhooks.py (4 new, 9 total green)
  - backend/tests/ (full suite 75 passed / 7 pre-existing-deferred)
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

Implemented the User Story 1 vertical slice (T012-T017) — the real ingestion
journey — after the user confirmed the US2 checkpoint.

- T012-T015 (RED first): added `_register_with_whatsapp`, `_signed_post`
  helpers and a `_fake_ai` fixture (patches
  `services.webhook_ingest.analyze_message` so tests never hit Groq) to
  `backend/tests/test_webhooks.py`. RED confirmed (3 failed on missing
  storage, 1 already-green non-message test).
- T016/T017 (GREEN): `backend/routes/webhooks.py` POST now parses the verified
  envelope and for every `messages[]` event extracts `sender`
  (`contacts[0].profile.name` else `from`), `content` (guarded `text.body`,
  empty for media), `message_type` (`text`/`media`), and `external_message_id`
  (`messages[].id`), then calls the shared `ingest_message(...,
  source="whatsapp", background_tasks=background_tasks)`. Owner is resolved
  server-side (`connections` where provider=whatsapp, status=connected) and
  the payload's `metadata.phone_number_id` must equal
  `WHATSAPP_PHONE_NUMBER_ID` — otherwise the delivery is acknowledged and
  skipped. Returns `{"status": "ok"}` after the loop; AI runs as a background
  task post-response.
- `backend/tests/conftest.py`: added `connections` to the clean lists (they
  are now part of ingestion and leaked between tests otherwise).

Verification: `python -m pytest tests/test_webhooks.py` → 9/9 green; full
suite → 75 passed / 7 failed, where the 7 are the known deferred
`test_user_isolation.py` items (5 legacy response-shape bugs + 2 webhook
ownership tests, scheduled for US5/T027). Zero new failures.

Note: the server-side owner resolution + phone_number_id filter were pulled
into T016 because ingestion cannot store a useful document without a
`user_id`; US5 (T030) will harden them with dedicated edge tests (no
connection / wrong number) and mark the implementation as verified.

## Outcome

- ✅ Impact: A real signed Meta text/media/batched delivery now stores
  normalized documents under the correct owner, scheduled for AI analysis
  after the fast 200 acknowledgement — the MVP dashboard journey is wired.
- 🧪 Tests: 4 new US1 tests green; full suite regression-checked (75 passed,
  7 pre-existing/deferred).
- 📁 Files: backend/routes/webhooks.py (parse/normalize/ingest), backend/tests/
  test_webhooks.py (+4), backend/tests/conftest.py (connections cleanup),
  tasks.md (T012-T017 [X]).
- 🔁 Next prompts: after confirmation, US3 (simulate parity) — and note US5
  T030's tests will re-verify the ownership logic already in place.
- 🧠 Reflection: I consciously used the real ownership resolution inside US1
  instead of leaving `user_id` unresolved, since a vertical slice's output
  (dashboard card for the owner) is impossible otherwise. Kept the
  phone_number_id filter in the same pass to avoid revisiting the handler in
  US5.

## Evaluation notes (flywheel)

- Failure modes observed: none new this slice; kept aware that TestClient
  executes background tasks synchronously before the test returns, so the
  `_fake_ai` stub is what keeps tests fast and deterministic.
- Graders run and results (PASS/FAIL): PASS — 4/4 new tests RED→GREEN, 9/9
  webhook tests green, 0 new suite failures, tasks T012-T017 [X].
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): User Story 3 (simulate parity)
  after user confirmation.