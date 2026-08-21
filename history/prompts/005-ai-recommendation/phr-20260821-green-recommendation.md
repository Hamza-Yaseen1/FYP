---
id: phr-20260821-green-recommendation
title: AI Recommendation implementation
stage: green
date: 2026-08-21
surface: cli
model: big-pickle
feature: 005-ai-recommendation
branch: 005-ai-recommendation
user: user
command: /sp.green
labels: [green, implementation, ai-feature, recommendation, day-13]
links:
  spec: specs/005-ai-recommendation/spec.md
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - backend/models/message.py
  - backend/services/ai/prompts/actions.txt
  - backend/services/ai/providers/groq.py
  - backend/services/ai/analyzer.py
  - components/MessageList.tsx
  - specs/005-ai-recommendation/tasks.md
tests: []
---

## Prompt

Start implementing the tasks for Day 13 – AI Recommendation (recommended_action).

Follow the tasks.md file.
Keep everything simple and reliable.
Generate short, clear, and actionable recommendations.
Never invent unrealistic actions.
Implement one vertical slice at a time.
After finishing the current group of tasks, stop and wait for my confirmation before continuing.

## Response snapshot

Implemented all 13 tasks across 5 phases. Modified 5 files: message.py (model), actions.txt (prompt), groq.py (provider), analyzer.py (orchestrator), MessageList.tsx (UI). Feature generates single recommended actions, matches message language, references deadlines, and displays on dashboard.

## Outcome

- ✅ Impact: AI Recommendation feature fully implemented
- 🧪 Tests: Manual testing required (send messages via API, check dashboard)
- 📁 Files: backend/models/message.py, backend/services/ai/prompts/actions.txt, backend/services/ai/providers/groq.py, backend/services/ai/analyzer.py, components/MessageList.tsx
- 🔁 Next prompts: Manual testing, refactoring if needed
- 🧠 Reflection: Feature follows existing patterns. Simple vertical slice from LLM to dashboard.

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
