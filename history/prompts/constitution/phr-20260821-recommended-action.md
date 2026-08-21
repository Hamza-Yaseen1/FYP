---
id: phr-20260821-recommended-action
title: Add Recommended Action constitution
stage: constitution
date: 2026-08-21
surface: cli
model: big-pickle
feature: N/A
branch: N/A
user: user
command: /sp.constitution
labels: [constitution, ai-feature, recommended-action]
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

Create a focused constitution for the AI Recommendation feature (Day 13).

### Context
- Project: Communication AI (FYP)
- We already have Priority, Summary, Task Extraction, and Deadline Detection working
- Now we want the AI to suggest a clear recommended action for the user

### Goal of this feature:
When a message arrives, the AI should also generate a short and useful recommended action.

Example:
Message: "Please send the report before 5 PM."

AI should return:
- Priority: Urgent
- Summary: Report needs to be submitted before 5 PM.
- Recommended action: "Prepare and send the report before the deadline."

### Please create a short constitution that covers:
1. Purpose of the Recommended Action feature
2. Core principles (helpful, clear, actionable, no hallucination)
3. What a good recommended action looks like
4. What the AI should NEVER do when generating recommendations
5. Quality bar for this feature

Keep it practical and aligned with the main project constitution (Simplicity First, AI is Assistive not Magical).

## Response snapshot

Updated constitution to v1.2.0 with new AI Feature Guidance section for Recommended Action. Added purpose, input/output contract, quality rules, anti-hallucination guardrails, and quality bar targets. Updated compliance checklist with 2 new checks. All templates verified as compatible.

## Outcome

- ✅ Impact: Constitution updated with new feature guidance section
- 🧪 Tests: N/A (constitution update)
- 📁 Files: .specify/memory/constitution.md
- 🔁 Next prompts: N/A
- 🧠 Reflection: MINOR version bump appropriate - new feature guidance added without changing existing principles

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
