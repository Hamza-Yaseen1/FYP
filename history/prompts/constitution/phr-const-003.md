---
id: phr-const-003
title: Summary Agent & Delete Message Constitution
stage: constitution
date: 2026-08-19
surface: cli
model: big-pickle
feature: general
branch: 1-baseline-spec
user: user
command: constitution
labels: [constitution, summary-agent, delete-message, fyp]
links:
  spec: null
  plan: null
  ticket: null
  adr: null
  pr: null
files:
  - docs/summary-agent-delete-constitution.md
tests: []
---

## Prompt

Create a focused constitution for two things:

1. Summary Agent (Day 10)
2. Delete Message feature on the Dashboard

### Context
- Project: Communication AI (FYP)
- We already have Priority Agent working
- Now we are adding the Summary Agent
- Also need a simple "Delete" option for messages on the Dashboard

### For the Summary Agent:
- Purpose: Create a short, clear summary of the message
- Input example: "Hey bro, just wanted to remind you that the teacher said we have to submit the final documentation before tomorrow's meeting."
- Expected output: "Final documentation must be submitted before tomorrow's meeting."
- Principles: Keep summaries short, accurate, and useful. Never invent information.

### For Delete Message:
- User should be able to delete a message from the Dashboard
- It should remove the message from MongoDB
- Keep it simple and safe

Please create a short and clear constitution that covers:
1. Purpose of the Summary Agent
2. Principles for good summaries
3. What the Summary Agent should never do
4. Rules for the Delete Message feature
5. Quality bar for both features

Keep it practical and aligned with the main project constitution (Simplicity First).

## Response snapshot

Created constitution at `docs/summary-agent-delete-constitution.md` covering both Summary Agent and Delete Message feature.

### Constitution Structure

**Part 1: Summary Agent**
- 5 Core Principles: Accuracy, Conciseness, Preserve Action Items, No Invention, Consistent Style
- Quality Bar: 85% accuracy, < 2 seconds, < 30 words
- Examples provided

**Part 2: Delete Message**
- 4 Core Principles: User Initiated Only, Confirmation Required, Permanent Deletion, No Cascade Effects
- Quality Bar: 100% success, < 1 second

### Key Design Decisions
- Summary: 1-2 sentences, under 30 words
- Summary preserves action items
- Delete requires confirmation dialog
- Delete is permanent (no soft-delete)
- Both follow Simplicity First principle

## Outcome

- Impact: Governance document for next features
- Tests: None required (constitution only)
- Files: docs/summary-agent-delete-constitution.md
- Next prompts: /sp.spec or /sp.plan for each feature
- Reflection: Constitution follows parent principles, practical for FYP

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results: N/A
- Prompt variant: N/A
- Next experiment: N/A
