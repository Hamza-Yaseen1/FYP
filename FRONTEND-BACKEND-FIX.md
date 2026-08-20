# Frontend-Backend Connection Fix

## 🔍 **Problem: Frontend Not Connected to Backend**

Quick diagnostic and fix guide.

---

## ✅ **Step 1: Verify Backend is Running**

### Check Backend Status:

**Open your backend terminal** and verify you see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

**If backend is NOT running:**
```bash
cd backend
uvicorn main:app --reload
```

### Test Backend Health:

**Method 1: Browser**
- Open: http://localhost:8000/health
- Should show: `{"status":"ok"}`

**Method 2: Command Line**
```bash
curl http://localhost:8000/health
```

**Method 3: PowerShell**
```powershell
Invoke-WebRequest -Uri http://localhost:8000/health
```

**✅ If you see `{"status":"ok"}`, backend is running!**

---

## ✅ **Step 2: Verify Frontend is Running**

### Check Frontend Status:

**Open your frontend terminal** and verify you see:
```
  ▲ Next.js 16.x.x
  - Local:        http://localhost:3000
  ✓ Ready in 2.5s
```

**If frontend is NOT running:**
```bash
npm run dev
```

### Test Frontend:

Open browser: http://localhost:3000/dashboard

**✅ If dashboard loads, frontend is running!**

---

## ✅ **Step 3: Test Connection Directly**

### Open Browser Console:

1. Open http://localhost:3000/dashboard
2. Press **F12** (open DevTools)
3. Go to **Console** tab
4. Run this command:

```javascript
fetch('http://localhost:8000/health')
  .then(res => res.json())
  .then(data => console.log('✅ Backend connected:', data))
  .catch(err => console.error('❌ Connection failed:', err))
```

**Expected Output:**
```
✅ Backend connected: {status: "ok"}
```

**If you see error:**
```
❌ Connection failed: TypeError: Failed to fetch
```
→ Backend is not running or CORS issue

---

## ✅ **Step 4: Test Message API**

### In Browser Console (F12):

```javascript
fetch('http://localhost:8000/messages')
  .then(res => res.json())
  .then(data => console.log('✅ Messages fetched:', data.length, 'messages'))
  .catch(err => console.error('❌ Failed:', err))
```

**Expected:** Should show count of messages

---

## ✅ **Step 5: Check Network Tab**

### In Browser DevTools:

1. Open http://localhost:3000/dashboard
2. Press **F12**
3. Go to **Network** tab
4. Refresh page or simulate a message
5. Look for requests to `localhost:8000`

**Look for:**
- ✅ `GET http://localhost:8000/messages` - Status: 200
- ✅ `POST http://localhost:8000/webhooks/whatsapp` - Status: 200

**If you see:**
- ❌ Status: Failed or (cancelled)
  → Backend not running
- ❌ Status: 0 or CORS error
  → CORS configuration issue
- ❌ Status: 404
  → Wrong endpoint URL

---

## 🔧 **Common Issues & Fixes**

### Issue 1: Backend Not Running

**Symptoms:**
- "Connection failed" in console
- Network requests show "Failed"
- Can't access http://localhost:8000/health

**Fix:**
```bash
cd backend
uvicorn main:app --reload
```

### Issue 2: Wrong Port

**Symptoms:**
- Backend running on different port

**Check backend terminal for actual port:**
```
INFO:     Uvicorn running on http://127.0.0.1:XXXX
```

**If not 8000, update frontend URLs:**

Edit `components/MessageList.tsx` and `components/SimulateMessage.tsx`:
```typescript
// Change from:
fetch("http://localhost:8000/messages")

// To actual port:
fetch("http://localhost:XXXX/messages")
```

### Issue 3: CORS Error

**Symptoms:**
- Console shows: "CORS policy: No 'Access-Control-Allow-Origin' header"

**Fix:**

Backend `main.py` should have:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue 4: Frontend Running on Different Port

**Check frontend terminal:**
```
- Local:        http://localhost:XXXX
```

**If not 3000:**

1. Stop frontend (Ctrl+C)
2. Start on port 3000:
```bash
npm run dev -- -p 3000
```

Or update backend CORS to include the actual port.

### Issue 5: Firewall Blocking Connection

**Symptoms:**
- Both backend and frontend running
- Still can't connect

**Fix (Windows):**
```powershell
# Allow Node.js and Python through firewall
# Run as Administrator
New-NetFirewallRule -DisplayName "Node.js" -Direction Inbound -Program "C:\Program Files\nodejs\node.exe" -Action Allow
New-NetFirewallRule -DisplayName "Python" -Direction Inbound -Program "C:\Python313\python.exe" -Action Allow
```

---

## 🧪 **Complete Test Sequence**

Run these in order to verify everything works:

### Test 1: Backend Health
```bash
curl http://localhost:8000/health
```
**Expected:** `{"status":"ok"}`

### Test 2: Get Messages
```bash
curl http://localhost:8000/messages
```
**Expected:** JSON array of messages (or empty array `[]`)

### Test 3: Simulate Message
```bash
curl -X POST http://localhost:8000/webhooks/whatsapp \
  -H "Content-Type: application/json" \
  -d '{"sender":"TestUser","message":"Test message"}'
```
**Expected:** `{"success":true, "message":"WhatsApp message received..."}`

### Test 4: Frontend Connection

Open browser console at http://localhost:3000/dashboard:
```javascript
fetch('http://localhost:8000/messages')
  .then(r => r.json())
  .then(d => console.log('✅ Connected! Messages:', d.length))
```

**Expected:** `✅ Connected! Messages: X`

---

## 📊 **Diagnostic Checklist**

Check each item:

- [ ] Backend terminal shows "Uvicorn running on http://127.0.0.1:8000"
- [ ] Frontend terminal shows "Local: http://localhost:3000"
- [ ] http://localhost:8000/health returns `{"status":"ok"}`
- [ ] http://localhost:3000/dashboard loads without errors
- [ ] Browser console shows no CORS errors
- [ ] Network tab shows successful requests to backend
- [ ] Can simulate a message and it appears in "Recent Messages"

**If ALL checked, connection is working!** ✅

---

## 🔄 **Quick Reset (If Nothing Works)**

### Complete Restart:

```bash
# 1. Stop both services (Ctrl+C in both terminals)

# 2. Restart backend
cd backend
uvicorn main:app --reload

# 3. In NEW terminal, restart frontend
cd ..  # back to project root
npm run dev

# 4. Open browser
# http://localhost:3000/dashboard

# 5. Check console for errors
```

---

## 🎯 **Still Not Working?**

### Run This Diagnostic:

**In project root directory:**

```bash
# Check if ports are in use
netstat -ano | findstr :8000
netstat -ano | findstr :3000

# If port 8000 or 3000 is in use by another process:
# Kill it (use PID from netstat output)
taskkill /PID <PID> /F
```

### Check Environment:

```bash
# Backend
cd backend
python -c "import fastapi, uvicorn, motor; print('✅ All backend packages installed')"

# Frontend  
cd ..
npm list next react react-dom
```

---

## ✅ **Success Indicators**

You know it's working when:

1. ✅ Can access http://localhost:8000/health
2. ✅ Can access http://localhost:3000/dashboard
3. ✅ Dashboard loads without console errors
4. ✅ Can simulate a message
5. ✅ Message appears in "Recent Messages" after refresh
6. ✅ No CORS errors in browser console

---

## 📝 **What to Tell Me**

If still not working, tell me:

1. **Backend terminal output** (copy/paste last 10 lines)
2. **Frontend terminal output** (copy/paste last 10 lines)
3. **Browser console errors** (F12 → Console tab → screenshot or copy errors)
4. **Network tab** (F12 → Network → filter by "localhost:8000" → screenshot)

This will help me diagnose the exact issue!
