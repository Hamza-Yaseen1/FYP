# Research: WhatsApp Business Integration Research + Setup

**Feature**: 013-whatsapp-business
**Date**: 2026-08-26
**Phase**: 0 (Research)

## 1. Meta Developer Platform Setup

### Decision: Use Meta Developer Portal (web UI) for app creation

**Rationale**: The Meta Developer portal is the only official way to
register a WhatsApp Business App. There is no CLI or API for app
creation — it must be done through the browser at
`https://developers.facebook.com`.

**Steps**:
1. Go to `https://developers.facebook.com` and log in with a
   Facebook/Meta account
2. Click "My Apps" → "Create App"
3. Select "Business" type (required for WhatsApp Business API)
4. Fill in App Name (e.g., "Communication AI"), contact email
5. Create the app → App Dashboard appears
6. Click "Add Products" → find "WhatsApp" → click "Set up"
7. A WhatsApp Business Account (WABA) is auto-created or linked

**Alternatives considered**:
- Graph API for app creation: Not available — Meta requires manual
  portal setup for initial app registration

## 2. WhatsApp Business Cloud API Credentials

### Decision: Collect four credentials from Meta Developer portal

**Rationale**: These are the minimum credentials required for the
webhook verification and message reception flow as documented by Meta.

**Credentials to collect**:

| Credential | Where to find it | Purpose |
|---|---|---|
| Phone Number ID | WhatsApp → API Setup → Phone number | Identifies the sending/receiving number |
| WhatsApp Business Account ID | WhatsApp → Getting Started → WABA ID | Identifies the business account |
| Temporary Access Token | WhatsApp → API Setup → Access Token | Authenticates API calls (short-lived) |
| Webhook Verify Token | You create this (any random string) | Used in webhook verification handshake |

**Note**: The temporary Access Token expires in ~24 hours. For Day 22
testing this is sufficient. Day 23 will need a System User Token or
long-lived token.

**Alternatives considered**:
- Using only Phone Number ID + Access Token: Insufficient — Meta also
  requires WABA ID for certain API calls and the verify token for
  webhook setup

## 3. Webhook Verification Flow

### Decision: Implement GET-based verification challenge per Meta's spec

**Rationale**: Meta's webhook verification is a simple HTTP GET
challenge-response. When you register a webhook URL in the portal,
Meta sends a GET request with three query parameters:

```
GET /webhook/whatsapp?hub.mode=subscribe&hub.verify_token=YOUR_TOKEN&hub.challenge=CHALLENGE_CODE
```

The backend MUST:
1. Check `hub.mode == "subscribe"`
2. Check `hub.verify_token` matches the configured verify token
3. Respond with the `hub.challenge` value as plain text (HTTP 200)
4. If verification fails, respond with HTTP 403

**Security**: The verify token is a shared secret between Meta and the
backend. It is NOT the same as the Access Token. The verify token is
created by the developer and entered in both the Meta portal and the
backend environment.

**Alternatives considered**:
- POST-based verification: Not supported by Meta — verification is
  always GET-based
- Skipping verification: Not possible — Meta will not send messages
  without a verified webhook

## 4. ngrok for Public HTTPS Tunnel

### Decision: Use ngrok to expose local backend during development

**Rationale**: Meta requires the webhook endpoint to be publicly
accessible over HTTPS. During local development, ngrok creates a
secure tunnel from a public URL to the local server.

**Setup**:
1. Install ngrok: `npm install -g ngrok` or download from ngrok.com
2. Start the backend server on a known port (e.g., 8000)
3. Run: `ngrok http 8000`
4. Copy the HTTPS URL (e.g., `https://xxxx.ngrok-free.app`)
5. Register this URL + `/webhook/whatsapp` as the webhook in Meta portal

**Configuration**:
- ngrok free tier provides one static domain per account
- The tunnel must remain active during testing
- ngrok provides request inspection UI at `http://127.0.0.1:4040`

**Alternatives considered**:
- Cloudflare Tunnel: More complex setup, not needed for FYP scope
- Deploying to a public server: Adds deployment complexity on a
  research day; ngrok is simpler and sufficient
- localtunnel: Less reliable than ngrok; ngrok is the industry standard

## 5. Backend Webhook Endpoint

### Decision: Add a new GET verification endpoint alongside the existing POST

**Rationale**: The current `backend/routes/webhooks.py` only has a POST
endpoint for receiving simulated messages. Day 22 requires adding a GET
endpoint for Meta's webhook verification challenge.

**Current state** (`backend/routes/webhooks.py`):
- `POST /webhooks/whatsapp` — receives fake/simulated messages
- No GET endpoint for verification

**Day 22 changes**:
- Add `GET /webhooks/whatsapp` for Meta verification challenge
- The POST endpoint remains unchanged (Day 23 will modify it for real
  payloads)
- The GET endpoint must NOT require authentication (Meta cannot send
  JWT cookies)

**Security concern**: The GET endpoint is public (no auth). This is
required by Meta's verification flow. The verify token acts as the
authentication mechanism for this specific endpoint.

**Alternatives considered**:
- Separate verification endpoint (e.g., `/webhooks/whatsapp/verify`):
  Adds unnecessary complexity; Meta expects the callback URL itself
  to handle both GET (verification) and POST (messages)
- Adding auth to the GET endpoint: Breaks verification — Meta cannot
  authenticate with JWT

## 6. Environment Variable Structure

### Decision: Add four WhatsApp-specific env vars to `.env.local`

**Rationale**: All credentials MUST be in environment variables per
constitution Principle V and Day 22 security rules.

**Variables to add**:
```
WHATSAPP_PHONE_NUMBER_ID=<from Meta portal>
WHATSAPP_BUSINESS_ACCOUNT_ID=<from Meta portal>
WHATSAPP_ACCESS_TOKEN=<temporary token from Meta portal>
WHATSAPP_VERIFY_TOKEN=<developer-created random string>
```

**Security rules**:
- `.env.local` MUST be in `.gitignore` (already is)
- NEVER log these values
- NEVER return them in API responses
- The Access Token is the most sensitive — treat like a password

**Alternatives considered**:
- Storing in MongoDB: Violates constitution — credentials belong in
  env vars, not database
- Using a secrets manager: Overkill for FYP; env vars are sufficient

## 7. Official WhatsApp Webhook Payload Structure

### Decision: Document the payload structure for Day 23 reference

**Rationale**: Understanding the real payload structure is critical for
Day 23 implementation. The current fake payload (`{sender, message}`)
differs significantly from Meta's real structure.

**Meta webhook payload structure** (POST):
```json
{
  "object": "whatsapp_business_account",
  "entry": [{
    "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
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

**Key differences from current fake payload**:
- Real payload is deeply nested (`entry[0].changes[0].value.messages`)
- Real payload includes metadata, contacts, and message types
- Message ID is provided by Meta (for deduplication)
- Timestamp is a Unix epoch, not ISO string
- Multiple message types: text, image, audio, document, etc.

**Day 23 will need**: A parser that extracts the flat fields
(sender, content, timestamp, message_id) from the nested Meta
structure and maps them to the existing message schema.

## 8. Signature Verification

### Decision: Implement X-Hub-Signature-256 validation

**Rationale**: Meta signs every webhook request with an HMAC-SHA256
signature using the App Secret. This prevents spoofed requests.

**Verification flow**:
1. Receive the raw request body (bytes)
2. Compute HMAC-SHA256 using the App Secret as key
3. Compare with the `X-Hub-Signature-256` header value
4. If they don't match, reject with HTTP 403

**Note**: The App Secret is different from the Access Token. It's found
in the Meta Developer portal under App Settings → Basic → App Secret.
For Day 22, signature verification can be implemented but may be
skipped initially to focus on getting the basic flow working. It MUST
be in place before Day 23.

**Alternatives considered**:
- Skipping signature verification: Security risk — anyone could send
  fake webhook payloads. Must be implemented.
- Using IP whitelisting: Meta's IP ranges change; signature
  verification is more reliable

## Summary of Decisions

| Area | Decision | Key Reason |
|---|---|---|
| App creation | Meta Developer portal (web UI) | Only official method |
| Credentials | 4 values: Phone Number ID, WABA ID, Access Token, Verify Token | Minimum for webhook flow |
| Verification | GET challenge-response per Meta spec | Required by Meta |
| Public URL | ngrok tunnel to local backend | Simple, sufficient for FYP |
| Webhook endpoint | GET + POST on `/webhooks/whatsapp` | Meta expects single URL |
| Environment vars | 4 new vars in `.env.local` | Constitution requirement |
| Payload structure | Nested `entry[0].changes[0].value` | Official Meta format |
| Signature | X-Hub-Signature-256 HMAC validation | Security requirement |
