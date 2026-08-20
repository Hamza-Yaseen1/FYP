---
id: phr-plan-004
title: Task Extraction & Deadline Detection Plan
stage: plan
date: 2026-08-20
surface: cli
model: big-pickle
feature: 004-task-extraction-deadline
branch: 004-task-extraction-deadline
user: user
command: plan
labels: [plan, task-extraction, deadline-detection, fyp]
links:
  spec: specs/004-task-extraction-deadline/spec.md
  plan: specs/004-task-extraction-deadline/plan.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/004-task-extraction-deadline/plan.md
  - specs/004-task-extraction-deadline/research.md
  - specs/004-task-extraction-deadline/data-model.md
  - specs/004-task-extraction-deadline/contracts/messages-api.md
  - specs/004-task-extraction-deadline/quickstart.md
  - AGENTS.md
tests: []
---

## Prompt

Create a practical technical implementation plan for two related features:

1. Task Extraction (Day 11)
2. Urgency + Deadline Detection (Day 12)

### Context
- Project: Communication AI
- Priority Agent and Summary Agent are already working
- We are using Groq as the AI provider
- Keep everything simple and reliable

### Goals:
- Extract clear tasks from messages
- Detect and understand deadlines (including relative terms like tonight, tomorrow, ASAP, etc.)
- Store extracted tasks in the `tasks` collection
- Never invent deadlines if the AI is not confident

### Example:
Input: "Send me the FYP slides tonight."
Output:
{
  "task": "Send FYP slides",
  "deadline": "Tonight",
  "requires_action": true
}

### Please include in the plan:
1. Goal of this phase
2. Technical approach (keep it simple)
3. Files that need to be created or updated
4. How Task Extraction + Deadline Detection will work (step-by-step)
5. How tasks will be stored in MongoDB
6. How results will be shown on the Dashboard / Tasks page
7. Implementation steps in order
8. Testing plan
9. Definition of Done

Follow the principles: Simplicity First and AI is Assistive (never invent deadlines).
Save the plan in the appropriate location.

## Response snapshot

Created implementation plan at `specs/004-task-extraction-deadline/plan.md`
with supporting artifacts: research.md, data-model.md, contracts/messages-api.md,
quickstart.md. Updated AGENTS.md via agent context script.

### Plan Structure

**Constitution Check**: All 9 principles pass (including new task/deadline rules)

**Phase 0 Research** (3 decisions):
1. Combine priority + task extraction in single LLM call
2. Structured task objects (ExtractedTask) in prompt output
3. Dual-write: embedded in message + separate tasks collection

**Phase 1 Design**:
- Data model: ExtractedTask Pydantic model, Task MongoDB document
- API contracts: 3 new endpoints (GET /tasks, PUT /tasks/{id}/status, DELETE /tasks/{id})
- Quickstart guide with test cases

**Implementation Roadmap**:
- Day 11: Backend (model, prompt, analyzer, routes, tests)
- Day 12: Frontend (MessageList badge, Tasks page, TaskList component)

**Files to create**: 4 (task.py, tasks.py, TaskList.tsx, test_task_extraction.py)
**Files to update**: 7 (base.py, groq.py, analyzer.py, messages.py, webhooks.py,
  MessageList.tsx, dashboard/page.tsx, tasks/page.tsx)

**Testing**: 6 unit test scenarios + 9 manual test cases

## Outcome

- Impact: Full implementation plan ready for task generation
- Tests: None required (plan only)
- Files: specs/004-task-extraction-deadline/plan.md + 4 supporting artifacts
- Next prompts: /sp.tasks to generate implementation task list
- Reflection: Plan follows Simplicity First — extends existing patterns, minimal new files

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results: N/A
- Prompt variant: N/A
- Next experiment: N/A
