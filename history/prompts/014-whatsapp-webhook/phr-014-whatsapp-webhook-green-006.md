---
id: phr-014-whatsapp-webhook-green-006
title: US5 Ownership & Security Slice
stage: green
date: 2026-08-28
surface: cli
model: opencode/big-pickle
feature: whatsapp-webhook
branch: 014-whatsapp-webhook
user: user
command: /sp.green
labels: [green, day23, whatsapp-webhook, ownership, isolation, session-fix]
links:
  spec: specs/014-whatsapp-webhook/spec.md
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - backend/tests/test_user_isolation.py
  - backend/tests/test_webhooks.py
  - specs/014-whatsapp-webhook/tasks.md
tests:
  - backend/tests/test_user_isolation.py (2 webhook ownership reworks + 5 shape fixes)
  - backend/tests/test_webhooks.py (2 new US5 tests, 16 total)
  - backend/tests/ (FULL SUITE 89 passed / 0 failed — first fully green run)
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

Implemented the User Story 5 slice (T027-T030) after user confirmation. This
closed the last 7 suite failures — the backend test suite is now FULLY GREEN
(89 passed / 0 failed).

- T027 (rework): `test_webhook_message_scoped_to_authenticating_user` and
  `test_webhook_tasks_scoped_to_authenticating_user` now follow the real flow:
  register user A → `POST /connections {"provider":"whatsapp"}` → deliver a
  **signed** Meta payload → assert A sees the message/tasks and B sees none.
  Added local `_meta_payload` / `_signed_webhook` / `_connect_whatsapp` class
  helpers (module-level `TEST_SECRET` env so the signature gate accepts). The
  tasks test patches `services.webhook_ingest.analyze_message` with a fake that
  ALSO inserts the extracted task doc (mirroring what the real analyzer does),
  so the "landed under the owner" assertion is meaningful.
- T028/T029 (new, locked green): signed payload with no connected whatsapp
  connection → 200 ack, nothing stored; signed payload with a foreign
  `metadata.phone_number_id` → 200 ack, nothing stored. Both confirm the
  ownership logic shipped in T016 (no-tamper, payload-independent)
- T030 (verify-only): owner resolution + phone_number_id filter already in
  `backend/routes/webhooks.py` from US1; pinned by T027-T029.
- Also fixed the 5 remaining pre-existing failures in the same file that were
  unrelated shape bugs: `GET /messages` now returns `{"messages":[...]}`
  (5 call sites updated from `.json()` to `.json()["messages"]`).

Verification: `tests/test_user_isolation.py` + `tests/test_webhooks.py` →
36/36 green; full suite → 89 passed / 0 failed (was 80/7 before this slice).

## Outcome

- ✅ Impact: Every webhook message is attributed server-side to the owning
  WhatsApp connection and is invisible to other accounts; edge deliveries
  (no connection, wrong number) are harmlessly acknowledged. Suite green.
- 🧪 Tests: 2 reworked + 5 fixed + 2 new; 89 passed / 0 failed.
- 📁 Files: backend/tests/test_user_isolation.py (helpers, rework, shape
  fixes), backend/tests/test_webhooks.py (+T028/T029), tasks.md (T027-T030 [X]).
- 🔁 Next prompts: after confirmation, Phase 8 polish (T031 full-suite verify
  is effectively already done, T032 standalone scripts, T033 manual real-message
  run — blocked on the user's real Meta App Secret, T034 constitution check).
- 🧠 Reflection: truthful sequencing note — T030's "implementation" already
  existed (T016 shipped it early because US1 could not persist without a
  `user_id`); T027-T029 are the tests that harden and prove it. The 5 shape
  bugs were stale dashboard-contract artifacts, fixed inline while editing the
  same file rather than deferring them to the polish phase.

## Evaluation notes (flywheel)

- Failure modes observed: first green attempt still risked a real Groq call in
  the message-scope test (background analyzer wasn't patched there) — caught by
  review and the webhook-path fake added; tasks fake must replicate the DB side
  effect or the tasks-scoping assertion is vacuous.
- Graders run and results (PASS/FAIL): PASS — 36/36 targeted, 89/89 full suite,
  tasks T027-T030 [X].
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Phase 8 polish after user
  confirmation (T031 done in effect; T032/T033 pending user's real Meta secret;
  T034 constitution re-check).