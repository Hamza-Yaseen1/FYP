# Quickstart: AI Recommended Action

**Date**: 2026-08-21
**Feature**: 005-ai-recommendation
**Branch**: 005-ai-recommendation

## Prerequisites

- Python 3.11+
- Node.js 18+
- MongoDB running locally or in Docker
- Groq API key in `.env.local` as `GROQ_API_KEY`

## Setup

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
npm install
npm run dev
```

## Testing the Feature

### 1. Send a message with clear action

```bash
curl -X POST http://localhost:8000/webhooks/whatsapp \
  -H "Content-Type: application/json" \
  -d '{"sender": "Test User", "message": "Please send the report before 5 PM"}'
```

**Expected response**:
```json
{
  "ai_analysis": {
    "priority": "urgent",
    "confidence": 0.85,
    "summary": "Report needs to be submitted before 5 PM.",
    "recommended_action": "Send the report before 5 PM",
    ...
  }
}
```

### 2. Send an informational message

```bash
curl -X POST http://localhost:8000/webhooks/whatsapp \
  -H "Content-Type: application/json" \
  -d '{"sender": "Test User", "message": "The meeting is at 3 PM tomorrow"}'
```

**Expected response**:
```json
{
  "ai_analysis": {
    "priority": "important",
    "recommended_action": "Review this message",
    ...
  }
}
```

### 3. Check the dashboard

1. Open http://localhost:3000/dashboard
2. Verify the recommended action appears below the summary for each message
3. Verify old messages show no recommended action (or "Review this message" if re-analyzed)

## API Response

The `GET /messages` endpoint now includes `recommended_action` in the response:

```json
{
  "id": "...",
  "sender": "Test User",
  "content": "Please send the report before 5 PM",
  "ai_analysis": {
    "priority": "urgent",
    "confidence": 0.85,
    "explanation": "Message contains explicit deadline...",
    "summary": "Report needs to be submitted before 5 PM.",
    "recommended_action": "Send the report before 5 PM",
    "tasks_extracted": [...],
    "deadlines": ["5 PM"],
    "provider": "groq",
    "analyzed_at": "2026-08-21T00:00:00Z",
    "status": "completed"
  }
}
```

## Troubleshooting

### Recommended action is empty

- Check Groq API key is set in `.env.local`
- Check backend logs for errors in `generate_recommendation()`
- Verify `actions.txt` prompt exists and is readable

### Recommended action is in wrong language

- The prompt should instruct the AI to match the message language
- If persistent, check the prompt in `backend/services/ai/prompts/actions.txt`

### Dashboard doesn't show recommended action

- Verify the frontend is using the latest API response
- Check browser console for errors
- Verify `MessageList.tsx` renders the `recommended_action` field
