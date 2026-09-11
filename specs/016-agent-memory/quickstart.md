# Quick Start: Agent Memory / Context — Day 25 Runbook

**Feature**: 016-agent-memory | **Date**: 2026-08-29 | **Phase**: 1 (Design)

## Prerequisites

- Backend running as in Day 24 (`cd backend && python -m uvicorn main:app`)
- MongoDB running; `.env` has `GROQ_API_KEY`, `GROQ_MODEL`
- Dashboard frontend running (`npm run dev`) on the same session

## 1. Verify the link rule (no live LLM required)

```powershell
cd backend
python -c "from services.threads import normalize_sender; print(normalize_sender('  Ali  '))"
python -c "from services.threads import LINK_WINDOW_MINUTES; print(LINK_WINDOW_MINUTES)"
```

Expect: `ali`, `60`.

## 2. Linked pair end-to-end (the headline scenario)

1. Start FastAPI; in the Dashboard Simulate form send:
   **"Can you send the report?"** (sender `ali`) →
   stored with `messageId`, `threadId=null`, `conversationId=null`
   (first message, no link).
2. Immediately send **"Need it before our meeting."** (same sender) →
   within 60 minutes so it links: this message AND the first now carry
   `threadId` = the FIRST message's `_id`, `conversationId` = same.
3. Inspect the first message in MongoDB (`db.messages.find(
   {threadId: <id>})`): its `ai_analysis` may now include
   `context_updates: [{field:"deadline", value:"before the meeting",
   source_message_id:<second _id>, reason:"…", applied_at:"…"}]`.
   Original analysis fields are untouched.
4. Dashboard: both messages still render as their own cards, fully populated —
   no merged/duplicate cards, no nulls.

## 3. Edge paths

- **Standalone regression**: send one message from a different sender →
  `threadId`/`conversationId` null, analysis identical to Day 24.
- **Out-of-window**: send again from the SAME sender after > 60 minutes →
  no link; analysis is standalone.
- **Channel mismatch**: simulate vs web vs whatsapp count as different
  `source` → never linked.
- **Trivial follow-up**: send `ok` right after a message → links (data) but
  still takes the zero-LLM trivial path; `routing.llm_call_used=false`.
- **Isolation**: register a second user, message on the same simulate channel
  with the same sender name → their thread is separate; neither thread ever
  contains the other user's messages.
- **Duplicate delivery**: resend the same `external_message_id` → existing id
  returned, no re-link, no re-analysis.

## 4. Dashboard contract check

- Cards read stored results only; the new identity/context fields are
  invisible to the UI by design (same as Day 24's `routing`).
- Inbox counts, NEEDS ATTENTION, tasks, and settings behave exactly as before.

## 5. Clean-up check

- `backend/tests/` — run `python -m pytest tests/ -q` (300s shell timeout):
  full suite green including `test_threads.py` and `test_context_ai.py`.
- Grep for memory-framework artifacts: `rg -i "vector|embedding|rag" backend/`
  → only documentation mentions, zero runtime imports (SC-008).
- `npm run lint`, `npx tsc --noEmit` (frontend untouched — should be no-op);
  `npm run build` green if touched at all.