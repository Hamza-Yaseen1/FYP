---
id: phr-015-ai-orchestrator-green-003
title: AI Orchestrator US3 Implementation
stage: green
date: 2026-08-29
surface: cli
model: big-pickle
feature: ai-orchestrator
branch: 015-ai-orchestrator
user: user
command: /sp.tasks (implementation)
labels: [green, day24, ai-orchestrator, us3, dashboard, additive-contract]
links:
  spec: specs/015-ai-orchestrator/spec.md
  tasks: specs/015-ai-orchestrator/tasks.md
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - backend/tests/test_messages.py
  - backend/tests/test_webhooks.py
tests:
  - pytest tests/test_messages.py tests/test_webhooks.py (46 passed)
  - pytest tests/ (120 passed)
---

## Prompt

Continue with Phase 5 – User Story 3 (final result unchanged for the Dashboard).
Follow tasks.md T018–T020: prove the stored/returned `ai_analysis` keeps every
legacy field plus the additive `routing`; prove a simulate ingestion persists it;
verify the Dashboard contract (zero frontend/behavior drift, render-time reads
only stored `ai_analysis`).

## Response snapshot

Implemented the US3 slice (T018–T020), mostly verification because US2 already
delivers the routing record end-to-end:

- T018: `TestUS3RoutingContract` in `backend/tests/test_messages.py` — POSTs a
  rich message through the REAL orchestrator with a fake provider patched on
  `services.ai.analyzer.get_provider`, then asserts the 201 response `ai_analysis`
  keeps all 13 legacy fields and adds `routing` (`agents_run` = all five agents,
  `agents_skipped` = [], `skip_reason="full"`, `triggers`, `llm_call_used=true`,
  `decided_at`).
- T019: `test_simulate_background_persists_ai_analysis_with_routing` in
  `backend/tests/test_webhooks.py` — same fake-provider approach through
  `/webhooks/simulate`; the background task's real `process_message` persists
  `ai_analysis` (legacy fields + `routing`) on the stored document.
- T020 (no code change): `git status --short -- components app lib` → clean;
  grep over `components/`, `app/`, `lib/` → zero references to
  `process_message`/`orchestr`/`analyze_message`/`routing`; the Dashboard reads
  only stored `ai_analysis`. GET endpoints never call the Orchestrator.

Both new tests were green immediately (feature already delivered by US2); they
now lock the contract. Full suite → 120 passed (118 + 2 new), only pre-existing
`utcnow` DeprecationWarnings. `tasks.md` T018–T020 marked `[x]`. Stopped per the
one-slice-at-a-time instruction — US4 (trivial/no-content short-circuit) is next.

## Outcome

- ✅ Impact: The additive `ai_analysis.routing` contract is now guarded on both
  the REST response surface and the stored webhook document; the Dashboard has
  zero changes and no render-time orchestrator reads.
- 🧪 Tests: 2 new tests; full suite 120 passed / 0 failed.
- 📁 Files: backend/tests/test_messages.py (new class), backend/tests/test_webhooks.py
  (new test). No production code changed.
- 🔁 Next prompts: confirm to continue with Phase 6 (US4) — T021..T027
  trivial/no-content short-circuit (`_deterministic_defaults`, skipped stubs).
- 🧠 Reflection: US2's exhaustive field work paid off — US3 needed only
  contract-guard tests and a verification pass. Fake-provider integration tests
  (real orchestrator, real persistence) give stronger coverage than spy tests
  while staying LLM-free.

## Evaluation notes (flywheel)

- Failure modes observed: none — tests passed on first run (expected: the
  behavior was already implemented in the US2 slice; the red-first convention
  is explicitly superseded by the contract-guard intent here).
- Graders run and results (PASS/FAIL): PASS — full legacy field set + routing on
  both response and stored doc; `git status` and grep confirm no frontend drift;
  independent test command green.
- Prompt variant (if applicable): contract-guard tests written after the
  feature existed (verification slice).
- Next experiment (smallest change to try): N/A