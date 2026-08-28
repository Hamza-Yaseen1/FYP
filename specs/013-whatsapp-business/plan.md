# Implementation Plan: WhatsApp Business Integration Research + Setup

**Branch**: `013-whatsapp-business` | **Date**: 2026-08-26 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/013-whatsapp-business/spec.md`

## Summary

Replace the fake WhatsApp webhook with a real integration using the
official WhatsApp Business Platform Cloud API. Day 22 is a research
and setup day: create the Meta Developer app, configure the webhook
endpoint, verify it works, and document the official message flow.
Full message reception and AI pipeline integration are deferred to
Day 23.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: FastAPI, uvicorn, python-dotenv
**Storage**: MongoDB (Motor async driver) — existing, unchanged on Day 22
**Testing**: pytest, httpx (existing test suite)
**Target Platform**: Local development (ngrok tunnel for public access)
**Project Type**: Web application (Next.js frontend + FastAPI backend)
**Performance Goals**: Webhook response < 500ms (verification), < 2s (message receipt)
**Constraints**: HTTPS required for webhook; ngrok tunnel must be active
**Scale/Scope**: Single developer, single WhatsApp Business number, test tier

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Simplicity First | ✅ PASS | Adding one GET endpoint + env vars; no new services |
| II. Vertical Slices | ✅ PASS | Webhook verification is a complete, testable slice |
| III. AI is Assistive | ✅ PASS | AI pipeline unchanged; webhook just receives messages |
| IV. User Control | ✅ PASS | User decides when to connect WhatsApp; no auto-sends |
| V. Security and Privacy | ✅ PASS | Credentials in env vars; no hardcoded secrets; webhook sig verification planned |
| VI. Clean Code | ✅ PASS | Follows existing FastAPI patterns in webhooks.py |
| VII. Progressive Enhancement | ✅ PASS | Dashboard still works without WhatsApp; webhook is additive |
| Day 22 Rules | ✅ PASS | Official Cloud API only; no personal data; credentials in .env |
| Day 19 Connection Arch | ✅ PASS | Token encryption planned for Day 23; Day 22 uses temp token |
| Day 18 User Isolation | ✅ PASS | Webhook resolves user_id from JWT (POST) or env (GET verification) |

**No violations. No complexity tracking needed.**

## Project Structure

### Documentation (this feature)

```text
specs/013-whatsapp-business/
├── plan.md              # This file
├── research.md          # Phase 0: Meta API research, ngrok setup, payload docs
├── data-model.md        # Phase 1: Existing schema + Day 23 extensions
├── quickstart.md        # Phase 1: Step-by-step setup guide
├── contracts/           # Phase 1: API contracts
│   └── webhook-api.md   # GET/POST webhook endpoint specs
└── tasks.md             # Phase 2: NOT created by /sp.plan
```

### Source Code (repository root)

```text
backend/
├── main.py                          # FastAPI app (add env loading)
├── routes/
│   └── webhooks.py                  # ADD GET endpoint for verification
├── .env.local                       # ADD WhatsApp credentials (gitignored)
└── tests/
    └── test_webhooks.py             # ADD verification endpoint tests

frontend/                            # No changes on Day 22
```

**Structure Decision**: Web application layout. Day 22 changes are
confined to `backend/routes/webhooks.py` (add GET handler) and
`backend/.env.local` (add 4 environment variables). No new files
are created in source code.

## Implementation Steps

### Phase 2: Day 22 Tasks (Setup + Research)

**Purpose**: Complete the research and setup goals defined in the spec.

#### Step 1: Meta Developer Account & App (Manual — No Code)

- [ ] Create Meta Developer account at `https://developers.facebook.com`
- [ ] Register new app (Business type) named "Communication AI"
- [ ] Add WhatsApp Business product to the app
- [ ] Note the App ID and App Secret (for later use)

**Checkpoint**: App visible in Meta Developer dashboard with WhatsApp
product active.

#### Step 2: Collect WhatsApp Credentials (Manual — No Code)

- [ ] In WhatsApp → API Setup, copy Phone Number ID
- [ ] In WhatsApp → API Setup, generate/copy Temporary Access Token
- [ ] In WhatsApp → Getting Started, copy WhatsApp Business Account ID
- [ ] Generate a random verify token string (e.g., `whatsapp_verify_day22`)
- [ ] Store all four in `backend/.env.local`:

```bash
WHATSAPP_PHONE_NUMBER_ID=<from portal>
WHATSAPP_BUSINESS_ACCOUNT_ID=<from portal>
WHATSAPP_ACCESS_TOKEN=<from portal>
WHATSAPP_VERIFY_TOKEN=whatsapp_verify_day22
```

- [ ] Verify `.env.local` is gitignored: `git status` must NOT show it

**Checkpoint**: All four credentials stored securely in `.env.local`.

#### Step 3: Start Backend + ngrok Tunnel (Manual — No Code)

- [ ] Start backend: `cd backend && uvicorn main:app --reload --port 8000`
- [ ] Start ngrok: `ngrok http 8000`
- [ ] Copy the HTTPS URL from ngrok
- [ ] Verify tunnel: `curl https://<ngrok-url>/health` → `{"status":"ok"}`

**Checkpoint**: Backend accessible via public HTTPS URL.

#### Step 4: Add Webhook Verification Endpoint (Code)

Modify `backend/routes/webhooks.py`:

- [ ] Add `GET /webhooks/whatsapp` endpoint
- [ ] Read `hub.mode`, `hub.verify_token`, `hub.challenge` from query params
- [ ] Validate `hub.mode == "subscribe"` and `hub.verify_token == env var`
- [ ] Return `hub.challenge` as plain text (HTTP 200) on success
- [ ] Return HTTP 403 on failure
- [ ] Do NOT require authentication (Meta cannot send JWT)
- [ ] Add logging for verification attempts (info level)

**Checkpoint**: GET endpoint responds to curl:
```bash
curl "http://localhost:8000/webhooks/whatsapp?hub.mode=subscribe&hub.verify_token=whatsapp_verify_day22&hub.challenge=test123"
# Should return: test123
```

#### Step 5: Configure Webhook in Meta Portal (Manual — No Code)

- [ ] In Meta Developer portal → WhatsApp → Configuration → Webhook
- [ ] Enter Callback URL: `https://<ngrok-url>/webhooks/whatsapp`
- [ ] Enter Verify Token: `whatsapp_verify_day22` (same as .env.local)
- [ ] Click "Verify and Save"
- [ ] Confirm portal shows webhook as "Verified"

**Checkpoint**: Meta portal shows webhook verified.

#### Step 6: Send Test Message (Manual — No Code)

- [ ] In Meta portal → WhatsApp → API Setup → send test message
- [ ] Check backend logs — webhook payload should arrive
- [ ] The existing POST endpoint processes it through the AI pipeline
- [ ] Check dashboard — message appears with AI analysis

**Checkpoint**: End-to-end flow works: phone → Meta → webhook → AI → dashboard.

#### Step 7: Document Message Flow (Research — No Code)

- [ ] Document the official Meta webhook payload structure in `research.md`
- [ ] Map Meta fields to existing message schema
- [ ] Note key differences from current fake payload
- [ ] Document message types (text, image, audio, document, etc.)
- [ ] Document acknowledgment mechanism
- [ ] Document error responses

**Checkpoint**: `research.md` contains complete payload documentation
for Day 23 reference.

#### Step 8: Test Signature Verification (Code — Optional for Day 22)

- [ ] Add `WHATSAPP_APP_SECRET` to `.env.local` (from Meta portal)
- [ ] Implement `X-Hub-Signature-256` HMAC validation on POST endpoint
- [ ] Test with valid and invalid signatures
- [ ] If time-constrained, defer to Day 23

**Checkpoint**: POST endpoint rejects requests with invalid signatures.

## Definition of Done for Day 22

A feature is DONE when:

1. ✅ Meta Developer account exists with WhatsApp Business App registered
2. ✅ Four credentials stored in `.env.local` (gitignored, not in code)
3. ✅ ngrok tunnel active and backend accessible over HTTPS
4. ✅ GET verification endpoint works and Meta portal shows "Verified"
5. ✅ Test message sent from Meta portal is received by backend
6. ✅ Test message appears on dashboard with AI analysis
7. ✅ `research.md` documents the official message flow
8. ✅ No hardcoded secrets anywhere in the codebase
9. ✅ Existing test suite still passes
10. ✅ Backend logs show verification and message receipt

## What's Ready at End of Day 22

| Artifact | Status | Notes |
|---|---|---|
| Meta Developer App | ✅ Created | WhatsApp Business product active |
| Webhook Verification | ✅ Working | GET endpoint responds to Meta's challenge |
| Test Message Reception | ✅ Working | POST endpoint receives real Meta payloads |
| Credentials | ✅ Stored | Four values in `.env.local` |
| ngrok Tunnel | ✅ Active | Public HTTPS URL available |
| Message Flow Docs | ✅ Documented | Payload structure mapped for Day 23 |
| Signature Verification | ⚠️ Optional | Implement if time permits; required for Day 23 |

## What's Done in Day 23

| Task | Priority | Notes |
|---|---|---|
| Parse real Meta webhook payloads | P1 | Extract from nested `entry[0].changes[0].value` |
| Store messages in MongoDB | P1 | Map Meta fields to existing message schema |
| Implement X-Hub-Signature-256 | P1 | Required for production security |
| Handle message types | P2 | Text first; image, audio, document later |
| Long-lived Access Token | P2 | Replace temporary token |
| User isolation for webhooks | P1 | Resolve user_id from server-side credentials |
| Dashboard integration | P1 | Messages appear with full AI analysis |

## Complexity Tracking

No violations. No complexity tracking needed.
