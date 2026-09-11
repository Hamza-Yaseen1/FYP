---
id: phr-spec-day25-agent-memory
title: "Day 25 Agent Memory Spec"
stage: spec
date: 2026-08-29
surface: cli
model: big-pickle
feature: 016-agent-memory
branch: 016-agent-memory
user: user
command: /sp.spec
labels: [spec, memory, context, ai, day-25]
links:
  spec: specs/016-agent-memory/spec.md
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - specs/016-agent-memory/spec.md
  - specs/016-agent-memory/checklists/requirements.md
tests:
  - N/A (specification phase; no code changes)
---

## Prompt

Create a clear and focused specification for Day 25 – Agent Memory / Context.

### Context
- Project: Communication AI
- AI Orchestrator and agents are already working
- Currently each message is analyzed in isolation
- Now we want the system to understand related messages

### Goal:
Messages should not always be analyzed alone.

Example:
Message 1: "Can you send the report?"
Message 2: "Need it before our meeting tomorrow."

The system should associate them when appropriate.

### Store these fields:
- conversationId
- threadId
- messageId

### Requirements:
- Link related messages in a simple way
- Use conversation/thread context when analyzing new messages
- Keep the solution simple (do not build a complex memory system)
- Existing AI pipeline and Dashboard should still work
- Only current user's messages should be considered

### Please include in the specification:
1. Feature Overview
2. Purpose of memory/context
3. How messages will be linked
4. Data fields to store
5. How context will be used during AI analysis
6. Acceptance Criteria
7. Edge cases

Keep it practical and clean for a university FYP.

## Response snapshot

Created feature branch `016-agent-memory` and wrote the Day 25 spec.

1. Branch/dir setup: ran `create-new-feature.ps1 -Number 16 -ShortName
   "agent-memory"` — highest existing feature number found: 015 (ai-orchestrator).
   Script hit a PowerShell 5.1 incompatibility (`Join-Path` with 3 positional
   args) after creating the branch/spec; completed the missing
   `history/prompts/016-agent-memory/` dir manually.
2. Wrote `specs/016-agent-memory/spec.md` mirroring the Day 24 spec structure:
   Feature Overview, Purpose of Memory/Context, How Messages Are Linked
   (deterministic rule: same user + channel + sender + ≤ 60 min window), Data
   Fields to Store (`messageId`/`threadId`/`conversationId`, server-set only),
   How Context Will Be Used During AI Analysis (≤ 5 recent thread messages
   inside the existing single AI call; user-stated facts win; effect recorded
   with explanation), 5 prioritized User Stories with acceptance scenarios,
   Edge Cases (14), Functional Requirements FR-001..FR-015, Key Entities,
   Measurable Success Criteria SC-001..SC-008, Assumptions, Out of Scope.
3. Ran the specification quality validation: no [NEEDS CLARIFICATION] markers
   (link window, context cap, and `conversationId` default all inherited from
   the Day 25 constitution v1.13.0); all 12 checklist items pass. Wrote
   `specs/016-agent-memory/checklists/requirements.md` with all items marked
   complete.

## Outcome

- ✅ Impact: Feature branch `016-agent-memory` with a complete, practical spec
  for Day 25 agent memory/context. Linking is deterministic (never guessed),
  context stays inside the existing single AI call, and the Dashboard/pipeline
  contract is preserved by design.
- 🧪 Tests: N/A — specification phase; no code tests run.
- 📁 Files: specs/016-agent-memory/spec.md, specs/016-agent-memory/checklists/requirements.md
- 🔁 Next prompts: /sp.clarify (not needed — no markers) or /sp.plan for the
  Day 25 agent memory feature
- 🧠 Reflection: The spec reuses the Day 24 (orchestrator) spec as a structural
  model, which keeps the repo's spec style consistent. The Microsoft-constitution
  amendment from the prior `/sp.constitution` prompt was the source of truth for
  the technical defaults (link rule, context cap, isolation), so no
  clarifications were required. Noted a tooling defect: the PowerShell feature
  script fails mid-way on PowerShell 5.1 due to `Join-Path` argument binding.

## Evaluation notes (flywheel)

- Failure modes observed: create-new-feature.ps1 fails with "positional
  parameter cannot accept argument 'prompts'" on Windows PowerShell 5.1
  (Join-Path accepts only 2 positional params there; script targets pwsh 7).
- Graders run and results (PASS/FAIL): PASS — no placeholder tokens, mandatory
  template sections preserved, FRs/SCs testable and technology-agnostic, edge
  cases covered, checklist complete
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A