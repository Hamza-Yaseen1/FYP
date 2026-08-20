---
id: phr-spec-003
title: Summary Agent & Delete Message Specification
stage: spec
date: 2026-08-20
surface: cli
model: big-pickle
feature: 3-summary-delete
branch: 3-summary-delete
user: user
command: spec
labels: [spec, summary-agent, delete-message, fyp]
links:
  spec: specs/3-summary-delete/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/3-summary-delete/spec.md
  - specs/3-summary-delete/checklists/requirements.md
tests: []
---

## Prompt

Create a clear and focused specification for two features:

1. Summary Agent (Day 10)
2. Delete Message option on the Dashboard

### Context
- Project: Communication AI
- Priority Agent is already working
- Now we need a Summary Agent that creates short, useful summaries
- Also add ability to delete messages from the Dashboard

### Summary Agent Requirements:
- Input: Full message text
- Output: A short and clear summary (1 sentence preferred)
- Example:
  Input: "Hey bro, just wanted to remind you that the teacher said we have to submit the final documentation before tomorrow's meeting."
  Output: "Final documentation must be submitted before tomorrow's meeting."
- Summary should be accurate and never invent information
- Summary should be shown on the Dashboard

### Delete Message Requirements:
- User can delete a message from the Dashboard
- It should permanently remove the message from MongoDB
- Add a clear "Delete" button on each message card
- Ask for confirmation before deleting (optional but preferred)
- After deletion, the message should disappear from the list

### Please include in the specification:
1. Feature Overview
2. User Stories
3. Input / Output for Summary Agent
4. Acceptance Criteria for both features
5. Edge cases
6. How both features fit into the current system

Keep it simple and practical for a university FYP.

## Response snapshot

Created specification for Summary Agent & Delete Message at `specs/3-summary-delete/spec.md`.

Specification includes:
- 3 user stories (P1: Auto-summary, P2: Delete, P3: Summary display)
- 14 functional requirements (8 for Summary, 6 for Delete)
- 6 success criteria
- Clear behavior rules for both features
- Edge cases identified
- Quality checklist created (all items pass)

Key decisions:
- Summary: 1-2 sentences, under 30 words
- Summary preserves action items
- Delete requires confirmation dialog
- Delete is permanent (no soft-delete)
- Both follow Simplicity First principle

## Outcome

- Impact: Established specification for Summary Agent & Delete Message
- Tests: None required (specification only)
- Files: specs/3-summary-delete/spec.md, specs/3-summary-delete/checklists/requirements.md
- Next prompts: /sp.plan or /sp.tasks
- Reflection: Spec follows constitution principles - simple, practical, FYP-appropriate

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results: N/A
- Prompt variant: N/A
- Next experiment: N/A
