# Quickstart: Task Extraction & Deadline Detection

**Feature**: 004-task-extraction-deadline
**Date**: 2026-08-20

## Prerequisites

- Python 3.11+
- Node.js 18+
- MongoDB running on localhost:27017
- GROQ_API_KEY set in `backend/.env`

## Setup

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Backend runs on http://localhost:8000

### Frontend

```bash
npm install
npm run dev
```

Frontend runs on http://localhost:3000

## Testing Task Extraction

### Via API (curl)

```bash
# Message with task + deadline
curl -X POST http://localhost:8000/messages \
  -H "Content-Type: application/json" \
  -d '{"sender": "Ali", "content": "Send me the FYP slides tonight.", "source": "whatsapp"}'

# Verify task was extracted
curl http://localhost:8000/tasks

# Message with no task (informational)
curl -X POST http://localhost:8000/messages \
  -H "Content-Type: application/json" \
  -d '{"sender": "System", "content": "FYI server maintenance tonight.", "source": "gmail"}'

# Verify no task was created
curl http://localhost:8000/tasks
```

### Via Dashboard

1. Open http://localhost:3000/dashboard
2. Use the "Simulate Message" form
3. Enter a message with a task: "Review the slides and send feedback by Thursday"
4. Verify:
   - Message card shows a task count badge
   - Navigate to Tasks page -> task appears with description and deadline

### Via Webhook

```bash
curl -X POST http://localhost:8000/webhooks/whatsapp \
  -H "Content-Type: application/json" \
  -d '{"sender": "Teacher", "message": "Submit the report by Friday.", "timestamp": "2026-08-20T10:00:00Z"}'
```

## Expected Behavior

| Message | Tasks Extracted | Deadline | Priority |
|---------|----------------|----------|----------|
| "Send me the FYP slides tonight" | 1 task: "Send FYP slides" | "tonight" | urgent |
| "Can you review this document?" | 1 task: "Review document" | null | normal |
| "I'll send you the files tomorrow" | 0 tasks | - | low |
| "FYI server down tomorrow" | 0 tasks | - | low |
| "ASAP: submit the form" | 1 task: "Submit the quarterly form" | "ASAP" | urgent |
| "Prepare slides next week" | 1 task: "Prepare slides" | "next week" | normal |
| "Review before the meeting" | 1 task: "Review the document" | "before the meeting" | normal |
| "Meeting notes from today" | 0 tasks | - | low |
| "Can you check this email?" | 1 task: "Check this email" | null | normal |

## Verifying No Deadline Invention

Send these messages and verify `deadline` is null:

```bash
# No deadline mentioned
curl -X POST http://localhost:8000/messages \
  -H "Content-Type: application/json" \
  -d '{"sender": "Bob", "content": "Can you check this email?", "source": "gmail"}'

# Deadline is for sender, not recipient
curl -X POST http://localhost:8000/messages \
  -H "Content-Type: application/json" \
  -d '{"sender": "Alice", "content": "I will finish the report by Friday.", "source": "whatsapp"}'
```

The first should produce a task with `deadline: null`. The second should
produce 0 tasks (sender's promise, not recipient action).

## Running Tests

```bash
cd backend
python -m pytest test_task_extraction.py -v
```

13 tests covering: extraction, no-false-positives, deadline preservation,
graceful fallback, edge cases (long messages, non-English), and DB storage.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /messages | Create message (triggers AI analysis + task extraction) |
| GET | /messages | List all messages |
| GET | /tasks | List all tasks |
| PUT | /tasks/{id}/status | Update task status (pending/in_progress/completed) |
| DELETE | /tasks/{id} | Delete a task |
| POST | /webhooks/whatsapp | WhatsApp webhook (triggers analysis + extraction) |

## Troubleshooting

- **Tasks not appearing**: Check GROQ_API_KEY is set in `backend/.env`
- **AI analysis pending**: Check backend logs for Groq API errors
- **Tasks page empty**: Ensure messages have been sent and analyzed
- **Dashboard not updating**: Refresh the page to see latest tasks
