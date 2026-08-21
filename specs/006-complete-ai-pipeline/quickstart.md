# Quickstart: Complete AI Pipeline — Run & Verify

**Feature**: 006-complete-ai-pipeline

## Prerequisites

- MongoDB running locally
- `backend/.env` with Groq API key (existing setup)
- Node modules installed (`npm install`)

## 1. Start the stack

```powershell
# Terminal 1 — backend
cd backend; uvicorn main:app --reload --port 8000

# Terminal 2 — frontend
npm run dev
```

## 2. Run backend tests

```powershell
cd backend; python -m pytest test_attention_pipeline.py -v
```

Expected: all attention-rule tests pass (R1 flag, R2 flag, no-flag cases,
reason invariants).

## 3. End-to-end verification (the Day 14 demo)

### Case A — flagged message (R1)

```powershell
$body = @{ sender = "Ali"; message = "Please send the FYP slides tonight."; timestamp = $null } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/webhooks/whatsapp" -Method Post -Body $body -ContentType "application/json"
```

Verify response `data.ai_analysis`:
- `needs_attention == true`
- `attention_reason == "A task with a near deadline was detected."`
- `tasks_extracted[0].description` mentions slides; `deadline == "Tonight"`

Then open http://localhost:3000/dashboard:
- 🔴 NEEDS ATTENTION card appears at top with task, "whatsapp • Ali",
  Deadline: Tonight, Why it matters line, Recommended line.

### Case B — unflagged message

Send `"Hey, how was your weekend?"` → card shows WITHOUT badge/reason;
appears in normal list only.

### Case C — duplicate protection

Re-send Case A's exact payload within 10 minutes → still exactly ONE
message document for it (check dashboard count / `GET /messages`).

### Case D — Attention page

Open http://localhost:3000/attention → flagged cards from Cases A appear;
unflagged messages do not.

### Case E — graceful degradation (optional)

Temporarily invalidate the API key, send a message → message still stored
and displayed with default values, no crash, no false flag. Restore key.

## 4. Definition of Done checklist

- [ ] All pytest tests pass
- [ ] Cases A–D verified manually in browser
- [ ] Card field order matches spec exactly
- [ ] No duplicates after re-sending (Case C)
- [ ] Existing features unaffected (inbox, tasks page, delete)
