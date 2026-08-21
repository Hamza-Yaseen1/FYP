---
id: phr-20260821-plan-pipeline
title: Day 14 Pipeline Implementation Plan
stage: plan
date: 2026-08-21
surface: cli
model: big-pickle
feature: 006-complete-ai-pipeline
branch: 006-complete-ai-pipeline
user: user
command: /sp.plan
labels: [plan, ai-pipeline, dashboard, day-14]
links:
  spec: specs/006-complete-ai-pipeline/spec.md
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - specs/006-complete-ai-pipeline/plan.md
  - specs/006-complete-ai-pipeline/research.md
  - specs/006-complete-ai-pipeline/data-model.md
  - specs/006-complete-ai-pipeline/contracts/messages-api.md
  - specs/006-complete-ai-pipeline/quickstart.md
  - AGENTS.md
tests: []
---

## Prompt

Create a practical technical implementation plan for Day 14 – Complete AI Pipeline.

### Context
- Project: Communication AI
- Individual AI features are already built (Priority, Summary, Task Extraction, Deadline, Recommended Action)
- Now we need to make the full pipeline work smoothly and display a clear “Needs Attention” card on the Dashboard

### Goal:
Message → Full AI Analysis → MongoDB → Dashboard shows:

🔴 NEEDS ATTENTION
Send FYP slides
WhatsApp • Ali
Deadline: Tonight
Why it matters: A task with a near deadline was detected.
Recommended: Send the slides before tonight.

### Please include in the plan:
1. Goal of this phase
2. Technical approach (keep it simple)
3. Files that need to be created or updated
4. How the complete pipeline should work (step-by-step)
5. Final data structure that should be stored
6. How the “Needs Attention” section should be built on the Frontend
7. Implementation steps in order
8. Testing plan
9. Definition of Done

Follow Simplicity First principle.
Save the plan in the appropriate location.

## Response snapshot

Explored actual codebase first (webhooks.py already inserts → analyze_message → update; analyzer orchestrates priority+tasks+deadlines in one provider call plus summary and recommendation calls; MessageList renders existing fields; attention page is a static placeholder). Wrote plan grounded in real paths: NEW backend/services/ai/attention.py (pure R1/R2 evaluation, keyword-based near-term deadline check), UPDATE analyzer.py + models/message.py (needs_attention, attention_reason), UPDATE webhooks.py (10-minute duplicate guard), NEW components/NeedsAttentionCard.tsx reused by dashboard and attention pages (client-side filter of GET /messages). Phase 0 research.md documents 6 decisions with alternatives rejected (no second LLM call, no dateparser dep, no new endpoint). Phase 1 data-model.md, contracts/messages-api.md (additive-only response fields), quickstart.md with 5 verification cases. Constitution Check: all 7 gates PASS pre-design; no violations so no Complexity Tracking. Agent context (AGENTS.md) updated via update-agent-context.ps1.

## Outcome

- ✅ Impact: Full planning artifact set generated; implementation-ready
- 🧪 Tests: N/A (planning phase); test strategy defined in plan + quickstart
- 📁 Files: plan.md, research.md, data-model.md, contracts/messages-api.md, quickstart.md, AGENTS.md
- 🔁 Next prompts: /sp.tasks for 006-complete-ai-pipeline
- 🧠 Reflection: Key insight — pipeline entry point already exists, so Day 14 is mostly an additive flag computation plus frontend card; keeping evaluation as a pure function makes it trivially testable without LLM mocks

## Evaluation notes (flywheel)

- Failure modes observed: None this run
- Graders run and results (PASS/FAIL): Constitution Check 7/7 PASS
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
