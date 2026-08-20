---
id: phr-const-002
title: Create Priority Agent Constitution
stage: constitution
date: 2026-08-19
surface: cli
model: big-pickle
feature: priority-agent
branch: 1-baseline-spec
user: user
command: constitution
labels: [constitution, ai, priority-agent, fyp]
links:
  spec: specs/1-baseline-spec/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - docs/priority-agent-constitution.md
tests: []
---

## Prompt

Create a focused constitution for the Priority Agent feature of my Communication AI project.

Context:
- We already have a main CONSTITUTION.md for the overall project.
- Now we are building the first real AI agent: Priority Agent.
- This agent's only job is to classify a message into one of these levels:
  - URGENT
  - IMPORTANT
  - NORMAL
  - LOW

Please create a short and clear constitution specifically for this Priority Agent that includes:

1. Purpose of the Priority Agent
2. Core Principles for this agent (keep it simple and reliable)
3. What the agent should do
4. What the agent should NEVER do (e.g. invent urgency, over-classify as Urgent)
5. Decision rules for each priority level
6. Quality bar for this agent

Keep it practical and aligned with the main project constitution (Simplicity First, AI is Assistive not Magical).
Save it as `docs/priority-agent-constitution.md` or update the relevant section.

## Response snapshot

Created focused constitution for Priority Agent at `docs/priority-agent-constitution.md`.

Constitution includes:
- Purpose statement (single responsibility: classify messages)
- 5 Core Principles (Simplicity, Evidence-Based, Conservative Urgency, Explainable, User Override)
- Clear DO/DON'T lists
- Decision rules for each priority level (URGENT, IMPORTANT, NORMAL, LOW)
- Quality bar (80% accuracy, 2s response, confidence thresholds)
- Alignment matrix with parent constitution

Key decisions:
- Four levels only (no scoring/granularity)
- Conservative urgency (default to NORMAL when uncertain)
- Explainable decisions required
- User override always allowed

## Outcome

- Impact: Established governance for Priority Agent implementation
- Tests: None required (constitution only)
- Files: docs/priority-agent-constitution.md
- Next prompts: Implementation of Priority Agent following this constitution
- Reflection: Constitution is focused, practical, and aligned with parent principles

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results: N/A
- Prompt variant: N/A
- Next experiment: N/A
