---
id: phr-015-ai-orchestrator-green-005
title: AI Orchestrator US5 Implementation
stage: green
date: 2026-08-29
surface: cli
model: big-pickle
feature: ai-orchestrator
branch: 015-ai-orchestrator
user: user
command: /sp.tasks (implementation)
labels: [green, day24, ai-orchestrator, us5, explainability, failure-vs-skip]
links:
  spec: specs/015-ai-orchestrator/spec.md
  tasks: specs/015-ai-orchestrator/tasks.md
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - backend/services/ai/orchestrate.py
  - backend/tests/test_orchestrator.py
tests:
  - pytest tests/test_orchestrator.py -k routing_record (passed)
  - pytest tests/ (125 passed)
---

## Prompt

Continue with Phase 7 – User Story 5 (routing decisions are explainable).
Follow tasks.md T024–T026: every processed message carries an inspectable
record (agents run/skipped, reason, AI-call flag) and failed agents are
distinguishable from deliberately skipped ones.

## Response snapshot

Implemented the US5 slice (T024–T026):

- T024: `test_routing_record_complete` — analyzed message: `agents_run ∪
  agents_skipped == {all five}`, `priority ∈ agents_run`, `skip_reason` /
  `triggers` populated; plus `routing` present with all six keys on every
  path (full / trivial / skipped). Wiring analysis calls through the
  recording-collection fake so no motor runs under `asyncio.run`.
- T025: `test_failure_distinct_from_skip` — a provider whose `analyze` raises
  → `status="pending"`, `routing.llm_call_used=true`, `skip_reason` intact;
  compared against trivial (`"completed"`, `llm_call_used=false`) so the two
  are provably distinguishable. (This path was already green: `analyze_message`
  catches provider-analyze failures internally and `process_message` attached
  the record afterwards.)
- T025+red: added `test_get_provider_failure_still_attaches_routing` — the
  actual red case. `analyze_message` calls `get_provider()` BEFORE its
  try-block, so a provider-*construction* failure raised straight through and
  the routing record was never attached (the message endpoint would 500).
- T026: `process_message` now awaits through a small `_analyze_with_fallback`
  wrapper whose try/except returns the same `status="pending"` fallback when
  `analyze_message` raises, so routing is attached on absolutely every analyzed
  path (`llm_call_used=true`), including provider-construction crashes.

Result: `test_orchestrator.py` → 32 passed; full suite → 125 passed (122 + 3
new), only pre-existing `utcnow` DeprecationWarnings. `tasks.md` T024–T026
marked `[x]`. Remaining: Phase 8 (Polish) — full-suite regression, standalone
script validation, manual quickstart pass, constitution compliance.

## Outcome

- ✅ Impact: Explaining a decision is now unconditional — every analyzed,
  trivial, skipped, and failed message returns a complete routing record, and
  failure (`pending` + `llm_call_used=true`) is unambiguous versus a deliberate
  skip. A provider-construction crash no longer surfaces above the orchestrator.
- 🧪 Tests: 3 new tests (record completeness, failure-vs-skip, provider-construction
  failure); full suite 125 passed / 0 failed.
- 📁 Files: backend/tests/test_orchestrator.py (+3), backend/services/ai/orchestrate.py
  (added `_analyze_with_fallback`).
- 🔁 Next prompts: confirm to continue with Phase 8 (Polish) — T027..T030:
  full-suite regression, standalone scripts against the live backend,
  quickstart manual validation, constitution compliance re-check.
- 🧠 Reflection: the genuinely red boundary was not the provider call but the
  provider factory (`get_provider` sits outside `analyze_message`'s try). Tests
  that only force `analyze` to raise would have "passed" without the fix —
  driving the test through `get_provider` was the difference.

## Evaluation notes (flywheel)

- Failure modes observed: provider-construction raise propagated (no routing
  record, endpoint would 500) — fixed by the wrapper. Expected red first.
- Graders run and results (PASS/FAIL): PASS — record completeness holds on all
  three shapes; failure-vs-skip distinguishable by status + llm_call_used;
  full suite green; `-k routing_record` independent test green.
- Prompt variant (if applicable): separate red test added for the factory-failure
  seam the task's prose didn't explicitly name.
- Next experiment (smallest change to try): N/A