---
id: phr-plan-day25-agent-memory
title: "Day 25 Agent Memory Implementation Plan"
stage: plan
date: 2026-08-29
surface: cli
model: big-pickle
feature: 016-agent-memory
branch: 016-agent-memory
user: user
command: /sp.plan
labels: [plan, memory, context, ai, day-25]
links:
  spec: specs/016-agent-memory/spec.md
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - specs/016-agent-memory/plan.md
  - specs/016-agent-memory/research.md
  - specs/016-agent-memory/data-model.md
  - specs/016-agent-memory/contracts/thread-identity-contract.md
  - specs/016-agent-memory/contracts/ai-context-prompt-contract.md
  - specs/016-agent-memory/quickstart.md
  - AGENTS.md (agent context refreshed via update-agent-context.ps1)
tests:
  - N/A (planning phase; no code changes)
---

## Prompt

Write a practical technical implementation plan for Day 25 — Agent Memory /
Context. Keep it simple for a university FYP. Include:

1. Goal of this phase
2. Technical approach (keep it simple)
3. How conversationId / threadId will be assigned
4. How context will be passed to AI
5. Files to create / update
6. Implementation steps in order
7. Testing plan
8. Definition of Done

## Response snapshot

1. Wrote `specs/016-agent-memory/plan.md` mirroring the Day 24 plan structure:
   Summary + phase goal, Technical Context (Python 3.13, no new deps, MongoDB
   additive fields + 2 indexes, pytest/TestClient, local dev, ≤10s budget),
   Constitution Check GATE table (all 13 rows PASS), Project Structure
   (2 NEW backend modules: `services/threads.py`, `services/ai/context.py`;
   updates to webhook_ingest/routes.messages/models.message/main.py/
   analyzer/orchestrate/providers; 2 NEW test files; frontend untouched),
   Technical Approach (4 subsections: id assignment via anchor rule,
   context injection inside the existing single call, validated outward
   enrichment, decision table), 10 ordered Implementation Steps with
   checkpoints, Testing Plan (30-pair labeled set ⇒ SC-002/3, single-call
   count ⇒ SC-006, isolation ⇒ SC-007, regression), Definition of Done mapped
   to FR/SC, Complexity Tracking (none).
2. Phase 0 `research.md`: decisions — link resolved at ingest (one indexed
   query), `threadId` = anchor message `_id`, `conversationId` = `threadId`,
   indexed via existing `received_at`, context block only when present
   (byte-compat when None), validation drops unproven `context_updates`,
   failure handling never blocks ingestion; 30-pair labeled set; no
   NEEDS CLARIFICATION.
3. Phase 1: `data-model.md`, `contracts/thread-identity-contract.md`,
   `contracts/ai-context-prompt-contract.md`, `quickstart.md`; refreshed
   agent context: `update-agent-context.ps1 -AgentType opencode` (AGENTS.md
   +2 lines, nextjs-agent-rules block intact).

## Outcome

- ✅ Impact: Complete Day 25 implementation plan on branch `016-agent-memory`
  with grounded file paths, ordered steps, and a test plan that directly
  measures the constitution's quality bar (≤5% false links, ≥80% recall on a
  30-pair labeled set; zero extra LLM round-trips; isolation; zero regression).
- 🧪 Tests: N/A — planning phase; no code tests run.
- 📁 Files: specs/016-agent-memory/{plan,research,data-model,quickstart}.md,
  specs/016-agent-memory/contracts/{thread-identity,ai-context-prompt}-contract.md,
  AGENTS.md
- 🔁 Next prompts: /sp.tasks to generate tasks.md, then implementation
- 🧠 Reflection: The plan reuses the Day 24 plan/research/data-model/contracts/
  quickstart shape for convention consistency. Capricious bit: `update-agent-
  context.ps1` truncates the multi-line `Primary Dependencies` value to its
  first line ("(stdlib) for") — cosmetic, matching how 015's entry reads; the
  `CONTEXT` block only exists on the analyze path and only with context, so
  the single-call and byte-compat guarantees are testable by counting provider
  invocations and diffing the prompt when `context=None`.

## Evaluation notes (flywheel)

- Failure modes observed: N/A (script ran; note the multi-line plan field
  truncation as a cosmetic parser limitation of update-agent-context.ps1).
- Graders run and results (PASS/FAIL): PASS — Technical Context has no
  NEEDS CLARIFICATION, Constitution Check gate re-checked against v1.13.0
  Day 25 section, all 8 requested sections present in plan.md, steps ordered
  with checkpoints, DoD maps to spec FR/SC.
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): /sp.tasks on Day 25