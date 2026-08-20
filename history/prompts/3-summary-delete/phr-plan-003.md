---
id: phr-plan-003
title: Summary Agent & Delete Message Plan
stage: plan
date: 2026-08-20
surface: cli
model: big-pickle
feature: 3-summary-delete
branch: 3-summary-delete
user: user
command: plan
labels: [plan, summary-agent, delete-message, fyp]
links:
  spec: specs/3-summary-delete/spec.md
  plan: specs/3-summary-delete/plan.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/3-summary-delete/plan.md
tests: []
---

## Prompt

Create a practical technical implementation plan for two features:

1. Summary Agent (Day 10)
2. Delete Message option on the Dashboard

### Context
- Project: Communication AI
- Priority Agent is already working
- We are using Groq as the AI provider
- Keep everything simple and reliable

### Summary Agent Goals:
- Generate a short, clear summary of the message
- Example:
  Input → "Hey bro, just wanted to remind you that the teacher said we have to submit the final documentation before tomorrow's meeting."
  Output → "Final documentation must be submitted before tomorrow's meeting."
- Show the summary on the Dashboard under each message

### Delete Message Goals:
- Add a Delete button on each message card in the Dashboard
- When clicked, permanently delete the message from MongoDB
- Refresh the list after deletion
- Keep the UI clean and simple

### Please include in the plan:
1. Goal of this phase
2. Technical approach (keep it simple)
3. Files that need to be created or updated
4. How the Summary Agent will work (step-by-step)
5. How Delete Message will work (API + Frontend)
6. Implementation steps in order
7. Testing plan
8. Definition of Done

Follow Simplicity First principle.
Save the plan in the appropriate location.

## Response snapshot

Created implementation plan at `specs/3-summary-delete/plan.md`.

### Plan Structure

**Goal**: Add Summary Agent and Delete Message features

**Technical Approach**:
- Summary Agent: Single LLM call with focused prompt
- Delete Message: Simple REST endpoint

**Files to Create**:
- `backend/services/ai/prompts/summary.txt`
- `backend/services/ai/agents/summary.py`

**Files to Update**:
- `backend/services/ai/providers/groq.py`
- `backend/services/ai/analyzer.py`
- `backend/models/message.py`
- `backend/routes/messages.py`
- `components/MessageList.tsx`

**Key Design Decisions**:
- Summary: 1-2 sentences, under 30 words
- Summary stored in ai_analysis.summary field
- Delete: Permanent removal, confirmation required
- Both follow Simplicity First principle

## Outcome

- Impact: Implementation plan ready for execution
- Tests: None required (plan only)
- Files: specs/3-summary-delete/plan.md
- Next prompts: /sp.tasks or start implementing
- Reflection: Plan follows constitution principles

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results: N/A
- Prompt variant: N/A
- Next experiment: N/A
