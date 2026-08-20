---
id: phr-const-004
title: Task Extraction & Deadline Detection Constitution
stage: constitution
date: 2026-08-20
surface: cli
model: big-pickle
feature: general
branch: 1-baseline-spec
user: user
command: constitution
labels: [constitution, task-extraction, deadline-detection, fyp]
links:
  spec: null
  plan: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/memory/constitution.md
  - CONSTITUTION.md
tests: []
---

## Prompt

Create a focused constitution for two related features:

1. Task Extraction (Day 11)
2. Urgency + Deadline Detection (Day 12)

### Context
- Project: Communication AI (FYP)
- Priority Agent and Summary Agent are already working
- Now we want the AI to extract tasks and understand deadlines from messages

### Task Extraction Goals:
- Identify clear tasks from a message
- Example:
  Input: "Send me the FYP slides tonight."
  Output:
  {
    "task": "Send FYP slides",
    "deadline": "Tonight",
    "requires_action": true
  }
- Store extracted tasks in the `tasks` collection

### Deadline & Urgency Goals:
- Understand relative time expressions such as:
  - right now, ASAP, today, tonight, tomorrow, next week, before the meeting
- Convert them into useful deadline information when possible
- If an exact date/time can be reliably determined, use it
- If not, keep the original expression (e.g. "Tonight") — never invent a date

### Please create a short constitution that covers:
1. Purpose of Task Extraction and Deadline Detection
2. Core principles (accuracy, no hallucination, simplicity)
3. What the AI should do
4. What the AI should NEVER do (especially about inventing deadlines)
5. Quality bar for these features

Keep it practical and aligned with the main project constitution (Simplicity First, AI is Assistive not Magical).

## Response snapshot

Updated constitution at `.specify/memory/constitution.md` and root `CONSTITUTION.md`
with focused guidance for Task Extraction and Urgency + Deadline Detection.

### Constitution Structure

**AI Feature Guidance (new section added):**
- Task Extraction: purpose, input/output contract, 5 MUST rules, 4 MUST NEVER rules, quality bar
- Urgency & Deadline Detection: purpose, supported expressions table, 5 MUST rules, 5 MUST NEVER rules, quality bar

**Expanded existing sections:**
- Quality Bar: added "Task Extraction & Deadline Detection Targets" subsection
- Compliance Checklist: added 3 new checks (false positives, invented deadlines, time expression preservation)

### Key Design Decisions
- Version bump: 1.0.0 → 1.1.0 (MINOR: new feature guidance sections)
- Task extraction output uses structured JSON with description, deadline, priority_indicator, requires_action
- Deadline values preserved as original expressions ("Tonight") — never converted to datetime
- Zero tolerance for deadline hallucination (0% target)
- Single LLM call for priority + tasks + deadlines (no extra latency)
- Graceful fallback: empty tasks/deadlines on failure, no user-facing errors

## Outcome

- Impact: Governance document for Days 11-12 features
- Tests: None required (constitution only)
- Files: .specify/memory/constitution.md, CONSTITUTION.md
- Next prompts: /sp.spec or /sp.plan for task extraction and deadline detection features
- Reflection: Constitution extends existing principles (III, AI is Assistive) with concrete rules

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results: N/A
- Prompt variant: N/A
- Next experiment: N/A
