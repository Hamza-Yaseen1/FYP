---
id: phr-tasks-day25-agent-memory
title: "Day 25 Agent Memory Task List"
stage: tasks
date: 2026-08-29
surface: cli
model: big-pickle
feature: 016-agent-memory
branch: 016-agent-memory
user: user
command: /sp.tasks
labels: [tasks, memory, context, ai, day-25]
links:
  spec: specs/016-agent-memory/spec.md
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - specs/016-agent-memory/tasks.md
tests:
  - N/A (task-generation phase; no code changes)
---

## Prompt

Create a clear and actionable task list for Day 25 – Agent Memory / Context.

### Context
- Project: Communication AI
- AI Orchestrator and agents are already working
- Currently each message is analyzed alone
- Now we need simple context awareness

### Goal:
Related messages should be linked when appropriate.

Example:
Message 1: "Can you send the report?"
Message 2: "Need it before our meeting tomorrow."

Store:
- conversationId
- threadId
- messageId

### Focus Areas:
- Add conversationId / threadId / messageId support
- Link related messages in a simple way
- Pass recent context to the AI when analyzing a new message
- Keep the solution simple (no complex memory system)
- Ensure existing AI pipeline and Dashboard still work

### Requirements for the task list:
- Break work into small, clear, executable tasks
- Group tasks logically (Database, Backend, AI Context, Testing)
- Write tasks in action language
- Include acceptance criteria
- Follow Simplicity First principle

Save the file in the appropriate location.

## Response snapshot

Generated `specs/016-agent-memory/tasks.md` (32 tasks, strict
`- [ ] T### [P?] [US#?] description + exact file path` format, all entries
validated programmatically).

1. Prerequisites: `check-prerequisites.ps1 -Json` returned FEATURE_DIR
   `specs\016-agent-memory` with docs available (research, data-model,
   contracts, quickstart); checklists `requirements.md` = 16/16 complete → PASS
   (no stop-for-confirmation needed). Docs loaded: plan, spec (5 user
   stories), data-model, both contracts, research, quickstart.
2. Structure (mirrors Day 24 tasks.md): Contract → User Story mapping + a
   Focus-area → Task mapping (Database / Backend / AI Context / Testing per
   the user request); Phase 1 Setup (2), Phase 2 Foundational (4:
   `ContextUpdate` + `MessageResponse` identity fields T003, two per-user
   indexes T004, `backend/services/threads.py` link module T005, no-memory-
   framework grep T006); Phase 3 US1-P1 MVP (9: link-rule tests, labeled
   30-pair test, context fetch/injection test, single-call + enrich test +
   context.py, provider CONTEXT block, analyzer, orchestrator wiring, ingest
   identity wiring); Phase 4 US2 (3), Phase 5 US3 (4), Phase 6 US4-P2 (4),
   Phase 7 US5 (3); Phase 8 Polish (3). Acceptance Criteria block per phase.
3. Dependencies: US2/US3/US4/US5 each "after US1" (they assert/verify the
   wiring US1 lands); parallel opportunities mapped per phase; MVP = US1.
   Coordination notes flag shared files (`context.py`, `test_context_ai.py`,
   `orchestrate.py`).

## Outcome

- ✅ Impact: 32 immediately-executable tasks on branch `016-agent-memory` with
  TDD ordering (per-story tests first), clear file paths, per-phase acceptance
  criteria, and a dependency graph — ready for implementation.
- 🧪 Tests: N/A — task-generation phase; no code tests run.
- 📁 Files: specs/016-agent-memory/tasks.md
- 🔁 Next prompts: /sp.api or implementation execution of the tasks (Phase 1 →
  Foundational → US1 MVP → US2..US5 → Polish)
- 🧠 Reflection: Reused the Day 24 tasks.md as the repo's format precedent
  (checkbox/ID/[P]/[Story]/file-path strictness, per-story test-first sections,
  acceptance criteria blocks, parallel examples, implementation strategy).
  Story organization is kept faithful to the spec's five priorities, with US1
  as the MVP slice and US2/US3/US5 as verification-style stories (mirroring
  Day 24's US3 verification story).

## Evaluation notes (flywheel)

- Failure modes observed: two authoring typos ("deadline/urg urgency",
  "(ass wording") caught and corrected via targeted edits before validation.
- Graders run and results (PASS/FAIL): PASS — 32/32 task lines match
  `- [ ] T\d{3}( \[P\])?( \[US\d\])? ... file path` (scripted check); format
  validation confirms all tasks carry IDs, story labels (story phases), and
  exact paths; 0 lines without a file path.
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A