---

description: "Task list for Day 22 – WhatsApp Business Integration Research + Setup"
---

# Tasks: WhatsApp Business Integration Research + Setup

**Input**: Design documents from `/specs/013-whatsapp-business/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: No test tasks requested. Day 22 is setup + research; test tasks deferred to Day 23.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/`, `frontend/`
- Paths follow existing project structure at repository root

---

## Phase 1: Setup (Manual Configuration)

**Purpose**: Complete all manual portal setup and credential collection before any code work

**⚠️ CRITICAL**: These tasks are browser-based (Meta Developer portal, ngrok). They cannot be automated. Complete all of them before moving to code phases.

- [x] T001 Create Meta Developer account at https://developers.facebook.com using existing Facebook account
- [x] T002 Register new app (Business type) named "Communication AI" in Meta Developer portal
- [x] T003 Add WhatsApp Business product to the app in Meta Developer dashboard
- [x] T004 Copy Phone Number ID from WhatsApp → API Setup page
- [x] T005 Copy Temporary Access Token from WhatsApp → API Setup page (click "Generate" if needed)
- [x] T006 Copy WhatsApp Business Account ID from WhatsApp → Getting Started page
- [x] T007 Generate a random verify token string (e.g., `whatsapp_verify_day22`) and note it
- [x] T008 Add all four credentials to `backend/.env.local`: WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_BUSINESS_ACCOUNT_ID, WHATSAPP_ACCESS_TOKEN, WHATSAPP_VERIFY_TOKEN
- [x] T009 Verify `.env.local` is gitignored: run `git status` and confirm it does NOT appear
- [x] T010 Install ngrok if not already available: `npm install -g ngrok` or download from ngrok.com
- [x] T011 Start backend server: `cd backend && uvicorn main:app --reload --port 8000`
- [x] T012 Start ngrok tunnel: `ngrok http 8000` — copy the HTTPS URL
- [x] T013 Verify tunnel works: `curl https://<ngrok-url>/health` returns `{"status":"ok"}`

**Checkpoint**: Meta Developer app created, credentials in `.env.local`, ngrok tunnel active and backend accessible over HTTPS.

---

## Phase 2: Foundational (Webhook Verification Endpoint)

**Purpose**: Implement the GET verification endpoint that Meta requires before sending any messages

**⚠️ CRITICAL**: No webhook configuration in Meta portal can succeed without this endpoint

- [x] T014 Add GET `/webhooks/whatsapp` endpoint in `backend/routes/webhooks.py` — read `hub.mode`, `hub.verify_token`, `hub.challenge` from query params, validate against env var, return challenge on success or 403 on failure, no authentication required, log verification attempts at info level
- [x] T015 Test GET endpoint locally: `curl "http://localhost:8000/webhooks/whatsapp?hub.mode=subscribe&hub.verify_token=whatsapp_verify_day22&hub.challenge=test123"` returns `test123`
- [x] T016 Test GET endpoint via ngrok: `curl "https://<ngrok-url>/webhooks/whatsapp?hub.mode=subscribe&hub.verify_token=whatsapp_verify_day22&hub.challenge=test456"` returns `test456`

**Checkpoint**: GET verification endpoint works locally and via ngrok. Ready for Meta portal configuration.

---

## Phase 3: User Story 3 — Webhook Configuration & Verification (Priority: P1) 🎯 MVP

**Goal**: Configure the webhook URL in Meta Developer portal and complete the verification challenge

**Independent Test**: Meta Developer portal shows webhook as "Verified" and a test message is received by the backend

### Implementation for User Story 3

- [x] T017 [US3] In Meta Developer portal → WhatsApp → Configuration → Webhook, enter Callback URL: `https://<ngrok-url>/webhooks/whatsapp`
- [x] T018 [US3] Enter Verify Token in Meta portal: `whatsapp_verify_day22` (must match `.env.local`)
- [x] T019 [US3] Click "Verify and Save" in Meta portal — confirm portal shows webhook as "Verified"
- [x] T020 [US3] In Meta portal → WhatsApp → API Setup → send a test message to the Business number
- [x] T021 [US3] Check backend logs — confirm the POST webhook payload arrives and is logged
- [x] T022 [US3] Open dashboard at http://localhost:3000/dashboard — confirm the test message appears with AI analysis

**Checkpoint**: End-to-end flow works: phone → Meta → webhook → AI → dashboard. Webhook is verified.

---

## Phase 4: User Story 4 — Credential Security & Environment Setup (Priority: P2)

**Goal**: Verify all credentials are stored securely and no secrets leak

**Independent Test**: `git status` shows no tracked secrets; code review confirms no hardcoded values

### Implementation for User Story 4

- [x] T023 [US4] Run `git status` and confirm `backend/.env.local` is NOT listed as tracked or staged
- [x] T024 [US4] Search codebase for hardcoded credentials: `grep -r "WHATSAPP_ACCESS_TOKEN\|WHATSAPP_PHONE_NUMBER_ID" backend/ --include="*.py"` — confirm zero matches in source files
- [x] T025 [US4] Verify `backend/.env` or `backend/.env.local` appears in `.gitignore`
- [x] T026 [US4] Confirm backend reads credentials at runtime: add temporary `print(os.getenv("WHATSAPP_PHONE_NUMBER_ID"))` in `backend/main.py` startup, verify it prints the value, then remove the print statement

**Checkpoint**: All credentials in `.env.local` only. Zero hardcoded secrets. `.env.local` gitignored.

---

## Phase 5: User Story 5 — Official Message Flow Understanding (Priority: P2)

**Goal**: Document the official WhatsApp Business Cloud API message flow for Day 23 reference

**Independent Test**: `research.md` contains complete payload documentation covering structure, message types, acknowledgments, and errors

### Implementation for User Story 5

- [ ] T027 [US5] Review Meta WhatsApp Business Cloud API documentation at https://developers.facebook.com/docs/whatsapp/cloud-api
- [ ] T028 [US5] Document the official webhook payload structure in `specs/013-whatsapp-business/research.md` — cover the nested `entry[0].changes[0].value` structure, contacts array, messages array
- [ ] T029 [US5] Map Meta webhook fields to existing message schema (sender, content, timestamp, message_id) in `specs/013-whatsapp-business/research.md`
- [ ] T030 [US5] Document supported message types (text, image, audio, video, document, location, contacts, interactive) in `specs/013-whatsapp-business/research.md`
- [ ] T031 [US5] Document the acknowledgment mechanism (HTTP 200 to acknowledge receipt) in `specs/013-whatsapp-business/research.md`
- [ ] T032 [US5] Document common error responses and retry behavior in `specs/013-whatsapp-business/research.md`
- [ ] T033 [US5] Note key differences between current fake payload (`{sender, message}`) and real Meta payload in `specs/013-whatsapp-business/research.md`

**Checkpoint**: `research.md` is a complete reference document for Day 23 implementation.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final verification and cleanup

- [x] T034 [P] Run existing test suite: `cd backend && pytest` — confirm all tests pass
- [x] T035 [P] Review `backend/routes/webhooks.py` for code quality: follows existing patterns, proper error handling, no credential exposure
- [x] T036 [P] Verify no WhatsApp credentials appear in backend logs (check log output during test message)
- [x] T037 [P] Update `specs/013-whatsapp-business/quickstart.md` with any corrections discovered during setup

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — can start immediately. All manual browser work.
- **Phase 2 (Foundational)**: Depends on Phase 1 (backend must be running, ngrok active)
- **Phase 3 (US3 — Webhook Verification)**: Depends on Phase 2 (GET endpoint must exist)
- **Phase 4 (US4 — Credential Security)**: Can run after Phase 1 (credentials already stored)
- **Phase 5 (US5 — Message Flow Docs)**: No code dependencies — can run in parallel with Phase 2-4
- **Phase 6 (Polish)**: Depends on Phase 3 (webhook must be verified)

### User Story Dependencies

- **US3 (Webhook Verification, P1)**: Depends on Phase 2 (GET endpoint)
- **US4 (Credential Security, P2)**: Independent — can run after Phase 1
- **US5 (Message Flow Docs, P2)**: Independent — can run any time

### Within Each User Story

- Manual tasks first (portal configuration)
- Code tasks second (endpoint implementation)
- Verification tasks last (test and confirm)

### Parallel Opportunities

- T027-T033 (US5 research) can run in parallel with T014-T022 (Phase 2 + US3)
- T023-T026 (US4 credential check) can run in parallel with T017-T022 (US3 portal config)
- T034-T037 (Polish) tasks marked [P] can run in parallel

---

## Parallel Example: Research + Verification

```bash
# Research (US5) can happen while waiting for portal configuration:
Task: "Review Meta WhatsApp Business documentation"
Task: "Document webhook payload structure in research.md"
Task: "Map Meta fields to existing message schema"

# Meanwhile, portal configuration (US3):
Task: "Configure webhook URL in Meta portal"
Task: "Verify webhook in Meta portal"
Task: "Send test message"
```

---

## Implementation Strategy

### MVP First (US3 — Webhook Verification)

1. Complete Phase 1: Manual setup (Meta account, credentials, ngrok)
2. Complete Phase 2: GET verification endpoint (code)
3. Complete Phase 3: Configure and verify webhook in Meta portal
4. **STOP and VALIDATE**: Test message arrives at backend
5. Day 22 is complete — move to Day 23 for full implementation

### Incremental Delivery

1. Phase 1 → Portal setup complete, credentials stored
2. Phase 2 → Verification endpoint works locally and via ngrok
3. Phase 3 → Webhook verified, test message received (MVP!)
4. Phase 4 → Credential security validated
5. Phase 5 → Message flow documented for Day 23
6. Phase 6 → Final cleanup and test suite passes

---

## Notes

- Most Day 22 tasks are manual (browser-based) — they cannot be automated by an LLM
- Code tasks are limited: one GET endpoint + credential storage
- Day 22 is deliberately minimal — full message reception is Day 23
- ngrok tunnel must remain active during all testing
- The temporary Access Token expires in ~24 hours — regenerate if needed
- If webhook verification fails, check: ngrok URL, verify token match, backend logs
