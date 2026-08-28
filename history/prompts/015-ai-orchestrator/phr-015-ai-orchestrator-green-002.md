---
id: phr-015-ai-orchestrator-green-002
title: AI Orchestrator US2 Implementation
stage: green
date: 2026-08-29
surface: cli
model: big-pickle
feature: ai-orchestrator
branch: 015-ai-orchestrator
user: user
command: /sp.tasks (implementation)
labels: [green, day24, ai-orchestrator, us2, orchestration, single-call, entry-points]
links:
  spec: specs/015-ai-orchestrator/spec.md
  tasks: specs/015-ai-orchestrator/tasks.md
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - backend/services/ai/orchestrate.py
  - backend/services/ai/__init__.py
  - backend/services/webhook_ingest.py
  - backend/routes/messages.py
  - backend/tests/test_orchestrator.py
  - backend/tests/test_webhooks.py
  - backend/tests/test_messages.py
  - backend/tests/test_auth.py
  - backend/tests/test_user_isolation.py
tests:
  - pytest tests/ (118 passed)
---

## Prompt

Continue with Phase 4 – User Story 2 (single orchestration layer). Follow tasks.md
T010–T017: every inbound message must flow through one `orchestrate.process_message`
(not a direct `analyze_message` call), preserving a single LLM call, and attach a
routing record. Write the tests first (red), then implement, then stop for
confirmation before US3.

## Response snapshot

Implemented the US2 slice (T010–T017) on branch `015-ai-orchestrator`:

- T010–T012 (tests FIRST, confirmed red): 
  - `test_process_message_single_provider_call` + 2 companions in
    `backend/tests/test_orchestrator.py` (exactly 1 provider call for a rich
    message; `agents_run`/`agents_skipped` recorded for a deadline-only message;
    zero calls + `llm_call_used=False` for empty content).
  - T011 webhook entry spy (`test_simulate_ingest_routes_through_orchestrator`)
    in `backend/tests/test_webhooks.py` — asserts `process_message` invoked and
    `webhook_ingest` no longer exposes `analyze_message`.
  - T012 `POST /messages` spy in `backend/tests/test_messages.py` — asserts the
    response still has the existing shape incl. `ai_analysis.routing.skip_reason`.
- T013: new `backend/services/ai/orchestrate.py` — `process_message` =
  `decide_routing` → short-circuit when `not needs_analysis` (rule-based stub,
  zero calls) → else `await analyze_message(..., run_tasks=routing.run_task_extraction,
  routing=routing)` (gating is internal) → attach `analysis["routing"]`. Logs one
  routing decision per message. Never raises; pending/fallback still gets the record.
- T014: `_analyze_and_store` now calls `process_message` (persistence unchanged).
- T015: `create_message` now calls `process_message` (response unchanged).
- T016: `services/ai/__init__.py` exports `process_message` (kept `analyze_message`).
- T017: grep confirms `analyze_message` lives only in analyzer/orchestrate/scripts/tests;
  no bypass in routes/services entry points.
- Existing test patches re-pointed: `services.webhook_ingest.analyze_message` →
  `process_message` (test_webhooks x2, test_user_isolation x2) and
  `routes.messages.analyze_message` → `process_message` (test_auth, test_user_isolation).

Process note: `test_orchestrator`'s `asyncio.run` + real motor didn't mix (the
pre-existing persistence test and new process_message tests awaited motor writes
from throwaway loops → "Event loop is closed"/"Future attached to a different
loop" depending on which test ran first). Resolved by: persistence assertion now
runs end-to-end through POST /messages (real motor on the TestClient loop), and the
new process_message tests use a `_RecordingTasksCollection` fake so no test awaits
motor under `asyncio.run`. `conftest.py` unchanged in the end.

Result: full suite → 118 passed (113 + 5 new US2 tests), only pre-existing
`utcnow` DeprecationWarnings. `tasks.md` T010–T017 marked `[x]`. Stopped per the
one-slice-at-a-time instruction — US3 (Dashboard/routing persistence) is next.

## Outcome

- ✅ Impact: Every inbound message now funnels through one Orchestrator entry
  point; rich messages cost exactly one provider call; skipped/no-content
  messages short-circuit with a rule-based stub; every result carries an
  explainable `routing` record; no route/service bypasses the layer.
- 🧪 Tests: 5 new tests (3 orchestrator, 1 webhook, 1 messages); full suite
  118 passed / 0 failed.
- 📁 Files: services/ai/orchestrate.py (new), services/ai/__init__.py (edited),
  services/webhook_ingest.py (edited), routes/messages.py (edited),
  tests/test_orchestrator.py, tests/test_webhooks.py, tests/test_messages.py,
  tests/test_auth.py, tests/test_user_isolation.py (edited).
- 🔁 Next prompts: confirm to continue with Phase 5 (US3) — T018..T022
  response-model routing rendering + Dashboard/attention + tasks slice.
- 🧠 Reflection: passing `routing=` into `analyze_message` (internal gating)
  made T013's explicit `_gate_outputs(result)` step redundant — the record
  attaches after the (already gated) call, preserving the single-call
  invariant. Motor must never be awaited from a throwaway `asyncio.run` loop;
  keeping motor-bound tests on the TestClient loop (or behind a fake
  collection) made the suite order-independent.

## Evaluation notes (flywheel)

- Failure modes observed: (1) the described motor/asyncio.run conflict — two
  distinct RuntimeErrors that flipped depending on which module ran first
  (order-dependence); fixed by removing motor awaits from `asyncio.run` worlds.
  An initial persistent-loop conftest pin was tried and reverted (it caused
  "Future attached to a different loop"). (2) full-suite needs ~105–120 s —
  run pytest with a 300s shell budget.
- Graders run and results (PASS/FAIL): PASS — tests-first verified red
  (ImportError on missing `process_message`/orchestrate module), then green;
  no bypass paths remain; one routing-decision log per message; full suite green.
- Prompt variant (if applicable): three parallel red tests, one per entry
  surface (orchestrator unit / webhook / REST).
- Next experiment (smallest change to try): N/A