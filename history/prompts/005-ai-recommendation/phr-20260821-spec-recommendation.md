---
id: phr-20260821-spec-recommendation
title: AI Recommendation feature spec
stage: spec
date: 2026-08-21
surface: cli
model: big-pickle
feature: 005-ai-recommendation
branch: 005-ai-recommendation
user: user
command: /sp.specify
labels: [spec, ai-feature, recommendation, day-13]
links:
  spec: specs/005-ai-recommendation/spec.md
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - specs/005-ai-recommendation/spec.md
  - specs/005-ai-recommendation/checklists/requirements.md
tests: []
---

## Prompt

Create a clear and focused specification for the AI Recommendation feature (Day 13).

### Context
- Project: Communication AI
- Priority, Summary, Task Extraction, and Deadline Detection are already working
- Now we want the AI to generate a short and useful recommended action

### Goal:
When a message is analyzed, the AI should also return a clear recommended action.

Example:
Message: "Please send the report before 5 PM."

Expected AI output:
- Priority: Urgent
- Summary: Report needs to be submitted before 5 PM.
- Recommended action: "Prepare and send the report before the deadline."

### Please include in the specification:
1. Feature Overview
2. Purpose of Recommended Action
3. Input / Output examples
4. Rules for generating good recommendations
5. What the AI should never do
6. User Stories
7. Acceptance Criteria
8. How the recommended action will be stored and shown on the Dashboard

Keep it simple and practical for a university FYP.
Follow the principles: Simplicity First and AI is Assistive (never invent actions).

## Response snapshot

Created spec for AI Recommended Action feature on branch 005-ai-recommendation. Included 3 user stories (P1: Dashboard display, P2: Language matching, P3: Deadline context), 11 functional requirements, 5 success criteria, and edge cases. Quality checklist validated all items on first iteration.

## Outcome

- ✅ Impact: Spec created and ready for planning
- 🧪 Tests: N/A (spec creation)
- 📁 Files: specs/005-ai-recommendation/spec.md, specs/005-ai-recommendation/checklists/requirements.md
- 🔁 Next prompts: /sp.clarify or /sp.plan
- 🧠 Reflection: MINOR version bump appropriate - new feature guidance added without changing existing principles

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
