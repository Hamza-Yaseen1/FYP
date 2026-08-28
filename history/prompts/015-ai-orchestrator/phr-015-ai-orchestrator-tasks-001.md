---
id: phr-015-ai-orchestrator-tasks-001
title: AI Orchestrator Task List
stage: tasks
date: 2026-08-29
surface: cli
model: big-pickle
feature: ai-orchestrator
branch: 015-ai-orchestrator
user: user
command: /sp.tasks
labels: [tasks, day24, ai-orchestrator, user-stories, task-list]
links:
  spec: specs/015-ai-orchestrator/spec.md
  tasks: specs/015-ai-orchestrator/tasks.md
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - specs/015-ai-orchestrator/tasks.md
tests:
  - N/A (planning stage)
---

## Prompt

Create a clear and actionable task list for Day 24 – AI Orchestrator.

### Context
- Project: Communication AI
- Individual AI features already work (Priority, Summary, Task Extraction, Deadline, Recommended Action)
- Now we need a central AI Orchestrator

### Goal:
When a new message arrives:
New Message → AI Orchestrator → Decides which agents to run → Combined result → MongoDB → Dashboard

### Focus Areas:
- Create an AI Orchestrator service
- Decide which agents should run for a message
- Call existing agents in a clean way
- Combine their results into one final analysis
- Keep the system simple (not a complex multi-agent framework)
- Make sure Dashboard still works with the final result

### Requirements for the task list:
- Break work into small, clear, executable tasks
- Group tasks logically (Orchestrator, Integration, Testing)
- Write tasks in action language
- Include acceptance criteria
- Follow Simplicity First principle

Save the file in the appropriate location.

## Response snapshot

Created `specs/015-ai-orchestrator/tasks.md` on branch `015-ai-orchestrator`
with 30 tasks grouped into 8 phases:

- Phase 1 Setup (T001–T002): branch + Groq env verification — Day 24 adds NO
  new env vars or dependencies (routing is stdlib `re`/`unicodedata` only).
- Phase 2 Foundational (T003): declare `RoutingRecord` + `AIAnalysis.routing`
  in `backend/models/message.py` — the Pydantic-2 `extra='ignore'` drop was the
  key discovery the whole record surface hinges on.
- Phase 3 US1 (P1, MVP, T004–T009): decision-table + 50-labeled-message
  accuracy (SC-002) + gating tests written first; `routing.py` signal module,
  `analyze_message(run_tasks=True)` persistence gate, `_gate_outputs` +
  attention after gating.
- Phase 4 US2 (P1, T010–T017): single-call/call-count + entry-point spy tests;
  `orchestrate.process_message`, redirects in `webhook_ingest.py` and
  `routes/messages.py`, `__init__` export, grep-verified no bypass.
- Phase 5 US3 (P1, T018–T020): response/storage shape preserved + additive
  `routing`; Dashboard contract verified with zero frontend changes.
- Phase 6 US4 (P2, T021–T023): trivial → 0 AI calls, deterministic
  `status:"completed"` defaults; no-content/media → `skipped` stub with reason.
- Phase 7 US5 (P2, T024–T026): routing-record completeness + failure-vs-skip
  (`pending` + `llm_call_used=True` ≠ deliberate skip).
- Phase 8 Polish (T027–T030): full pytest suite, standalone scripts, quickstart
  manual pass, constitution Day 24 re-check.

Format compliance: every task uses `- [ ] TNNN [P?] [US?] action with file
path`; phases carry goals, independent tests, checkpoints; dependencies,
parallel examples, and MVP (= US1) strategy are documented.

## Outcome

- ✅ Impact: A directly executable task list organized by the spec's 5 user
  stories (P1: US1–US3 routing correctness, orchestration layer, dashboard
  stability; P2: US4 trivial cost, US5 explainability). Tests are written
  first and must fail before implementation. Story ordering keeps
  `orchestrate.py` single-author (US2→US4→US5 sequential).
- 🧪 Tests: N/A (planning stage) — but test tasks are included per the spec's
  mandatory "User Scenarios & Testing" and the plan's pytest matrix.
- 📁 Files: specs/015-ai-orchestrator/tasks.md
- 🔁 Next prompts: /sp.red or /sp.green for user story implementation,
  starting with Phase 1–3
- 🧠 Reflection: The cleanest framing was "US1 decides, US4 exploits, US2
  funnels, US5 explains" — keeping each story's surface small and its
  independent test runnable with a single pytest `-k` selector. The labeled
  50-message accuracy test makes SC-002 measurable without a live LLM.

## Evaluation notes (flywheel)

- Failure modes observed: none blocking. `create-phr.sh` was absent from
  `.specify/scripts/` (no bash scripts dir), so the PHR was authored directly
  from `.specify/templates/phr-template.prompt.md`. Two wording slips in
  tasks.md (an invalid `git status --frontend` flag and a stray "(knowledge:"
  fragment) were corrected before completion.
- Graders run and results (PASS/FAIL): PASS — all 30 tasks follow the strict
  checklist format (checkbox, ID, labels, file paths), stories carry priority
  labels and independent test criteria, phases include checkpoints, no sample
  tasks remain, acceptance criteria present.
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A