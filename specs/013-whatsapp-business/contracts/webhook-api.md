# API Contracts: WhatsApp Business Integration Research + Setup

**Feature**: 013-whatsapp-business
**Date**: 2026-08-26
**Phase**: 1 (Design)

## Webhook Endpoints

### GET /webhooks/whatsapp — Meta Webhook Verification

**Purpose**: Respond to Meta's verification challenge when the webhook
is configured in the Developer portal.

**Authentication**: NONE (Meta cannot send JWT cookies)

**Request**:
```
GET /webhooks/whatsapp?hub.mode=subscribe&hub.verify_token=<token>&hub.challenge=<code>
```

**Query Parameters**:
| Parameter | Type | Required | Description |
|---|---|---|---|
| `hub.mode` | string | Yes | Must be `"subscribe"` |
| `hub.verify_token` | string | Yes | Must match `WHATSAPP_VERIFY_TOKEN` env var |
| `hub.challenge` | string | Yes | Random string to echo back |

**Success Response** (HTTP 200):
```
<challenge_value>
```
Plain text body containing the `hub.challenge` value.

**Failure Response** (HTTP 403):
```
Verification failed
```

**Logic**:
1. If `hub.mode != "subscribe"` → 403
2. If `hub.verify_token != env.WHATSAPP_VERIFY_TOKEN` → 403
3. Otherwise → 200 with `hub.challenge` as body

---

### POST /webhooks/whatsapp — Receive Incoming Messages

**Purpose**: Receive incoming WhatsApp message events from Meta.

**Authentication**: X-Hub-Signature-256 HMAC validation (Day 22:
optional for initial testing; Day 23: required)

**Request Headers**:
| Header | Type | Required | Description |
|---|---|---|---|
| `X-Hub-Signature-256` | string | Yes | HMAC-SHA256 signature of raw body |
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

**Success Response** (HTTP 200):
```json
{
  "status": "ok"
}
```

**Note**: Day 22 response is minimal — just acknowledge receipt. Day 23
will add message storage and AI pipeline integration.

**Error Response** (HTTP 403):
```json
{
  "error": "Invalid signature"
}
```

---

## Environment Variables

| Variable | Source | Required | Description |
|---|---|---|---|
| `WHATSAPP_PHONE_NUMBER_ID` | Meta portal | Yes | Identifies the Business phone number |
| `WHATSAPP_BUSINESS_ACCOUNT_ID` | Meta portal | Yes | Identifies the WhatsApp Business Account |
| `WHATSAPP_ACCESS_TOKEN` | Meta portal | Yes | Authenticates API calls (temporary) |
| `WHATSAPP_VERIFY_TOKEN` | Developer-created | Yes | Shared secret for webhook verification |
| `WHATSAPP_APP_SECRET` | Meta portal | Day 23 | Used for signature verification |

## Status Codes

| Code | Meaning | When |
|---|---|---|
| 200 | Success | Verification passed or message received |
| 403 | Forbidden | Invalid verify token or signature |
| 400 | Bad Request | Malformed webhook payload |
| 500 | Server Error | Backend processing failure |
