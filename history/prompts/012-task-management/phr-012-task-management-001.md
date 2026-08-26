---
id: phr-012-task-management-001
title: Task Management Spec
stage: spec
date: 2026-08-26
surface: cli
model: opencode/big-pickle
feature: 012-task-management
branch: 012-task-management
user: user
command: spec
labels: [spec, task-management, day21, simplicity-first]
links:
  spec: ../specs/012-task-management/spec.md
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - specs/012-task-management/spec.md
  - specs/012-task-management/checklists/requirements.md
tests:
  - N/A
---

## Prompt

Create a clear and focused specification for Day 21 – Task Management.

### Context
- Project: Communication AI
- AI already extracts tasks and deadlines from messages
- Now we need a proper and clean Task Management experience

### Goal:
Create a "My Tasks" page that shows all extracted tasks clearly.

Example:
My Tasks

🔴 Send FYP slides
Due: Tonight

🟡 Review documentation
Due: Tomorrow

🟢 Read project update
Due: Friday

### Actions for each task:
- Complete → mark task as done
- Snooze → temporarily hide or postpone the task
- View message → open the original message that created this task

### Requirements:
- Only show tasks that belong to the logged-in user
- Show priority (color + icon)
- Show deadline clearly
- Tasks should be sorted in a useful way (Urgent first, then by deadline)
- After marking Complete, task should move out of the active list

### Please include in the specification:
1. Feature Overview
2. User Stories
3. Task display rules
4. Actions behavior (Complete, Snooze, View message)
5. Acceptance Criteria
6. Edge cases

Keep it simple, clean, and practical for a university FYP. 

## Response snapshot

Created specification for Day 21 Task Management:
- Generated branch `012-task-management` and spec file
- Wrote comprehensive specification with 4 user stories, 14 functional requirements, 8 success criteria
- Created quality checklist and validated all items passed
- Identified key entities: Task, User, Message
- Documented assumptions and edge cases

## Outcome

- ✅ Impact: Complete specification ready for planning phase
- 🧪 Tests: N/A (specification documentation)
- 📁 Files: specs/012-task-management/spec.md, specs/012-task-management/checklists/requirements.md
- 🔁 Next prompts: `/sp.plan` to create implementation plan
- 🧠 Reflection: Specification follows Simplicity First principle with clear user stories and testable requirements

## Evaluation notes (flybook)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A