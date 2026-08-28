# Quick Start: AI Orchestrator — Day 24 Runbook

**Feature**: 015-ai-orchestrator | **Date**: 2026-08-29 | **Phase**: 1 (Design)

## Prerequisites

- Backend running as in Day 23 (`cd backend && python -m uvicorn main:app ...`)
- MongoDB running; `.env` already contains `GROQ_API_KEY`, `GROQ_MODEL`
- Dashboard frontend running (`npm run dev`) on the same session

## 1. Verify the routing table (no live LLM required)

```powershell
cd backend
python -c "from services.ai.routing import decide_routing; print(decide_routing('Send me the slides tonight.'))"
python -c "from services.ai.routing import decide_routing; print(decide_routing('ok'))"
python -c "from services.ai.routing import decide_routing; print(decide_routing('The meeting is tomorrow'))"
python -c "from services.ai.routing import decide_routing; print(decide_routing('أرسل الملفات'))"
```

Expect: the first = all five agents + `llm_call_used=True`; `"ok"` =
`needs_llm=False`; tomorrow-case = deadline on + task off; Arabic = full
default.

## 2. Exercise the Orchestrator

```powershell
cd backend
python -c "import asyncio; from services.ai.orchestrate import process_message; asyncio.run(process_message('hi', message_id='m1', user_id='demo'))"
```

Expect a completed, `provider="rule-based"` result, `routing.llm_call_used=false`.

## 3. End-to-end through the app

1. Start FastAPI (`uvicorn main:app --reload` in `backend/`).
2. In the Dashboard use the Simulate form and send a **trivial** greeting
   (`hi`): the message card renders normally (priority normal); afterwards in
   MongoDB (`db.messages`) the document's `ai_analysis` carries
   `status:"completed"`, `provider:"rule-based"`, and
   `routing.llm_call_used=false`.
3. Simulate a rich message (`Send me the slides tonight.`): full five-field
   analysis; `routing.agents_run` = all five; `routing.triggers` = `["send",
   "tonight"]`; `llm_call_used=true`.
4. Simulate a long FYI with no action words: `routing.agents_run` =
   `["priority","summary"]`; `tasks_extracted` and `deadlines` are empty and
   the `tasks` collection received no insert.
5. Confirm the NEEDS ATTENTION flag still appears only where the unchanged
   attention rules say so.
6. Send a media/webhook message (or an empty-text delivery): stored stub with
   `status:"skipped"` and `routing.skip_reason="no analyzable content"`.

## 4. Dashboard contract check

- Open any message: card shows priority, confidence, summary
  (when present), tasks/deadlines (when present) — identical to yesterday's
  UI. The `routing` key is invisible to the UI by design.
- Inbox counts (`all/normal/urgent/important`, attention) behave exactly as
  before.

## 5. Run the full test suite

```powershell
cd backend
python -m pytest tests/ -q
python test_task_extraction.py
python test_attention_pipeline.py
```

## 6. Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `routing` missing from `GET /messages` response | `routing` not declared on `AIAnalysis` — Step 2 of plan; Pydantic drops undeclared keys |
| Tasks created for a msg whose task agent was skipped | `run_tasks` gate missing in `analyze_message` — plan Step 2 |
| Trivial message still hits the LLM | `decide_routing` sets `needs_llm=True`; check triggers/`TRIVIAL_PHRASES` match |
| Arabic message routed as trivial | Verify `has_non_latin_script` forces full default |
| Two provider calls in tests | Orchestrator wired to call `analyze_message` directly instead of the shared single-call path |