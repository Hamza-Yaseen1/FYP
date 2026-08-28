# Quickstart: WhatsApp Business Integration Research + Setup

**Feature**: 013-whatsapp-business
**Date**: 2026-08-26
**Phase**: 1 (Design)

## Prerequisites

- Python 3.11+ with FastAPI installed
- Node.js 18+ (for ngrok)
- A Facebook/Meta account
- The backend server running locally

## Step 1: Create Meta Developer Account

1. Go to `https://developers.facebook.com`
2. Log in with your Facebook/Meta account
3. If prompted, accept the Meta Developer terms
4. Your developer account is now active

## Step 2: Register WhatsApp Business App

1. In the Meta Developer portal, click "My Apps" → "Create App"
2. Select "Business" type
3. Enter App Name: `Communication AI`
4. Enter contact email
5. Click "Create App"
6. In the App Dashboard, click "Add Products"
7. Find "WhatsApp" → click "Set up"
8. A WhatsApp Business Account is created or linked

## Step 3: Collect Credentials

1. In the App Dashboard, go to WhatsApp → API Setup
2. Copy the **Phone Number ID** (shown next to the test number)
3. Copy the **Temporary Access Token** (click "Generate" if needed)
4. Go to WhatsApp → Getting Started → copy the **WhatsApp Business Account ID**
5. Generate a random verify token string (e.g., `my_secret_verify_token_123`)

## Step 4: Store Credentials in `.env.local`

Add these lines to `backend/.env.local`:

```bash
WHATSAPP_PHONE_NUMBER_ID=<paste Phone Number ID here>
WHATSAPP_BUSINESS_ACCOUNT_ID=<paste WABA ID here>
WHATSAPP_ACCESS_TOKEN=<paste Temporary Access Token here>
WHATSAPP_VERIFY_TOKEN=my_secret_verify_token_123
```

**Verify**:
```bash
git status  # .env.local should NOT appear
```

## Step 5: Start Backend Server

```bash
cd backend
uvicorn main:app --reload --port 8000
```

Verify the server is running:
```bash
curl http://localhost:8000/health
# Should return: {"status": "ok"}
```

## Step 6: Start ngrok Tunnel

In a new terminal:
```bash
ngrok http 8000
```

Copy the HTTPS URL (e.g., `https://abcd1234.ngrok-free.app`).

**Verify the tunnel works**:
```bash
curl https://abcd1234.ngrok-free.app/health
# Should return: {"status": "ok"}
```

## Step 7: Configure Webhook in Meta Portal

1. In the Meta Developer portal, go to WhatsApp → Configuration → Webhook
2. Click "Edit" next to Callback URL
3. Enter: `https://<your-ngrok-url>/webhooks/whatsapp`
4. Enter the Verify Token: `my_secret_verify_token_123` (same as in .env.local)
5. Click "Verify and Save"
6. The portal should show the webhook as "Verified"

## Step 8: Test Webhook Verification

The GET verification should have succeeded in Step 7. If it failed:
- Check the ngrok tunnel is active
- Check the backend is running
- Check the verify token matches between Meta portal and `.env.local`
- Check the backend logs for the verification request

## Step 9: Send Test Message

1. In the Meta Developer portal, go to WhatsApp → API Setup
2. Send a test message to the test phone number
3. Check the backend logs — you should see the webhook payload arrive
4. The POST endpoint will process the message through the AI pipeline

## Step 10: Verify End-to-End

1. Open the dashboard at `http://localhost:3000/dashboard`
2. The test message should appear with AI analysis
3. Check MongoDB — the message is stored with `source: "whatsapp"`

## Troubleshooting

| Problem | Solution |
|---|---|
| ngrok tunnel won't start | Check port 8000 is in use by the backend |
| Webhook verification fails | Check verify token matches; check backend logs |
| No test messages arrive | Check ngrok is active; Meta may need a few seconds |
| Access Token expired | Generate a new one in Meta portal API Setup |
| Backend crashes on webhook | Check backend logs; the GET endpoint must not require auth |

## What's Ready After Day 22

- Meta Developer account with WhatsApp Business App
- Webhook verified and receiving test messages
- Credentials stored securely in `.env.local`
- Official message flow documented in `research.md`
- Backend can receive and log real Meta webhook payloads

## What's Done in Day 23

- Parse real Meta webhook payloads (nested structure)
- Map Meta fields to existing message schema
- Store received messages in MongoDB with proper `user_id`
- Integrate with AI pipeline (priority, summary, tasks)
- Handle different message types (text, image, etc.)
- Implement X-Hub-Signature-256 verification
