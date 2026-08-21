---
id: phr-20260821-complete-pipeline
title: Day 14 Complete AI Pipeline
stage: constitution
date: 2026-08-21
surface: cli
model: big-pickle
feature: N/A
branch: N/A
user: user
command: /sp.constitution
labels: [constitution, ai-pipeline, dashboard, day-14]
links:
  spec: N/A
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - .specify/memory/constitution.md
tests: []
---

## Prompt

Create a focused constitution for Day 14 – Complete AI Pipeline.

### Context
- Project: Communication AI
- Individual agents are already built: Priority, Summary, Task Extraction, Deadline Detection, Recommended Action
- Now we want the complete pipeline to work smoothly together

### Goal of Day 14:
When a message arrives, the full AI pipeline should run:

Message
  ↓
Priority Agent
  ↓
Summary
  ↓
Task Extraction
  ↓
Deadline Detection
  ↓
Recommended Action
  ↓
MongoDB
  ↓
Dashboard

The Dashboard should clearly show:

🔴 NEEDS ATTENTION
Send FYP slides
WhatsApp • Ali
Deadline: Tonight
Why it matters: A task with a near deadline was detected.
Recommended: Send the slides before tonight.

### Please create a short constitution that covers:
1. Purpose of the Complete AI Pipeline
2. Core principles for the full flow
3. What “Needs Attention” means
4. How the final result should look on the Dashboard
5. Quality bar for the complete pipeline

Keep it practical and aligned with Simplicity First.

## Response snapshot

Updated constitution to v1.3.0 with new "Complete AI Pipeline" section covering: purpose (full flow diagram Message → five agents → MongoDB → Dashboard), six core principles for the full flow (one analysis per message, fixed stage order, single LLM call, persist once/read many, per-stage graceful degradation, idempotent processing), a derived-not-invented definition of NEEDS ATTENTION with signal table and mandatory "Why it matters" explanation, exact dashboard card format with field mapping rules, and a pipeline quality bar (≤10s latency, zero duplicates, flag honesty, UI reads stored data only). Added Complete Pipeline Targets to Quality Bar and 4 new compliance checks. All templates verified compatible.

## Outcome

- ✅ Impact: Constitution updated with end-to-end pipeline governance for Day 14
- 🧪 Tests: N/A (constitution update)
- 📁 Files: .specify/memory/constitution.md
- 🔁 Next prompts: /sp.plan or /sp.spec for the pipeline integration feature
- 🧠 Reflection: MINOR bump correct — new section added, no existing principles redefined; Needs Attention criteria kept deliberately narrow to avoid false positives

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
