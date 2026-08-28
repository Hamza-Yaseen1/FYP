---
id: phr-015-ai-orchestrator-spec-001
title: Day 24 AI Orchestrator Spec
stage: spec
date: 2026-08-29
surface: cli
model: big-pickle
feature: ai-orchestrator
branch: 015-ai-orchestrator
user: user
command: /sp.specify
labels: [spec, day24, ai-orchestrator, routing, agents]
links:
  spec: specs/015-ai-orchestrator/spec.md
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - specs/015-ai-orchestrator/spec.md
  - specs/015-ai-orchestrator/checklists/requirements.md
tests:
  - N/A
---

## Prompt

Create a clear and focused specification for Day 24 – AI Orchestrator.

### Context
- Project: Communication AI
- We already have individual AI features: Priority, Summary, Task Extraction, Deadline Detection, Recommended Action
- Now we want to introduce an AI Orchestrator to make the system more agentic

### Goal:
When a new message arrives, the Orchestrator should decide which agents need to run.

Flow:
New Message
     ↓
AI Orchestrator
     ↓
Decides what is needed
     ↓
Priority Agent / Summary Agent / Task Agent / etc.
     ↓
Final combined result saved in MongoDB

### Requirements:
- Create a central Orchestrator
- It should intelligently decide which analyses are needed
- Keep it simple (not a very complex multi-agent framework)
- Final output should still contain: priority, summary, tasks, deadline, recommended action
- Existing Dashboard should continue to work

### Please include in the specification:
1. Feature Overview
2. Purpose of the Orchestrator
3. Decision logic (what it should decide)
4. Input / Output
5. How it works with existing agents
6. Acceptance Criteria
7. Edge cases

Keep it practical and clean for a university FYP.

## Response snapshot

Created spec on branch `015-ai-orchestrator` with:
- specs/015-ai-orchestrator/spec.md — Feature Overview (goal + out of scope),
  Purpose of the Orchestrator (3 reasons + flow), Decision Logic (rule-based
  first: whether to analyze, which agents run, whether an AI call is needed,
  execution order, unambiguous routing fallback), Input/Output (field table +
  routing record), How It Works with Existing Agents (integration flow + no
  bypass + dashboard unchanged), 5 prioritized User Stories with acceptance
  scenarios, 13 Edge Cases, 15 Functional Requirements, Key Entities, 8
  measurable Success Criteria, Assumptions, Out of Scope.
- specs/015-ai-orchestrator/checklists/requirements.md — Quality checklist
  with all items PASS on first pass.
- No [NEEDS CLARIFICATION] markers required — the Day 24 constitution section
  supplied documented defaults for every decision.
- Branch + spec created by create-new-feature.ps1; the PowerShell 5.1
  Join-Path failure on the multi-child history path (same as Day 23) was
  worked around by creating history/prompts/015-ai-orchestrator/ manually.

## Outcome

- ✅ Impact: Full Day 24 spec written; the anchoring idea is "one rule-based
  decision layer, not a framework" — minimal agent subset per message,
  priority always runs, single combined AI call preserved, explainable routing
  record, and the Dashboard contract held constant.
- 🧪 Tests: N/A (specification stage)
- 📁 Files: specs/015-ai-orchestrator/spec.md,
  specs/015-ai-orchestrator/checklists/requirements.md
- 🔁 Next prompts: /sp.plan for ai-orchestrator
- 🧠 Reflection: The spec reconciles the constitution's existing constraints
  (single AI call, Priority always, fixed order, Day 23 normalization) with
  the new routing capability by making the Orchestrator rule-based and adding
  a "fail toward completeness" default. The 5 user stories map 1:1 to the
  constitution's orchestration principles and quality bar.

## Evaluation notes (flywheel)

- Failure modes observed: Create-new-feature.ps1 failed on PowerShell 5.1
  `Join-Path` with 3+ child paths after branch + spec creation; worked around
  manually (prompts dir).
- Graders run and results (PASS/FAIL): PASS — no placeholders, no
  implementation details, no [NEEDS CLARIFICATION] markers, all mandatory
  sections present, checklist fully marked
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A