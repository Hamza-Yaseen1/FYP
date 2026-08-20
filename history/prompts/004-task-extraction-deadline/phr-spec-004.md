---
id: phr-spec-004
title: Task Extraction & Deadline Detection Spec
stage: spec
date: 2026-08-20
surface: cli
model: big-pickle
feature: 004-task-extraction-deadline
branch: 004-task-extraction-deadline
user: user
command: spec
labels: [spec, task-extraction, deadline-detection, fyp]
links:
  spec: specs/004-task-extraction-deadline/spec.md
  plan: null
  ticket: null
  adr: null
  pr: null
files:
  - specs/004-task-extraction-deadline/spec.md
  - specs/004-task-extraction-deadline/checklists/requirements.md
tests: []
---

## Prompt

Create a clear and focused specification for two related features:

1. Task Extraction (Day 11)
2. Urgency + Deadline Detection (Day 12)

### Context
- Project: Communication AI
- Priority and Summary agents are already working
- Now the AI should extract tasks and understand deadlines from messages

### Task Extraction Requirements:
- Identify clear actionable tasks from a message
- Example:
  Input: "Send me the FYP slides tonight."
  Output:
  {
    "task": "Send FYP slides",
    "deadline": "Tonight",
    "requires_action": true
  }
- Store extracted tasks in the `tasks` collection in MongoDB
- Link the task to the original message

### Deadline Detection Requirements:
- Understand relative time expressions such as:
  - right now, ASAP, today, tonight, tomorrow, next week, before the meeting
- Convert them into useful deadline information when possible
- If the system can reliably determine an exact date/time, use it (e.g. "August 20, 2026 — 10:00 PM")
- If it cannot determine an exact date/time reliably, keep the original expression (e.g. "Tonight")
- Never invent a deadline

### Please include in the specification:
1. Feature Overview
2. User Stories
3. Input / Output examples
4. Data structure for tasks
5. Acceptance Criteria
6. Edge cases and rules (especially about not inventing deadlines)
7. How these features fit into the current AI analysis flow

Keep it simple and practical for a university FYP.

## Response snapshot

Created specification at `specs/004-task-extraction-deadline/spec.md` with
quality checklist at `specs/004-task-extraction-deadline/checklists/requirements.md`.

### Specification Structure

**3 User Stories:**
- US1 (P1): Extract Tasks from Messages — core extraction capability
- US2 (P1): Detect Deadlines and Urgency — time expression handling
- US3 (P2): View Extracted Tasks on Dashboard — visible output

**12 Functional Requirements** (FR-001 through FR-012):
- Task extraction, deadline detection, storage, display, graceful fallback

**8 Success Criteria** (SC-001 through SC-008):
- ≥85% extraction accuracy, ≤10% false positives, 0% deadline hallucination,
  ≥90% time expression accuracy

**7 Edge Cases** covered:
- No task from informational messages, ambiguous deadlines, long messages,
  AI unavailability, duplicate tasks, unsupported languages

**AI Analysis Flow** documented:
- Single LLM call for priority + summary + tasks + deadlines

### Quality Checklist
All 12 items pass. No [NEEDS CLARIFICATION] markers remain.

## Outcome

- Impact: Feature spec ready for planning phase
- Tests: None required (spec only)
- Files: specs/004-task-extraction-deadline/spec.md, checklists/requirements.md
- Next prompts: /sp.plan or /sp.tasks for implementation planning
- Reflection: Spec aligns with constitution v1.1.0 (AI Feature Guidance sections)

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results: N/A
- Prompt variant: N/A
- Next experiment: N/A
