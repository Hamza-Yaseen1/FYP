---
id: phr-constitution-day21-001
title: Day 21 Task Management Constitution
stage: constitution
date: 2026-08-26
surface: cli
model: opencode/big-pickle
feature: task-management
branch: main
user: user
command: constitution
labels: [constitution, day21, task-management, simplicity-first, user-isolation]
links:
  spec: N/A
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - .specify/memory/constitution.md
tests:
  - N/A
---

## Prompt

Create a focused constitution for Day 21 – Task Management.

### Context
- Project: Communication AI (FYP)
- AI already extracts tasks and deadlines from messages
- Now we need a proper Task Management page

### Goal of Day 21:
Create a clean "My Tasks" page that shows extracted tasks clearly.

Example layout:
My Tasks

🔴 Send FYP slides
Due: Tonight

🟡 Review documentation
Due: Tomorrow

🟢 Read project update
Due: Friday

### Actions for each task:
- Complete
- Snooze
- View message

### Please create a short constitution that covers:
1. Purpose of the Task Management feature
2. Core principles (clear, actionable, simple)
3. How tasks should be displayed
4. Rules for Complete, Snooze, and View message actions
5. Quality bar for this feature

Keep it practical, clean, and user-focused.
Align with Simplicity First principle. 

## Response snapshot

Updated `.specify/memory/constitution.md` with:
- New Day 21 Task Management section
- Version bump 1.8.0 → 1.9.0 (MINOR)
- Last Amended date: 2026-08-26
- Sync Impact Report updated at top
- Compliance checklist expanded with 12 task management-specific checks

## Outcome

- ✅ Impact: Constitution updated with task management rules
- 🧪 Tests: N/A (constitution documentation)
- 📁 Files: .specify/memory/constitution.md
- 🔁 Next prompts: spec, plan, tasks for task-management feature
- 🧠 Reflection: Day 21 constitution focuses on simplicity and clarity for task display and actions

## Evaluation notes (flybook)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A