# Quick Start Guide - Communication AI

## 🚀 Get Up and Running in 5 Minutes

### Step 1: Add Your OpenAI API Key

1. Get your API key from: https://platform.openai.com/api-keys
2. Open `backend/.env`
3. Replace `your-openai-api-key-here` with your actual key:
   ```
   OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
   ```

### Step 2: Install Dependencies

```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend (if not already done)
cd ..
npm install
```

### Step 3: Start the Services

**Terminal 1 - Backend:**
```bash
cd backend
uvicorn main:app --reload
```
Backend will run on: http://localhost:8000

> **Same-origin API proxy:** the frontend calls `/api/*` (not `:8000` directly). `next.config.ts`
> rewrites `/api/:path*` → `http://localhost:8000/:path*`, so cookies work across both ports
> (host `localhost`) with no CORS. Override the backend target with `BACKEND_URL` if you run it
> elsewhere.

**Terminal 2 - Frontend:**
```bash
npm run dev
```
Frontend will run on: http://localhost:3000

### Step 4: Test the System

1. Open http://localhost:3000/dashboard
2. Scroll to "Simulate Message" section
3. Try these test messages:

**Test 1: Urgent Priority**
```
Sender: Boss
Message: Please send the presentation slides by 5 PM today. This is urgent for tomorrow's client meeting.
```

**Test 2: Task Extraction**
```
Sender: Supervisor
Message: Can you review the project requirements document and submit your feedback by Friday? Also, please schedule a meeting with the team for next week.
```

**Test 3: Normal Priority**
```
Sender: Friend
Message: Hey! Just wanted to share this interesting article I found. Check it out when you have time.
```

### Step 5: Verify AI Analysis

After sending each message:
1. Wait 2-3 seconds for analysis
2. Check the "Recent Messages" section
3. Open MongoDB Compass or your database client
4. Find the message in `communication_ai.messages` collection
5. Look for the `ai_analysis` field with:
   - `priority`: "urgent", "important", "normal", or "low"
   - `confidence`: 0.0 to 1.0
   - `summary`: Generated summary (if message is long)
   - `tasks_extracted`: List of tasks found
   - `recommended_actions`: Suggested next steps
   - `deadlines`: Extracted deadline strings

---

## 🔍 Troubleshooting

### Backend won't start
- Check if MongoDB connection works: `MONGO_URI` in `.env`
- Verify OpenAI API key is valid
- Run: `pip install -r requirements.txt` again

### Frontend won't start
- Run: `npm install` to ensure all packages are installed
- Check if port 3000 is already in use

### AI analysis not appearing
1. Check backend terminal for errors
2. Verify `OPENAI_API_KEY` is set correctly
3. Check if you have OpenAI API credits
4. Look at backend logs for error messages

### Message appears but no AI data
- AI analysis may have failed silently
- Check `ai_analysis.status` field in MongoDB:
  - `"completed"` = Success ✅
  - `"failed"` = Error ❌
  - `"pending"` = Not analyzed yet ⏳

---

## 📊 What to Expect

### API Endpoints Available:

**Messages:**
- `GET /messages` - List all messages
- `GET /messages/{id}` - Get single message
- `POST /messages` - Create message (with AI analysis)
- `PUT /messages/{id}` - Update message
- `DELETE /messages/{id}` - Delete message

**Webhooks:**
- `POST /webhooks/whatsapp` - Simulate WhatsApp message (with AI analysis)

**Health:**
- `GET /health` - Check if backend is running

### AI Analysis Time:
- Typical: 1-3 seconds per message
- Depends on: Groq API response time
- `POST /messages` and webhook ingestion are non-blocking: the message is stored immediately with
  `ai_analysis: null` and analysis completes in the background. The inbox auto-polls and re-renders
  ("Analyzing…" badge) once analysis lands, so no manual refresh is needed.
- Unknown/missing/pending analyses are bucketed as `pending` in analytics (kept visible, never dropped).
- Multi-worker note: uvicorn runs the Gmail poller in every worker; duplicate fetches are
  de-duplicated by the `{user_id, external_message_id}` index, so extra workers are safe.

### Current Limitations:
- ✅ Priority classification works
- ✅ Task extraction works
- ✅ Summary generation works
- ✅ Action recommendations work
- ⚠️ Frontend doesn't display AI results yet (next step!)
- ⚠️ No task management UI yet
- ⚠️ Dashboard shows hardcoded data

---

## 🎯 Current MVP Features

### What Works:
1. ✅ Message simulation
2. ✅ Message storage in MongoDB
3. ✅ AI priority classification
4. ✅ AI task extraction
5. ✅ AI summary generation
6. ✅ AI action recommendations
7. ✅ Dashboard displays messages
8. ✅ Auto-refresh every 10 seconds

### What's Next (Frontend Updates):
1. Display priority badges
2. Show AI summaries
3. Display extracted tasks
4. Show recommended actions
5. Dynamic summary cards
6. Real "Needs Attention" section

---

## 🧪 Testing Examples

### Test the API Directly:

**Create a message with AI analysis:**
```bash
curl -X POST http://localhost:8000/messages \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "Test User",
    "content": "Please review the report and submit feedback by tomorrow morning.",
    "source": "whatsapp",
    "status": "unread"
  }'
```

**Get all messages:**
```bash
curl http://localhost:8000/messages
```

**Simulate WhatsApp message:**
```bash
curl -X POST http://localhost:8000/webhooks/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "John Doe",
    "message": "Meeting at 3 PM today. Please confirm."
  }'
```

---

## 📁 Project Structure Reference

```
my-app/
├── backend/
│   ├── main.py                  # FastAPI app entry point
│   ├── database.py              # MongoDB connection
│   ├── .env                     # Environment variables (add OPENAI_API_KEY here!)
│   ├── requirements.txt         # Python dependencies
│   ├── models/
│   │   └── message.py           # Message and AIAnalysis models
│   ├── routes/
│   │   ├── messages.py          # Message CRUD endpoints
│   │   └── webhooks.py          # Simulation endpoint (with AI!)
│   └── services/
│       └── ai/
│           ├── analyzer.py      # Main AI orchestrator
│           ├── prompts/         # AI prompt templates
│           │   ├── priority.txt # Priority classification
│           │   ├── tasks.txt    # Task extraction
│           │   ├── summary.txt  # Summary generation
│           │   └── actions.txt  # Action recommendations
│           └── providers/
│               ├── base.py      # Abstract provider
│               └── openai.py    # OpenAI implementation
│
├── app/
│   └── (dashboard)/
│       └── dashboard/
│           └── page.tsx         # Main dashboard page
│
├── components/
│   ├── MessageList.tsx          # Message display component
│   └── SimulateMessage.tsx      # Message simulation form
│
├── specs/
│   └── 1-baseline-spec/
│       ├── spec.md              # Feature specification
│       ├── plan.md              # Implementation plan
│       └── tasks.md             # Task breakdown (NEW!)
│
├── CONSTITUTION.md              # Project principles
├── SPEC.md                      # Main specification
├── PLAN.md                      # Implementation plan
├── FIXES-APPLIED.md             # What was fixed today
└── QUICK-START.md               # This file
```

---

## 💡 Pro Tips

1. **Check backend logs**: Watch the terminal running `uvicorn` for AI analysis status
2. **Use MongoDB Compass**: Visual tool to inspect message documents and ai_analysis fields
3. **Test various message types**: Try urgent, casual, tasks, questions, FYI messages
4. **Monitor OpenAI usage**: Check your API usage at https://platform.openai.com/usage
5. **Cost awareness**: gpt-4o-mini is cheap (~$0.15 per 1M tokens), but monitor for FYP scale

---

## 🆘 Need Help?

### Common Issues:

**"OpenAI API key not found"**
- Solution: Add `OPENAI_API_KEY=sk-...` to `backend/.env`

**"Connection refused to MongoDB"**
- Solution: Check `MONGO_URI` in `backend/.env` is correct

**"Module 'openai' not found"**
- Solution: Run `pip install -r requirements.txt` in backend directory

**AI analysis shows "pending" or "failed"**
- Check backend terminal for error messages
- Verify OpenAI API key is valid
- Ensure you have API credits available

---

## ✅ Success Checklist

After following this guide, you should be able to:

- [ ] Backend starts without errors
- [ ] Frontend starts and shows dashboard
- [ ] Simulate a message successfully
- [ ] Message appears in "Recent Messages"
- [ ] MongoDB shows message with `ai_analysis` field
- [ ] AI analysis includes priority, confidence, summary, tasks, actions
- [ ] Backend logs show "AI analysis completed"

**If all checked, you're ready for Day 8! 🎉**

---

## 📞 Next Steps

1. ✅ Complete this Quick Start
2. 🔄 Test all the example messages
3. 🔜 Update frontend to display AI results (Priority 2)
4. 🔜 Implement task management UI (User Story 4)
5. 🔜 Polish dashboard with real data

---

**Current Status**: AI Backend Complete ✅ | Frontend Display Pending 🔄

**You're 80% done with the core AI features!**
