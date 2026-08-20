---
id: phr-tasks-004
title: Task Extraction & Deadline Detection Tasks
stage: tasks
date: 2026-08-20
surface: cli
model: big-pickle
feature: 004-task-extraction-deadline
branch: 004-task-extraction-deadline
user: user
command: tasks
labels: [tasks, task-extraction, deadline-detection, fyp]
links:
  spec: specs/004-task-extraction-deadline/spec.md
  plan: specs/004-task-extraction-deadline/plan.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/004-task-extraction-deadline/tasks.md
tests: []
---

## Prompt

Create a clear and actionable task list for implementing two related features:

1. Task Extraction (Day 11)
2. Urgency + Deadline Detection (Day 12)

### Context
- Project: Communication AI
- Priority and Summary agents are already working
- We are using Groq as the AI provider
- Keep everything simple and reliable

### Focus Areas:

**Task Extraction:**
- Extract clear actionable tasks from messages
- Example: "Send me the FYP slides tonight." → task = "Send FYP slides"
- Store tasks in the `tasks` collection
- Link each task to the original message

**Deadline Detection:**
- Understand relative time expressions (tonight, tomorrow, ASAP, today, next week, before the meeting, etc.)
- Convert them into useful deadline information when possible
- Never invent a deadline if not confident
- Store the deadline with the task

### Requirements for the task list:
- Break work into small, clear, executable tasks
- Group tasks logically (Backend, Prompt, Database, Frontend, Testing)
- Write tasks in action language
- Include acceptance criteria for important tasks
- Follow Simplicity First and "never invent deadlines" principles

Save the file in the appropriate location.

## Response snapshot

Created task list at `specs/004-task-extraction-deadline/tasks.md` with 20 tasks
across 4 phases.

### Task Breakdown

**Phase 1: Foundational** (3 tasks)
- T001-T003: ExtractedTask model, AIAnalysisResult update, AIAnalysis update

**Phase 2: US1+US2 — Task Extraction & Deadline Detection** (9 tasks)
- T004: Tests (write first, verify fail)
- T005-T006: Prompt updates (parallel)
- T007: Groq provider parsing
- T008: Analyzer task storage
- T009-T010: Route updates
- T011-T012: Task CRUD routes + registration

**Phase 3: US3 — Dashboard View** (4 tasks)
- T013-T014: MessageList badge + TaskList component (parallel)
- T015-T016: Tasks page + Dashboard summary card

**Phase 4: Polish** (4 tasks)
- T017-T020: Tests, manual testing, constitution compliance, doc updates

### Key Decisions
- US1 and US2 combined (tightly coupled, both P1)
- 20 total tasks, 5 parallel opportunities
- Tests written first (TDD for T004)
- MVP scope: Phase 1 + Phase 2 (backend extraction working)

## Outcome

- Impact: Task list ready for implementation
- Tests: None required (tasks only)
- Files: specs/004-task-extraction-deadline/tasks.md
- Next prompts: Start implementing with T001 (ExtractedTask model)
- Reflection: Tasks follow checklist format, each has file path, organized by story

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results: N/A
- Prompt variant: N/A
- Next experiment: N/A
