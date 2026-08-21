---
id: phr-20260821-tasks-recommendation
title: AI Recommendation task list
stage: tasks
date: 2026-08-21
surface: cli
model: big-pickle
feature: 005-ai-recommendation
branch: 005-ai-recommendation
user: user
command: /sp.tasks
labels: [tasks, ai-feature, recommendation, day-13]
links:
  spec: specs/005-ai-recommendation/spec.md
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - specs/005-ai-recommendation/tasks.md
tests: []
---

## Prompt

Create a clear and actionable task list for implementing the AI Recommendation feature (Day 13).

### Context
- Project: Communication AI
- Priority, Summary, Task Extraction, and Deadline Detection are already working
- We are using Groq as the AI provider
- Keep everything simple and reliable

### Goal:
Generate a short and useful recommended_action for each message.

Example:
Message: "Please send the report before 5 PM."
Recommended action: "Prepare and send the report before the deadline."

### Focus Areas:
- Improve or create the recommendation part of the AI analysis
- Write a clear prompt for generating good recommended actions
- Store recommended_action in MongoDB (inside ai_analysis)
- Display the recommended action on the Dashboard under each message
- Keep the recommendation short, clear, and actionable

### Requirements for the task list:
- Break work into small, clear, executable tasks
- Group tasks logically (Backend, Prompt, Frontend, Testing)
- Write tasks in action language
- Include acceptance criteria for important tasks
- Follow Simplicity First and "AI is Assistive" principles

Save the file in the appropriate location.

## Response snapshot

Created tasks.md with 13 tasks across 5 phases. Tasks organized by 3 user stories (P1: Core recommendation, P2: Language matching, P3: Deadline context). Foundational phase updates the data model. MVP scope is US1 only (4 tasks). All tasks follow checklist format with IDs, labels, and file paths.

## Outcome

- ✅ Impact: Task list created and ready for implementation
- 🧪 Tests: N/A (task generation)
- 📁 Files: specs/005-ai-recommendation/tasks.md
- 🔁 Next prompts: Start implementing tasks
- 🧠 Reflection: Task list is immediately executable — each task has specific file paths and action language

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
