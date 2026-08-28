# Implementation Plan: Real WhatsApp Webhook (Day 23)

**Branch**: `014-whatsapp-webhook` | **Date**: 2026-08-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/014-whatsapp-webhook/spec.md`

## Summary

Turn the verified webhook from Day 22 into a real ingestion endpoint. A real
WhatsApp message sent to the Business number arrives at the webhook, its
`X-Hub-Signature-256` signature is verified, the Meta payload is parsed and
converted into the canonical normalized message format, the message is stored
in MongoDB under the correct owning user (deduplicated by
`externalMessageId`), the AI pipeline runs off the request path, and the
message appears on the Dashboard — identically to simulated messages.

The architectural anchor is **source-agnosticity**: one shared ingestion
service translates any channel into the normalized format, so the AI
pipeline, storage, and Dashboard never read channel-specific payloads.

```text
WhatsApp → Webhook POST → Verify signature → Parse → Normalize →
Dedupe → MongoDB → 200 OK (fast) → AI Pipeline (background) → Dashboard
```

## Technical Context

**Language/Version**: Python 3.13
**Primary Dependencies**: FastAPI, uvicorn, motor, pydantic, python-dotenv
(stock — no new runtime dependencies)
**Storage**: MongoDB (`messages`, `connections`, `users` collections) — add a
partial unique index on `messages.external_message_id`
**Testing**: pytest + httpx TestClient (existing suite) plus a manual
real-message pass through ngrok and the Meta Developer portal
**Target Platform**: Local development (ngrok tunnel provides HTTPS)
**Project Type**: Web application (Next.js frontend + FastAPI backend)
**Performance Goals**: Webhook responds 200 in < 1s; AI pipeline stays within
the existing ≤ 10s budget and never blocks the webhook response
**Constraints**: Meta requires HTTPS and a subscription to the `messages`
field; requests without a valid `X-Hub-Signature-256` MUST be rejected;
ownership MUST be resolved server-side (never from the payload)
**Scale/Scope**: Single WhatsApp Business test number, demo user; multi-number
support and outbound messaging are out of scope

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle / Rule | Status | Notes |
|---|---|---|
| I. Simplicity First | ✅ PASS | One shared ingest service + two route handlers; no new services or queues |
| II. Vertical Slices | ✅ PASS | Real ingestion is a complete end-to-end slice: webhook → MongoDB → AI → Dashboard |
| III. AI is Assistive | ✅ PASS | AI pipeline unchanged; runs on stored normalized messages as today |
| IV. User Control | ✅ PASS | Receive-only; no auto-replies or outbound sends |
| V. Security and Privacy | ✅ PASS | Signature-first validation; credentials in env; no raw payloads persisted |
| VI. Clean Code | ✅ PASS | Follows existing FastAPI route/service patterns; shared ingest function avoids duplication |
| VII. Progressive Enhancement | ✅ PASS | Message renders on Dashboard even if `ai_analysis` is pending/failed |
| Day 18 User Isolation | ✅ PASS | `user_id` resolved server-side from the connected whatsapp connection; payload carries no identity |
| Day 19 Connection Arch | ✅ PASS | Ownership mapping reuses the existing `connections` collection; token fields untouched |
| Day 22 WhatsApp Rules | ✅ PASS | Official Cloud API only; no personal-account access; credentials in `.env` |
| Day 23 Webhook Rules | ✅ PASS | Signature verified before parse; dedup on `external_message_id`; respond-200-first; no bare `text.body` reads below the ingestion boundary |

**No violations. No complexity tracking needed.**

## Project Structure

### Documentation (this feature)

```text
specs/014-whatsapp-webhook/
├── plan.md              # This file
├── spec.md              # Feature spec (/sp.specify output)
├── research.md          # Phase 0: payload handling, signature, design decisions
├── data-model.md        # Phase 1: normalized message schema + indexes
├── quickstart.md        # Phase 1: Day 23 runbook
├── contracts/           # Phase 1: API contracts
│   └── webhook-api.md   # GET/POST webhook + simulate endpoints
└── tasks.md             # Phase 2: NOT created by /sp.plan
```

### Source Code (repository root)

```text
backend/
├── routes/
│   └── webhooks.py                  # REWORK POST; keep GET; ADD POST /webhooks/simulate
├── services/
│   └── webhook_ingest.py            # NEW — shared normalize+dedupe+persist service
├── models/
│   └── message.py                   # ADD optional external_message_id, received_at to response
├── main.py                          # ADD partial unique index on external_message_id
├── .env / .env.example              # ADD WHATSAPP_APP_SECRET
└── tests/
    ├── test_webhooks.py             # NEW — signature, parse, dedup, simulate, isolation
    ├── test_auth.py                 # UPDATE — PUBLIC_ROUTES, webhook no longer 401
    └── test_user_isolation.py       # UPDATE — ownership via connected whatsapp connection
    test_attention_pipeline.py       # UPDATE — duplicate-guard against signed Meta payload

frontend/
└── components/
    └── SimulateMessage.tsx          # UPDATE — POST to /webhooks/simulate
```

**Structure Decision**: Web application layout. Day 23 changes are confined to
the backend ingestion path plus one frontend endpoint pointer. A shared
`webhook_ingest.py` service is introduced so the real webhook and the simulate
endpoint produce identical normalized documents through one code path.

## Technical Approach

1. **Keep the GET verification endpoint** (`GET /webhooks/whatsapp`) exactly
   as delivered on Day 22 — it is public, token-protected, and already
   verified by the Meta portal.
2. **Make the Meta delivery endpoint public but signature-gated.**
   `POST /webhooks/whatsapp` is removed from JWT auth (Meta cannot send
   cookies) and protected instead by `X-Hub-Signature-256` HMAC-SHA256
   verification of the raw body with `WHATSAPP_APP_SECRET`. Invalid or
   missing signatures return 403 before any parsing.
3. **Parse the real Meta payload.** Extract every `messages[].*` entry from
   the nested structure (`entry[0].changes[0].value`). For each message text
   event build a normalized document; ignore non-message events
   (`field != "messages"`) and any payload whose
   `metadata.phone_number_id` does not match `WHATSAPP_PHONE_NUMBER_ID`.
4. **Normalize at the boundary.** A single shared service
   `ingest_message(user_id, source, sender, content, external_message_id,
   message_type)` builds the canonical document that MongoDB, the AI pipeline,
   and the Dashboard consume. For WhatsApp: `source="whatsapp"`,
   `sender=profile.name or from(wa_id)`, `content=text.body` (empty for
   media, flagged `message_type="media"`), `external_message_id=messages[].id`,
   `received_at=server now (UTC)`.
5. **Deduplicate atomically.** A partial unique index on
   `messages.external_message_id` guarantees one document per provider message
   ID. On index violation the duplicate is acknowledged (200) and skipped —
   not re-analyzed.
6. **Resolve ownership server-side.** `user_id` comes from the connected
   WhatsApp connection (`connections` where `provider="whatsapp"` and
   `status="connected"`). If no connection exists (or the phone number ID does
   not match ours), the delivery is acknowledged but not stored.
7. **Respond fast, analyze later.** The handler inserts the message, returns
   200, then schedules the existing `analyze_message` pipeline as a FastAPI
   background task. No pipeline work happens before the response is sent.
8. **Keep simulation first-class.** A new authenticated endpoint
   `POST /webhooks/simulate` calls the *same* ingest service with
   `source="simulate"`, so simulated and real messages follow one normalized
   path (spec US3 parity). `SimulateMessage.tsx` points here instead of the
   Meta endpoint.

## Implementation Steps (in order)

### Step 1 — Add `WHATSAPP_APP_SECRET` to environment

- [ ] Add `WHATSAPP_APP_SECRET=<App Secret from Meta portal — App Settings →
      Basic>` to `backend/.env`
- [ ] Add the key (empty value) to `backend/.env.example`
- [ ] Confirm `backend/.env` is gitignored (`git status` does not show it)

**Checkpoint**: `WHATSAPP_APP_SECRET` readable at runtime, never committed.

### Step 2 — Create the shared ingestion service

New file `backend/services/webhook_ingest.py`:

- [ ] `async ingest_message(user_id, source, sender, content, external_message_id=None, message_type="text") -> str`
  - [ ] Build the normalized document: `user_id`, `source`, `sender`,
        `content`, `external_message_id` (optional), `message_type`,
        `status="unread"`, `state="active"`, `received_at` / `created_at`
        (UTC now), `updated_at`
  - [ ] Insert; on `DuplicateKeyError` on `external_message_id` return the
        existing message id (skip re-insert)
  - [ ] Schedule `analyze_message(content, message_id, user_id)` as the
        background task (or return the message id for the caller to schedule)
  - [ ] Return the message id on both fresh and duplicate paths

**Checkpoint**: Service builds and inserts the same document shape as the
existing `/messages` create path, plus the new dedup field.

### Step 3 — Rework `POST /webhooks/whatsapp` for Meta

Modify `backend/routes/webhooks.py`:

- [ ] Drop `get_current_user` from the POST handler (no JWT)
- [ ] Accept raw body bytes, verify `X-Hub-Signature-256` against
      `WHATSAPP_APP_SECRET` (constant-time compare); return 403 on mismatch
- [ ] Parse with a Pydantic model matching Meta's payload; return 400 on
      malformed JSON
- [ ] Validate `value.metadata.phone_number_id == WHATSAPP_PHONE_NUMBER_ID`;
      skip (acknowledge) foreign/unknown numbers
- [ ] Ignore non-message events (`field != "messages"` or empty
      `messages[]`) with a 200 acknowledgement
- [ ] Resolve `user_id` from the connected whatsapp connection
- [ ] For each message event: map to normalized fields and call
      `ingest_message(..., source="whatsapp")`
- [ ] Return 200 `{"status":"ok"}` immediately; AI runs in the background

**Checkpoint**: `curl` with a wrong signature → 403; with a valid signature →
200 and a normalized document in the `messages` collection.

### Step 4 — Add `POST /webhooks/simulate`

In `backend/routes/webhooks.py`:

- [ ] Keep the authenticated `Depends(get_current_user)` dependency
- [ ] Accept `{sender, message}` (same shape the frontend sends today)
- [ ] Call `ingest_message(user_id, source="simulate", ...)` with the JWT user
- [ ] Return the stored message response

**Checkpoint**: Simulated messages land in MongoDB with `source="simulate"`
and follow the identical AI pipeline (parity with real messages).

### Step 5 — Extend the message response surface

Modify `backend/models/message.py`:

- [ ] Add optional `external_message_id: Optional[str]` and
      `received_at: Optional[datetime]` to `MessageResponse` and to
      `message_doc_to_response` (absent for simulate/legacy messages → omitted)

**Checkpoint**: Serializer tolerates missing dedup/received fields.

### Step 6 — Add the dedup index

Modify `backend/main.py` lifespan (and note in `backend/database.py` docs):

- [ ] `messages_collection.create_index([("external_message_id", 1)], unique=True, partialFilterExpression={"external_message_id": {"$type": "string"}})`

**Checkpoint**: Duplicate inserts of the same `external_message_id` raise a
duplicate-key error caught by the ingest service.

### Step 7 — Update the frontend simulation pointer

Modify `components/SimulateMessage.tsx`:

- [ ] Change the POST target from `/webhooks/whatsapp` to `/webhooks/simulate`
      (payload `{sender, message}` unchanged)

**Checkpoint**: Simulate form in the app still works; dashboard card shows
source "Simulate".

### Step 8 — Update tests

- [ ] `backend/tests/test_auth.py`:
  - [ ] Add `("GET", "/webhooks/whatsapp")` and
        `("POST", "/webhooks/whatsapp")` to `PUBLIC_ROUTES`
  - [ ] Change the "webhook returns 401 without session" assertion to target
        `/webhooks/simulate` instead
- [ ] `backend/tests/test_user_isolation.py`:
  - [ ] Rework webhook ownership tests: register user A, connect WhatsApp
        (provider `whatsapp`), send a signed real Meta payload, assert message
        is stored under A and invisible to user B
- [ ] `backend/test_attention_pipeline.py`:
  - [ ] Update the duplicate-guard test to POST a signed Meta payload twice
        (same `wamid`) and assert one document

### Step 9 — Add `backend/tests/test_webhooks.py`

- [ ] Helper to build a Meta payload string and sign it with the app secret
- [ ] `test_verification_challenge_echoes_challenge` (GET success/failure)
- [ ] `test_post_rejects_invalid_signature` → 403, nothing stored
- [ ] `test_post_rejects_missing_signature` → 403
- [ ] `test_post_ingests_real_text_message` → 200, normalized fields stored,
      `external_message_id` present
- [ ] `test_post_duplicate_external_id_single_document` → 200 twice, one doc
- [ ] `test_post_non_message_event_ignored` → 200, nothing stored
- [ ] `test_post_unknown_phone_number_ignored` → acknowledged, nothing stored
- [ ] `test_simulate_endpoint_ingests_with_source` → message stored,
      `source="simulate"`
- [ ] `test_media_only_message_stored_not_dropped` → `content=""`,
      `message_type="media"`

### Step 10 — Run the test suite and the real-message pass

- [ ] `cd backend && python -m pytest tests/ -q` — all green
- [ ] Standalone scripts `test_ai_analysis.py`, `test_attention_pipeline.py`
      updated and passing
- [ ] Manual real-message pass per `testing-with-real-whatsapp.md` section below

## Testing Plan (using a real WhatsApp message)

Automated (pytest) — the matrix in Step 9 covers signature rejection,
normalization, dedup, media messages, non-message events, simulate parity, and
user isolation, all using a locally computed valid signature.

Manual end-to-end with the real Business number:

1. Ensure `WHATSAPP_APP_SECRET` and `WHATSAPP_PHONE_NUMBER_ID` are set in
   `backend/.env`; restart the backend.
2. Start ngrok: `ngrok http 8000`; confirm `/health` over HTTPS.
3. Verify the portal callback URL is still `https://<ngrok-url>/webhooks/whatsapp`
   and matches the running tunnel; re-save if the URL changed.
4. Open the app, log in, and connect WhatsApp so a `connected` connection
   exists (this maps the webhook to the owner).
5. From your phone (or the portal's "Send test message"), send:
   `Send me the slides tonight.`
6. Expect, within 30s: message card on the Dashboard with sender name,
   content, source WhatsApp, and full AI analysis.
7. Confirm in MongoDB that exactly one document exists with
   `external_message_id` set (query by content), proving dedup plumbing.
8. Resend the identical payload via a signed curl while watching the DB — the
   message count does not change (idempotence).
9. Send a photo — the Dashboard shows a media-marked card with empty content.
10. Send curl with a tampered signature → 403 and no new document.

## Definition of Done

A feature is DONE when:

1. ✅ A real WhatsApp message flows end-to-end: phone → webhook → signature
   verification → normalize → MongoDB → AI pipeline → Dashboard (spec SC-001)
2. ✅ `POST /webhooks/whatsapp` rejects invalid/missing signatures (403) with
   no data stored (spec SC-004)
3. ✅ Redelivering the same `externalMessageId` produces one document and one
   pipeline run (spec SC-003)
4. ✅ Normalized documents carry `user_id`, `source`, `sender`, `content`,
   `received_at`, `external_message_id` (spec FR-004, FR-005)
5. ✅ Ownership is resolved server-side from the WhatsApp connection; the
   message is invisible to other users (spec SC-005)
6. ✅ The simulation feature works through the same ingest path
   (`POST /webhooks/simulate`) with zero regressions (spec SC-002, FR-011)
7. ✅ Media-only messages are stored with a media marker, never dropped
   (spec SC-006)
8. ✅ The webhook acknowledges valid deliveries fast (200 < 1s) with AI in the
   background (spec SC-007)
9. ✅ Existing test suite passes (`python -m pytest tests/ -q`)
10. ✅ No hardcoded secrets; `WHATSAPP_APP_SECRET` in gitignored `backend/.env`
11. ✅ Real and simulated messages with the same text produce identical AI
    analysis (spec SC-008)

## Complexity Tracking

No violations. No complexity tracking needed.