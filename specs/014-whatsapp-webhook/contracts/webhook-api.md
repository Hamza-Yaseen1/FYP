# API Contracts: Real WhatsApp Webhook Ingestion

**Feature**: 014-whatsapp-webhook | **Date**: 2026-08-28 | **Phase**: 1 (Design)

Supersedes the Day 22 contract for `POST /webhooks/whatsapp` (now
signature-protected, parses real Meta payloads, stores normalized documents).
The GET verification endpoint and `POST /webhooks/simulate` are specified here
too. Environment variables for this feature are listed at the bottom.

## 1. GET /webhooks/whatsapp — Meta Webhook Verification (unchanged)

**Authentication**: NONE

**Request**: `GET /webhooks/whatsapp?hub.mode=subscribe&hub.verify_token=<token>&hub.challenge=<code>`

| Parameter | Type | Required | Description |
|---|---|---|---|
| `hub.mode` | string | Yes | Must be `"subscribe"` |
| `hub.verify_token` | string | Yes | Must equal `WHATSAPP_VERIFY_TOKEN` |
| `hub.challenge` | string | Yes | Echoed back as plain text |

- 200: plain-text `hub.challenge`
- 403: `Verification failed`

---

## 2. POST /webhooks/whatsapp — Receive Real WhatsApp Messages

**Purpose**: Ingest messages Meta delivers for the subscribed Business number.

**Authentication**: **NONE (no JWT).** Protected by `X-Hub-Signature-256`
validation against `WHATSAPP_APP_SECRET`. Invalid or missing signature →
403 before any parsing.

**Request Headers**:
| Header | Type | Required | Description |
|---|---|---|---|
| `X-Hub-Signature-256` | string | Yes | `sha256=` + hex HMAC-SHA256 of raw body with App Secret |
| `Content-Type` | string | Yes | `application/json` |

**Request Body** (Meta's webhook payload):
```json
{
  "object": "whatsapp_business_account",
  "entry": [{
    "id": "WABA_ID",
    "changes": [{
      "value": {
        "messaging_product": "whatsapp",
        "metadata": {
          "display_phone_number": "1234567890",
          "phone_number_id": "PHONE_NUMBER_ID"
        },
        "contacts": [{
          "wa_id": "1234567890",
          "profile": { "name": "User Name" }
        }],
        "messages": [{
          "from": "1234567890",
          "id": "wamid.xxx",
          "timestamp": "1234567890",
          "type": "text",
          "text": { "body": "Hello" }
        }]
      },
      "field": "messages"
    }]
  }]
}
```

Meta may batch several message events in one `entry[].changes[].value.messages`
array; each is ingested independently.

**Handling rules (in order)**:
1. Signature missing/invalid → **403** `{"error": "Invalid signature"}`.
2. Malformed JSON or schema → **400** `{"error": "Invalid payload"}`.
3. `field != "messages"` event, or `messages` empty/absent (e.g. `statuses`
   updates) → **200** `{"status": "ok"}` (acknowledge, store nothing).
4. `value.metadata.phone_number_id != WHATSAPP_PHONE_NUMBER_ID` → **200**
   acknowledged, store nothing (not for our number).
5. No connected whatsapp connection (`connections`: `provider="whatsapp"`,
   `status="connected"`) → **200** acknowledged, store nothing.
6. Otherwise, for each `messages[]` event, insert via the shared ingest
   service (normalize → dedup → persist), then **200**.

**Success Response** (HTTP 200):
```json
{ "status": "ok" }
```
Returned fast (< 1s); AI analysis runs as a background task.

**Error Response** (HTTP 403):
```json
{ "error": "Invalid signature" }
```

**Status codes**: 200 valid/acknowledged/duplicate · 400 malformed · 403 bad
signature. Never 401 (public endpoint).

**Normalized mapping (per message event)**:
| Normalized | Source |
|---|---|
| `source` | `"whatsapp"` (constant) |
| `sender` | `contacts[0].profile.name` else `messages[].from` |
| `content` | `text.body` when `type == "text"`; else `""` |
| `message_type` | `"text"` when `type == "text"`; else `"media"` |
| `external_message_id` | `messages[].id` (dedup key) |
| `received_at` | server UTC now |

---

## 3. POST /webhooks/simulate — Simulate an Incoming Message

**Purpose**: Mirror of the old simulated webhook POST so the frontend
simulate form keeps working on the same ingestion path.

**Authentication**: **Required** — JWT session (`Depends(get_current_user)`).

**Request Body**:
```json
{ "sender": "Alice", "message": "Send me the slides tonight." }
```

**Success Response** (HTTP 200): the stored message response — same shape as
`POST /messages` (id, sender, content, source, status, state, ai_analysis,
created_at, updated_at, plus optional `received_at`). `source` resolves to
`"simulate"`, `message_type` to `"text"`, no `external_message_id`.

**Error Responses**: 401 unauthenticated · 400 missing/invalid body fields.

**Normalized mapping**:
| Normalized | Value |
|---|---|
| `source` | `"simulate"` |
| `sender` / `content` | from request body |
| `message_type` | `"text"` |
| `external_message_id` | absent (exempt from dedup) |
| `received_at` | server UTC now |
| `user_id` | from authenticated session |

---

## 4. Environment Variables (this feature)

| Variable | Source | Required | Notes |
|---|---|---|---|
| `WHATSAPP_APP_SECRET` | Meta portal → App Settings → Basic | **Yes (NEW)** | HMAC key for `X-Hub-Signature-256` |
| `WHATSAPP_PHONE_NUMBER_ID` | Meta portal | Yes | Owner filter for inbound delivery |
| `WHATSAPP_VERIFY_TOKEN` | Developer-created | Yes | GET verification handshake |

Required vars now `backend/.env` must contain all five (013 list + App
Secret). No variables new to simulate — it uses the session JWT only.

## 5. Contract Change Log (vs Day 22)

| Change | Old (013/Day 22) | New (014) |
|---|---|---|
| POST auth | JWT via `get_current_user` | None; `X-Hub-Signature-256` required |
| POST body | `{sender, message, timestamp}` fake | Real Meta nested payload |
| POST response | message JSON | `{"status": "ok"}` (200 acknowledge) |
| Dedup | time-window content match | unique `external_message_id` |
| AI timing | synchronous in request | background task after 200 |
| Simulate | POST `/webhooks/whatsapp` | POST `/webhooks/simulate` (JWT) |