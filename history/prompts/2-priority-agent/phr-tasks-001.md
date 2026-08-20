---
id: phr-tasks-001
title: Priority Agent Task List
stage: tasks
date: 2026-08-19
surface: cli
model: big-pickle
feature: 2-priority-agent
branch: 2-priority-agent
user: user
command: tasks
labels: [tasks, priority-agent, ai, fyp]
links:
  spec: specs/2-priority-agent/spec.md
  plan: specs/2-priority-agent/plan.md
  tasks: specs/2-priority-agent/tasks.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/2-priority-agent/tasks.md
tests: []
---

## Prompt

Create a clear and actionable task list for implementing the Priority Agent (Day 9).

### Context
- Project: Communication AI
- We are building only the Priority Agent right now
- Goal: Reliably classify messages into URGENT, IMPORTANT, NORMAL, or LOW
- Keep it simple — no multi-agent system

### Requirements for the task list:
- Break the work into small, clear, executable tasks
- Group tasks logically (Backend, Prompt, Integration, Frontend, Testing)
- Write tasks in action language (e.g. "Create priority_agent.py", "Update webhook to use Priority Agent")
- Include acceptance criteria for important tasks
- Follow Simplicity First principle

### Focus areas:
1. Create / improve the Priority Agent
2. Write a strong priority classification prompt
3. Connect it to the existing AI analysis flow
4. Store priority result in MongoDB
5. Show priority badge on the Dashboard
6. Testing

Save the file as `specs/priority-agent/tasks.md` or in the appropriate location.

## Response snapshot

Created task list at `specs/2-priority-agent/tasks.md` with 37 tasks organized by user stories.

### Task Summary
- Phase 1: Setup (3 tasks)
- Phase 2: Foundational (3 tasks)
- Phase 3: US1 - Auto Classification (7 tasks)
- Phase 4: US2 - Override (6 tasks)
- Phase 5: US3 - Confidence (4 tasks)
- Phase 6: Polish & Testing (14 tasks)

### Key Design Decisions
- MVP scope: T001-T013 (Setup + Foundational + US1)
- Parallel opportunities identified
- Clear dependency graph
- Each task is specific and executable

## Outcome

- Impact: Task list ready for implementation
- Tests: None required (task list only)
- Files: specs/2-priority-agent/tasks.md
- Next prompts: /sp.red (TDD), or start implementing T001
- Reflection: Tasks follow checklist format, organized by user stories

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results: N/A
- Prompt variant: N/A
- Next experiment: N/A
