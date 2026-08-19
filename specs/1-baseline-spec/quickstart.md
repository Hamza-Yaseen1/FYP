# Quickstart: Communication AI Development

**Date**: 2026-08-19
**Feature**: AI Intelligence Layer

## Prerequisites

- Python 3.11+
- Node.js 18+
- MongoDB running locally
- LLM API key (OpenAI, Groq, or Gemini)

## Setup

### 1. Backend

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Add AI dependencies
pip install openai groq google-generativeai

# Set environment variables
export LLM_PROVIDER=openai          # or "groq" or "gemini"
export OPENAI_API_KEY=sk-...        # if using OpenAI
export GROQ_API_KEY=gsk_...         # if using Groq
export GEMINI_API_KEY=...           # if using Gemini

# Run backend
uvicorn main:app --reload --port 8000
```

### 2. Frontend

```bash
# From project root
npm install
npm run dev
```

### 3. Verify

- Backend: http://localhost:8000/health
- Frontend: http://localhost:3000

## Testing AI Features

### Send Simulated Message

```bash
curl -X POST http://localhost:8000/webhooks/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "John",
    "message": "Hey, can you send me the project report by Friday? Also, we have a meeting tomorrow at 3pm."
  }'
```

**Expected Response**: Message with AI analysis including:
- Priority: "urgent" or "important" (has deadline)
- Tasks: ["Send project report"]
- Deadlines: ["Friday"]
- Actions: ["Reply", "Schedule meeting"]

### Test Different Message Types

**Urgent Message**:
```bash
curl -X POST http://localhost:8000/webhooks/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "Boss",
    "message": "URGENT: Client demo in 2 hours, need the final presentation now!"
  }'
```

**Casual Message**:
```bash
curl -X POST http://localhost:8000/webhooks/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "Friend",
    "message": "Hey, want to grab lunch sometime this week?"
  }'
```

**Long Message (triggers summary)**:
```bash
curl -X POST http://localhost:8000/webhooks/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "Colleague",
    "message": "Hi team, I wanted to share the quarterly report with everyone. The report covers our performance metrics, customer satisfaction scores, and revenue growth for Q2 2026. We saw a 15% increase in user engagement, 8% improvement in retention rates, and 22% growth in recurring revenue. The full report is attached. Please review before our team meeting on Thursday and come prepared with your questions and suggestions for Q3 planning."
  }'
```

### Check Messages on Dashboard

1. Open http://localhost:3000
2. Messages should appear within 10 seconds (auto-poll)
3. Each message shows:
   - Priority badge (Red/Orange/Blue/Gray)
   - Summary (if >200 chars)
   - Recommended actions
   - Task count (if tasks extracted)

### Test Task Management

```bash
# Get tasks
curl http://localhost:8000/tasks

# Complete a task
curl -X PUT http://localhost:8000/tasks/{task_id} \
  -H "Content-Type: application/json" \
  -d '{"status": "completed"}'
```

## Switching LLM Providers

Change the `LLM_PROVIDER` environment variable and restart backend:

```bash
# Use Groq (free, fast)
export LLM_PROVIDER=groq
export GROQ_API_KEY=gsk_...
uvicorn main:app --reload

# Use Gemini (free tier)
export LLM_PROVIDER=gemini
export GEMINI_API_KEY=...
uvicorn main:app --reload
```

## Troubleshooting

### AI Analysis Shows "pending"

- Check LLM API key is set correctly
- Check LLM_PROVIDER matches the key
- Check backend logs for error messages

### Slow Response Times

- OpenAI: 2-5 seconds typical
- Groq: 1-2 seconds typical
- Gemini: 2-4 seconds typical
- If slower, check network connectivity

### Messages Not Appearing

- Ensure MongoDB is running
- Check backend is on port 8000
- Check frontend is on port 3000
- Check browser console for API errors
