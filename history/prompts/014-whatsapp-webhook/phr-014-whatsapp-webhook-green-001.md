---
id: phr-014-whatsapp-webhook-green-001
title: Day 23 Setup and Foundational Slice
stage: green
date: 2026-08-28
surface: cli
model: opencode/big-pickle
feature: whatsapp-webhook
branch: 014-whatsapp-webhook
user: user
command: /sp.green
labels: [green, day23, whatsapp-webhook, foundational, ingress]
links:
  spec: specs/014-whatsapp-webhook/spec.md
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - backend/services/webhook_ingest.py
  - backend/main.py
  - backend/models/message.py
  - backend/.env
  - backend/.env.example
  - specs/014-whatsapp-webhook/tasks.md
tests:
  - backend/tests/test_auth.py (baseline, 4 of full set predate this work)
  - backend/tests/test_user_isolation.py (baseline, 4 of full set predate this work)
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

Implemented Phase 1 (Setup) + Phase 2 (Foundational) of
`specs/014-whatsapp-webhook/tasks.md` — the blocking infrastructure every
user story depends on — and STOPPED for confirmation per the prompt.

- T001/T002: Added `WHATSAPP_APP_SECRET=` key to `backend/.env` (gitignored,
  empty — real value must be pasted from Meta portal by the user) and
  `backend/.env.example`.
- T003: Created `backend/services/webhook_ingest.py` —
  `async ingest_message(user_id, source, sender, content,
  external_message_id=None, message_type="text", background_tasks=None)`
  builds the normalized doc (snake_case fields + `received_at`,
  `message_type`, `status="unread"`, `state="active"`), inserts,
  catches `DuplicateKeyError` → returns existing id (no re-insert / no
  re-analysis), and schedules `analyze_message` as a FastAPI background task.
- T004: Added partial unique index on `messages.external_message_id`
  (`unique=True`, `$type:"string"` partial filter) to the lifespan in
  `backend/main.py`.
- T005: Added optional `external_message_id` + `received_at` to
  `MessageResponse` and `message_doc_to_response` in
  `backend/models/message.py` (emitted only when present).

Verification:
- Smoke test (test DB): duplicate `external_message_id` → same id returned,
  exactly 1 stored doc; media message stored with `message_type="media"`,
  empty content, `received_at` set. PASS.
- pytest subset: 39 passed / 8 failed. The 8 failures were proven
  pre-existing by stashing the two changed files and reproducing them on the
  baseline: (a) isolation/auth tests written against the old `/messages`
  bare-list response shape (fix scheduled in T027, US5); (b)
  `TestAuthCoverage` PUBLIC_ROUTES missing Day 22's `GET /webhooks/whatsapp`
  (fix scheduled in T010, US2). Phase 1/2 introduce zero new failures.

## Outcome

- ✅ Impact: Dedup-safe, normalized ingestion path and index now exist and are
  verified; subsequent stories (US2 signature gate → US1 parse/store) slot in
  on top.
- 🧪 Tests: Not written this phase (per tasks.md tests belong to each story).
  Baseline suite ran; no regressions introduced.
- 📁 Files: backend/services/webhook_ingest.py (new), backend/main.py,
  backend/models/message.py, backend/.env, backend/.env.example,
  tasks.md (T001-T005 marked [X]).
- 🔁 Next prompts: /sp.red for User Story 2 (signature + structure gate),
  then User Story 1 (parse/normalize/store + fast ack).
- 🧠 Reflection: The horizontal foundation proved its value — the same 8 test
  failures exist on the stashed baseline, so the checkpoint is clean. The
  only user action needed is pasting the real WHATSAPP_APP_SECRET before real
  traffic; signature tests in US2 will set their own test secret.

## Evaluation notes (flywheel)

- Failure modes observed: 8 pytest failures looked alarming but were all
  pre-existing (response-shape assumptions vs PUBLIC_ROUTES gap); isolated
  via `git stash push -- <paths>` comparison. `.env.example` is gitignored
  (`.env*` rule) so it cannot be stashed/committed via pathspec — worth
  remembering. No create-phr script on Windows → agent-native PHR.
- Graders run and results (PASS/FAIL): PASS — Phase 1+2 complete, smoke tests
  green, zero new test failures, tasks T001-T005 marked [X].
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): US2 signature-verification
  vertical slice with failing tests written first.