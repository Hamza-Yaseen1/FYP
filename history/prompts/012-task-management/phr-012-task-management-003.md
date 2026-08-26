---
id: phr-012-task-management-003
title: Task Management Tasks
stage: tasks
date: 2026-08-26
surface: cli
model: opencode/big-pickle
feature: 012-task-management
branch: 012-task-management
user: user
command: tasks
labels: [tasks, task-management, day21, simplicity-first, vertical-slices]
links:
  spec: ../specs/012-task-management/spec.md
  plan: ../specs/012-task-management/plan.md
  tasks: ../specs/012-task-management/tasks.md
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - specs/012-task-management/tasks.md
tests:
  - N/A
---

## Prompt

Create a clear and actionable task list for Day 21 – Task Management.

### Context
- Project: Communication AI
- AI already extracts tasks and deadlines
- Authentication and User Isolation are working
- Now build a proper "My Tasks" page

### Goal:
Show tasks like this:

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

### Focus Areas:
- Fetch and display tasks of the logged-in user
- Show priority and deadline clearly
- Implement Complete, Snooze, and View message actions
- Keep the UI clean and easy to use

### Requirements for the task list:
- Break work into small, clear, executable tasks
- Group tasks logically (Backend, Frontend, Actions, Testing)
- Write tasks in action language
- Include acceptance criteria for important tasks
- Follow Simplicity First principle

Save the file in the appropriate location. 

The tasks.md should be immediately executable - each task must be specific enough that an LLM can complete it without additional context.

## Response snapshot

Created comprehensive task list for Day 21 Task Management:
- 40 tasks organized by 4 user stories
- Foundational phase with 5 tasks (model updates, indexes, base components)
- User Story 1 (View My Tasks): 9 tasks - core display functionality
- User Story 2 (Complete Task): 6 tasks - complete action
- User Story 3 (Snooze Task): 7 tasks - snooze functionality
- User Story 4 (View Message): 7 tasks - message context
- Polish phase: 6 tasks - accessibility, performance, security
- Each story independently testable
- MVP scope: User Story 1 only

## Outcome

- ✅ Impact: Complete task list ready for implementation
- 🧪 Tests: N/A (task list documentation)
- 📁 Files: specs/012-task-management/tasks.md
- 🔁 Next prompts: Implementation can begin with `/sp.red` or direct coding
- 🧠 Reflection: Tasks follow Simplicity First principle, organized by user story for independent implementation

## Evaluation notes (flybook)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A