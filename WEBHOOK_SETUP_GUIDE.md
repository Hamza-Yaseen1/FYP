# WhatsApp Webhook Setup Guide

Your webhook endpoint is **working correctly**. The issue is that Meta isn't sending messages to it.

## ✅ What's Working

1. ✅ Backend webhook endpoint is running
2. ✅ GET verification endpoint responds correctly
3. ✅ POST endpoint receives and stores messages
4. ✅ WhatsApp connection exists in database
5. ✅ Signature verification works
6. ✅ Message ingestion and AI analysis works

## ❌ What's Not Working

Meta is not sending webhook POSTs when you send messages to your test number.

## 🔧 Fix: Configure Meta Webhook

### Step 1: Access Meta Developer Dashboard

1. Go to https://developers.facebook.com/apps
2. Select your WhatsApp app
3. Go to **WhatsApp > Configuration**

### Step 2: Configure Webhook

1. Find the **Webhook** section
2. Click **Edit** or **Configure Webhook**

3. Enter these values:
   ```
   Callback URL: https://blazer-salvage-hypnosis.ngrok-free.dev/webhooks/whatsapp
   Verify Token: my_fyp_secret_123
   ```

4. Click **Verify and Save**
   - Meta will send a GET request to verify your endpoint
   - Your endpoint should respond with the challenge
   - You should see ✅ "Webhook verified successfully"

### Step 3: Subscribe to Webhook Events

In the **Webhook fields** section, make sure you have subscribed to:
- ✅ `messages` (required - to receive incoming messages)

Other optional but useful fields:
- ✅ `message_status` (to track message delivery status)
- ✅ `messaging_product` (general updates)

### Step 4: Test the Webhook

1. **Method 1: Send a message from your phone**
   - Send a WhatsApp message from your personal phone to the test number
   - Check your app's inbox at http://localhost:3000/inbox

2. **Method 2: Use Meta's Test Button**
   - In the webhook configuration, look for "Test" or "Send Test Event"
   - Meta will send a sample webhook POST
   - Check the logs: `Get-Content backend\uvicorn.out.log -Tail 20`

3. **Method 3: Use the simulate script**
   ```bash
   cd backend
   python -m scripts.simulate_meta_webhook
   python -m scripts.test_webhook
   ```

## 🐛 Troubleshooting

### Issue: "Webhook verification failed"

**Cause:** Your ngrok tunnel or backend is not accessible from the internet

**Fix:**
1. Make sure backend is running: `Get-Process python`
2. Make sure ngrok is running: `Get-Process ngrok`
3. Test the endpoint yourself:
   ```powershell
   Invoke-WebRequest -Uri "https://blazer-salvage-hypnosis.ngrok-free.dev/webhooks/whatsapp?hub.mode=subscribe&hub.verify_token=my_fyp_secret_123&hub.challenge=test" -Method GET -Headers @{"ngrok-skip-browser-warning"="true"}
   ```

### Issue: Verification works but no messages received

**Cause:** You haven't subscribed to the `messages` webhook field

**Fix:**
1. Go to Webhook configuration in Meta dashboard
2. Find "Webhook fields" section
3. Make sure `messages` is checked ✅
4. Click Save

### Issue: ngrok URL keeps changing

**Cause:** Free ngrok tunnels use random URLs that change on restart

**Fix:**
1. Get a static ngrok domain (free tier allows 1 static domain)
2. Or update the webhook URL in Meta dashboard each time ngrok restarts
3. Current ngrok URL: `https://blazer-salvage-hypnosis.ngrok-free.dev`

### Issue: Messages only work in one direction

**Current situation:** You can send from test number → your phone, but not your phone → test number

**Cause:** Meta only sends webhooks for messages **sent TO your business number**. Messages sent FROM your business number won't trigger webhooks.

**Expected behavior:**
- Your phone → Test number = ✅ Creates webhook POST → Appears in your inbox
- Test number → Your phone = ❌ No webhook (this is sent by you via API, not received)

## 📊 Verify Configuration

Run these commands to verify everything:

```powershell
# Check backend is running
Get-Process python

# Check ngrok is running
Get-Process ngrok

# Get current ngrok URL
curl.exe http://127.0.0.1:4040/api/tunnels

# Test webhook GET (verification)
Invoke-WebRequest -Uri "https://blazer-salvage-hypnosis.ngrok-free.dev/webhooks/whatsapp?hub.mode=subscribe&hub.verify_token=my_fyp_secret_123&hub.challenge=test" -Method GET

# Check database setup
cd backend
python -m scripts.test_webhook

# Simulate a webhook POST
python -m scripts.simulate_meta_webhook
```

## 📝 Environment Variables

Make sure these are set in `backend/.env`:

```env
WHATSAPP_PHONE_NUMBER_ID=1308658958991189
WHATSAPP_VERIFY_TOKEN=my_fyp_secret_123
WHATSAPP_APP_SECRET=d1a2667f6b798b664a8fbeded9a3a4e3
NGROK_URL=https://blazer-salvage-hypnosis.ngrok-free.dev
```

## ✅ Next Steps

1. Open Meta Developer Dashboard
2. Configure the webhook URL with your ngrok URL
3. Subscribe to `messages` events
4. Send a test message from your phone
5. Check your inbox!
