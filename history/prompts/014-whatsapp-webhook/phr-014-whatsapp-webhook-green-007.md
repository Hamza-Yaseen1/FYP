---
id: phr-014-whatsapp-webhook-green-007
title: Phase 8 Polish & Verification
stage: green
date: 2026-08-28
surface: cli
model: opencode/big-pickle
feature: whatsapp-webhook
branch: 014-whatsapp-webhook
user: user
command: /sp.green
labels: [green, day23, whatsapp-webhook, polish, constitution, verification]
links:
  spec: specs/014-whatsapp-webhook/spec.md
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - backend/test_attention_pipeline.py
  - specs/014-whatsapp-webhook/tasks.md
tests:
  - backend/tests/ (89 passed / 0 failed — T031)
  - backend/test_attention_pipeline.py (10/10 incl live signed integration — T032)
  - backend/test_ai_analysis.py (3/3 on retry — T032)
  - live-server curls (tampered sig 403, signed-body dedup single doc)
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

Phase 8 polish after user confirmation. Discovery: the user has pasted the real
`WHATSAPP_APP_SECRET` into `backend/.env` and a uvicorn (--reload) already runs
on :8000 with current code (unsigned probe → 403), so most of T032/T033 could be
run against the LIVE server.

- T031 [X]: `pytest tests/` final → 89 passed / 0 failed.
- T032 [X]: 
  - `test_attention_pipeline.py` → 10/10 (9 evaluate_attention unit tests +
    signed-Meta duplicate-guard integration against live :8000: register user,
    create whatsapp connection, deliver twice, one doc, `ai_analysis.status`
    completed via background poll). Fixed a gap in that script it had: it must
    `POST /connections {"provider":"whatsapp"}` before delivering, else the
    server-side owner resolution stores nothing; also added a short poll for the
    async analysis.
  - `test_ai_analysis.py` → 3/3 on retry. First run flaked on test 3 ("normal
    message" came back `status=pending`); identical call on retry returned
    `completed` — transient Groq/provider flake, not a regression. Needs
    `PYTHONUTF8=1`/`PYTHONIOENCODING=utf-8` on this cp1252 console (emoji).
- T033 [ ] (user-blocked, partially validated): tampered-signature curl
  (HMAC over a DIFFERENT body) → 403 and signed-body dedup (single
  `externalMessageId` doc) verified live. The real-phone send still requires
  the user: ngrok up (`.env` `NGROK_URL` is stale), portal callback → ngrok,
  send an actual message to the Business number, confirm dashboard card.
- T034 [X]: read the full Day 23 constitution block and verified every rule:
  all 6 normalized-format rules (`source` enum-branching, human-readable
  sender, media→empty-content-not-drop, server `receivedAt`,
  `externalMessageId` keys idempotence, server-side `user_id` from connection
  mapping), all 6 security rules (signature-first 403, Pydantic 400, fast 200
  + async AI, idempotent redelivery, credentials env-only, minimal retention),
  all MUST-NOTs (no unverified processing, no AI blocking, no raw payloads, no
  client identity, no bypass-normalization, receive-only), and the quality bar
  — including a grep that WhatsApp-specific fields (`wa_id`,
  `messaging_product`) appear ONLY in the parse boundary
  (`models/meta_webhook.py`) and Meta test fixtures.

## Outcome

- ✅ Impact: Day 23 feature complete and constitution-compliant; the only
  remaining gate is the user's own real-message smoke test (phone + tunnel).
- 🧪 Tests: 89/89 full suite; both standalone scripts green; live-server
  tamper/dedup proven.
- 📁 Files: backend/test_attention_pipeline.py (connection + poll), tasks.md
  (T031/T032/T034 [X], T033 user-blocked with state).
- 🔁 Next prompts: none remaining for Day 23; the user should (1) run ngrok,
  update NGROK_URL/portal callback, (2) send a real WhatsApp message and
  confirm the dashboard card, (3) then mark T033 [X] and wrap the feature.
- 🧠 Reflection: the live-server runs turned polish into real verification. The
  T025 script's owner-resolution gap would have silently 200'd nothing had the
  connections flow not been recalled — a good reminder that the integration
  script must mirror the app, not the test mocks.

## Evaluation notes (flywheel)

- Failure modes observed: (1) Groq transient flake on "normal message" — first
  attempt pending, retry completed; (2) cp1252 console chokes on emoji in
  test_ai_analysis — needs PYTHONUTF8=1; (3) integration script lacked the
  connection step — fixed.
- Graders run and results (PASS/FAIL): PASS — 89/89, 10/10 + 3/3 standalone,
  tamper 403 + dedup live. T033 explicitly NOT claimed complete.
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): full handover to the user for the
  real-phone quickstart smoke test.