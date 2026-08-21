---
id: phr-20260821-plan-recommendation
title: AI Recommendation implementation plan
stage: plan
date: 2026-08-21
surface: cli
model: big-pickle
feature: 005-ai-recommendation
branch: 005-ai-recommendation
user: user
command: /sp.plan
labels: [plan, ai-feature, recommendation, day-13]
links:
  spec: specs/005-ai-recommendation/spec.md
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - specs/005-ai-recommendation/plan.md
  - specs/005-ai-recommendation/research.md
  - specs/005-ai-recommendation/data-model.md
  - specs/005-ai-recommendation/quickstart.md
  - specs/005-ai-recommendation/contracts/api.md
  - AGENTS.md
tests: []
---

## Prompt

Create a practical technical implementation plan for the AI Recommendation feature (Day 13).

### Context
- Project: Communication AI
- Priority, Summary, Task Extraction, and Deadline Detection are already working
- We are using Groq as the AI provider
- Keep everything simple and reliable

### Goal:
Add a clear recommended_action for each analyzed message.

Example:
Message: "Please send the report before 5 PM."

AI should return:
- Priority: Urgent
- Summary: Report needs to be submitted before 5 PM.
- Recommended action: "Prepare and send the report before the deadline."

### Please include in the plan:
1. Goal of this phase
2. Technical approach (keep it simple)
3. Files that need to be created or updated
4. How the Recommended Action will be generated (step-by-step)
5. How it will be stored in MongoDB
6. How it will be shown on the Dashboard
7. Implementation steps in order
8. Testing plan
9. Definition of Done

Follow the principles: Simplicity First and AI is Assistive (never invent unrealistic actions).
Save the plan in the appropriate location.

## Response snapshot

Created implementation plan for AI Recommended Action feature. Plan includes 5 implementation steps across 4 files. Research resolved 4 design decisions. Data model extends existing ai_analysis subdocument with new `recommended_action` string field. Quickstart and API contracts created. Constitution check passed with no violations.

## Outcome

- ✅ Impact: Plan created and ready for task generation
- 🧪 Tests: N/A (plan creation)
- 📁 Files: specs/005-ai-recommendation/plan.md, research.md, data-model.md, quickstart.md, contracts/api.md, AGENTS.md
- 🔁 Next prompts: /sp.tasks
- 🧠 Reflection: Plan follows existing patterns in codebase. Low risk changes.

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
