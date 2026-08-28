---
id: phr-constitution-day24-ai-orchestrator
title: "Day 24 AI Orchestrator Constitution"
stage: constitution
date: 2026-08-29
surface: cli
model: big-pickle
feature: ai-orchestrator
branch: main
user: user
command: /sp.constitution
labels: [constitution, ai, orchestrator, day-24]
links:
  spec: N/A
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - .specify/memory/constitution.md
tests:
  - N/A (constitution amendment; no code changes)
---

## Prompt

Create a focused constitution for Day 24 – AI Orchestrator.

### Context
- Project: Communication AI (FYP)
- We already have individual AI capabilities: Priority, Summary, Task Extraction, Deadline, Recommended Action
- Now we want to introduce a proper AI Orchestrator to make the system more agentic

### Goal of Day 24:
Create an AI Orchestrator whose job is to decide which agents need to run for a new message.

Flow:
New Message
     ↓
Orchestrator
     ↓
What do we need to know?
     ↓
Priority Agent / Task Agent / Summary Agent / etc.

### Principles:
- Keep it simple (do not build a very complex multi-agent system)
- Orchestrator should intelligently decide what is needed
- Still follow "AI is Assistive, not Magical"
- One clear orchestration layer is better than messy scattered AI calls

### Please create a short constitution that covers:
1. Purpose of the AI Orchestrator
2. Core principles for orchestration
3. What the Orchestrator should decide
4. What it should NOT do
5. Quality bar for this feature

Keep it practical and suitable for a university FYP.

## Response snapshot

Updated `.specify/memory/constitution.md` from v1.11.0 to v1.12.0 (MINOR bump).

Changes made:
1. Added "Day 24 AI Orchestrator" section after Day 23 Real WhatsApp Webhook,
   containing: Purpose of the AI Orchestrator (flow diagram), Core
   Orchestration Principles (7 rules incl. one orchestration layer, minimal
   analysis, priority never optional, rule-based-first, no multi-agent
   framework), What the Orchestrator MUST Decide (5 decisions incl. whether
   to analyze at all, which agents run, execution order, fallbacks, whether
   the LLM call is needed), What the Orchestrator MUST NOT Do (7 absolute
   prohibitions), Quality Bar for the AI Orchestrator (7 verification
   criteria).
2. Amended "Complete AI Pipeline" rules to defer agent selection to the
   Orchestrator: principle #1 "One message in, one directed analysis out",
   principle #2 fixed order among selected agents, pipeline diagram, and a
   Day 24 amendment note.
3. Updated "Complete Pipeline Targets" (message → Orchestrator → selected
   agents) and the matching compliance checklist item.
4. Added 5 new Compliance Checklist items for orchestration requirements.
5. Updated Sync Impact Report at top of file.
6. Updated version footer to 1.12.0 with date 2026-08-29.

## Outcome

- ✅ Impact: Constitution updated with a focused Day 24 AI Orchestrator
  section; Complete AI Pipeline reconciled so agent selection now routes
  through the Orchestrator; compliance checklist expanded with orchestration
  checks.
- 🧪 Tests: N/A — constitution amendment only; no code tests run.
- 📁 Files: .specify/memory/constitution.md (single file modified)
- 🔁 Next prompts: /sp.spec (or /sp.plan) for the Day 24 AI Orchestrator
  feature specification
- 🧠 Reflection: The existing Complete AI Pipeline "always run all five
  agents" default conflicted with the new routing concept, so two existing
  principles were amended rather than silently contradicted. The MINOR bump
  is appropriate: a materially new section plus refinements to existing
  pipeline guidance. The proposal keeps orchestration rule-based-first to
  respect the constitution's existing single-LLM-round-trip constraint.

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): PASS — all bracket tokens resolved,
  version matches report, dates ISO format, principles declarative and
  testable
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A