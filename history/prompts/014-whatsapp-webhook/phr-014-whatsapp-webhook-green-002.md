---
id: phr-014-whatsapp-webhook-green-002
title: US2 Webhook Verification Slice
stage: green
date: 2026-08-28
surface: cli
model: opencode/big-pickle
feature: whatsapp-webhook
branch: 014-whatsapp-webhook
user: user
command: /sp.green
labels: [green, day23, whatsapp-webhook, signature, security]
links:
  spec: specs/014-whatsapp-webhook/spec.md
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - backend/routes/webhooks.py
  - backend/models/meta_webhook.py
  - backend/tests/test_webhooks.py
  - backend/tests/test_auth.py
  - backend/tests/test_user_isolation.py
  - specs/014-whatsapp-webhook/tasks.md
tests:
  - backend/tests/test_webhooks.py (5 new)
  - backend/tests/test_auth.py (fixed + 5)
  - backend/tests/test_user_isolation.py (removed obsolete patch)
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

Implemented the User Story 2 vertical slice (T006-T011, security gate) after
the user confirmed the foundational checkpoint.

- T006/T007/T008 (RED first): wrote `backend/tests/test_webhooks.py` helper
  (`_signature`, `_meta_object_payload`, `_text_message`) + 5 tests. Ticket:
  3 signature tests failed with 401 (old JWT-gated POST), 2 GET-challenge
  tests passed — RED confirmed.
- T009/T011 (GREEN): rewrote `backend/routes/webhooks.py` — POST is now
  public; `verify_signature()` reads `WHATSAPP_APP_SECRET` lazily, rejects
  when unset, constant-time compare via `hmac.compare_digest`, 403 before any
  parsing; body validated through the new Meta envelope model
  `backend/models/meta_webhook.py` (Pydantic, tolerant of unknown fields),
  400 on malformed; valid deliveries acknowledged `{"status": "ok"}`. GET
  verification unchanged.
- T010: `backend/tests/test_auth.py` — added GET+POST `/webhooks/whatsapp`
  to `PUBLIC_ROUTES` (fixes TestAuthCoverage failing since Day 22); anonymous
  webhook assertion 401 → 403; also opportunistically fixed the pre-existing
  `listing.json()["messages"]` shape bug in
  `test_messages_isolated_between_users`. Deviation from task text (noted in
  tasks.md): the anonymous-401 move to `/webhooks/simulate` was deferred to
  T019 since that route exists only from US3; instead the webhook asserts the
  403 signature gate now.
- Removed the obsolete `monkeypatch.setattr("routes.webhooks.analyze_message",
  ...)` autouse fixture line in `backend/tests/test_user_isolation.py`
  (symbol no longer exists after US2) — this was ERRORing the whole class.

Verification: `python -m pytest tests/` → 71 passed / 7 failed. The 7
remaining failures are all in `test_user_isolation.py` (5 legacy
response-shape bugs + 2 webhook-ownership tests), all scheduled for rework in
T027 (US5). Net vs the pre-Day-23 baseline: 2 pre-existing failures fixed, 0
new failures.

## Outcome

- ✅ Impact: The security gate for real Meta deliveries is in place — no
  unverified or malformed delivery can reach storage; verification challenge
  retained.
- 🧪 Tests: 5 US2 tests green; full suite regression-checked (71 passed, 7
  pre-existing/deferred).
- 📁 Files: backend/routes/webhooks.py (reworked), backend/models/meta_webhook.py
  (new), backend/tests/test_webhooks.py (new), backend/tests/test_auth.py
  (updated), backend/tests/test_user_isolation.py (fixture fix), tasks.md
  (T006-T011 [X]).
- 🔁 Next prompts: /sp.green for User Story 1 (parse/normalize/store + fast
  ack) after user confirmation.
- 🧠 Reflection: Hardest part was not code but test surgery — the removed
  `routes.webhooks.analyze_message` fixture symbol ERRORed the entire
  isolation class, and a botched indent edit twice broke test_auth.py
  collection; both caught by running the suite. TDD ordering (RED then GREEN)
  made the contract change obvious (401 → 403).

## Evaluation notes (flywheel)

- Failure modes observed: monkeypatch on a removed import Error's the whole
  class (must audit fixtures when a route loses a symbol); edit-tool
  indentation slip corrupted a test file and took two repair passes.
- Graders run and results (PASS/FAIL): PASS — 5/5 US2 tests green, auth audit
  green, 0 new suite failures, tasks T006-T011 [X].
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): User Story 1 ingestion on top of
  the verified handler, with US1 tests written first.