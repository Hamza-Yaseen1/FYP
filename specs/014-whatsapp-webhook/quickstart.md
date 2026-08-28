# Quickstart: Day 23 Real WhatsApp Webhook

**Feature**: 014-whatsapp-webhook | **Date**: 2026-08-28 | **Phase**: 1

Runbook to go from a verified-but-fake webhook to real message ingestion.

## Prerequisites

- Day 22 setup done: WABA, Phone Number ID, Verify Token, App Access/System
  User Token, ngrok, `POST` verification passing in the Meta portal.
- Access to the Meta Developer portal (`App Settings → Basic` for the App
  Secret).
- The app, frontend, and MongoDB running; a registered test user who has
  connected WhatsApp (so ownership can be resolved).

## Setup

1. **Add the App Secret**
   - Meta portal → App → Settings → Basic → copy **App Secret**.
   - `backend/.env`:
     ```
     WHATSAPP_APP_SECRET=<App Secret>
     WHATSAPP_PHONE_NUMBER_ID=<already set>
     ```
   - Also add an empty `WHATSAPP_APP_SECRET=` line to `backend/.env.example`.
   - Confirm `backend/.env` is NOT tracked by git.

2. **Make sure the DB index exists**
   - Start the backend once after Step 6 of the plan — the lifespan creates
     the unique partial index on `messages.external_message_id`.

3. **Expose the backend**
   - `ngrok http 8000`
   - Open `https://<ngrok-url>/health` → 200.
   - In Meta portal → WhatsApp → Configuration → Webhook:
     callback URL = `https://<ngrok-url>/webhooks/whatsapp`,
     Verify token = your token → Verify. If the URL changed since Day 22,
     re-verify (Meta requires a successful challenge per active URL).

## Test Flow (real message)

1. Log in to the app and ensure WhatsApp is connected (owner mapping).
2. From your phone, message the Business number: `Send me the slides tonight.`
3. Within ~30s the Dashboard shows the card with source **WhatsApp** and full
   AI analysis.
4. Verify one document only in MongoDB:
   ```javascript
   db.messages.find({ content: "Send me the slides tonight." })
   // expect a single row with external_message_id like "wamid.HBgz..."
   ```
5. Resend the same payload with a signed curl — count does not change
   (idempotence), and no second AI run:
   ```powershell
   $secret = (Get-Content backend/.env | Select-String 'WHATSAPP_APP_SECRET=.*').ToString().Split('=')[1]
   $body = '{"object":"whatsapp_business_account","entry":[{"id":"WABA","changes":[{"value":{"messaging_product":"whatsapp","metadata":{"display_phone_number":"+15550000000","phone_number_id":"<PHONE_NUMBER_ID>"},"contacts":[{"wa_id":"12345","profile":{"name":"Alice"}}],"messages":[{"from":"12345","id":"wamid.HBgzTEST","timestamp":"1700000000","type":"text","text":{"body":"Send me the slides tonight."}}]},"field":"messages"}]}]}'
   $sig = "sha256=" + [System.BitConverter]::ToString((New-Object System.Security.Cryptography.HMACSHA256([System.Text.Encoding]::UTF8.GetBytes($secret))).ComputeHash([System.Text.Encoding]::UTF8.GetBytes($body))).Replace("-","").ToLower()
   Invoke-RestMethod -Method Post -Uri http://localhost:8000/webhooks/whatsapp -Headers @{"X-Hub-Signature-256"=$sig} -ContentType "application/json" -Body $body
   ```
6. Send a photo from your phone → media-marked card (empty content,
   type media), message stored, count grows by one.
7. Tamper test: same curl with a flipped byte in the signature → HTTP 403,
   no document.
8. Simulate flow: use the in-app Simulate button → card with source
   **Simulate**, identical AI pipeline.

## Verify

- `cd backend; python -m pytest tests/ -q` → green
- See `plan.md → Definition of Done` for the full acceptance checklist.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| Meta webhook "Verification failed" | Verify token mismatch or callback URL not the running ngrok URL |
| Real message never arrives | Subscription set to `messages` field? ngrok tunnel alive? |
| 403 in ngrok inspector when phone sends | `WHATSAPP_APP_SECRET` missing/mismatched — fix `.env` and restart |
| Message arrives but no Dashboard card | Owner not resolvable: user has no `connections` row with provider=whatsapp, status=connected |
| Duplicate cards | Index not created (old backend process) — restart backend, check index |
| AI never populates | Check Groq key / analyze_message logs; card still renders (pending) |