---
id: phr-20260821-spec-pipeline
title: Day 14 Complete Pipeline Spec
stage: spec
date: 2026-08-21
surface: cli
model: big-pickle
feature: 006-complete-ai-pipeline
branch: 006-complete-ai-pipeline
user: user
command: /sp.specify
labels: [spec, ai-pipeline, dashboard, day-14]
links:
  spec: specs/006-complete-ai-pipeline/spec.md
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - specs/006-complete-ai-pipeline/spec.md
  - specs/006-complete-ai-pipeline/checklists/requirements.md
tests: []
---

## Prompt

Create a clear and focused specification for Day 14 – Complete AI Pipeline.

### Context
- Project: Communication AI
- Individual parts are already working: Priority, Summary, Task Extraction, Deadline Detection, Recommended Action
- Now we want the full pipeline to work smoothly and display clearly on the Dashboard

### Goal:
When a message arrives, the complete AI flow should run and the Dashboard should show a clear “Needs Attention” card.

Example of final result on Dashboard:

🔴 NEEDS ATTENTION
Send FYP slides
WhatsApp • Ali
Deadline: Tonight
Why it matters: A task with a near deadline was detected.
Recommended: Send the slides before tonight.

### Please include in the specification:
1. Feature Overview
2. Complete Pipeline Flow (step-by-step)
3. Final Output Structure (what should be stored in MongoDB)
4. How the “Needs Attention” card should look
5. User Stories
6. Acceptance Criteria
7. Rules for showing something in “Needs Attention”
8. Edge cases

Keep it simple and practical for a university FYP.

## Response snapshot

Created branch 006-complete-ai-pipeline and wrote spec with all 8 requested sections mapped onto the standard template: Feature Overview, 3 prioritized user stories (full analysis on arrival P1, Needs Attention flagging P2, graceful degradation P3) with Given/When/Then acceptance scenarios, 13 functional requirements including flag rules R1/R2 mirroring constitution v1.3.0, step-by-step pipeline flow, exact Needs Attention card layout with field-source table, Message Analysis Record entity for storage structure, 7 edge cases, 6 measurable success criteria, assumptions, and out-of-scope. Quality checklist passed first iteration with zero NEEDS CLARIFICATION markers. Note: create-new-feature.ps1 partially failed on PowerShell 5.1 (Join-Path with 4 args); branch/spec/prompts-dir completed manually.

## Outcome

- ✅ Impact: Feature specified and ready for planning; constitution alignment verified
- 🧪 Tests: N/A (specification phase)
- 📁 Files: specs/006-complete-ai-pipeline/spec.md, specs/006-complete-ai-pipeline/checklists/requirements.md
- 🔁 Next prompts: /sp.clarify or /sp.plan for 006-complete-ai-pipeline
- 🧠 Reflection: Reusing constitution R1/R2 flag rules kept spec consistent with governance; no clarifications needed because Day 14 rules were already ratified in v1.3.0

## Evaluation notes (flywheel)

- Failure modes observed: create-new-feature.ps1 Join-Path 4-argument call incompatible with Windows PowerShell 5.1 (works in pwsh 6+); script died after spec copy but before prompts dir creation
- Graders run and results (PASS/FAIL): Spec quality checklist PASS (all 16 items)
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Fix script to use nested Join-Path calls for 5.1 compatibility
