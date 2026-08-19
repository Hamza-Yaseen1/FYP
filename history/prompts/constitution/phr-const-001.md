---
id: phr-const-001
title: Create Communication AI Constitution
stage: constitution
date: 2026-08-19
surface: cli
model: big-pickle
feature: communication-ai
branch: main
user: user
command: constitution
labels: [constitution, setup, fyp]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/memory/constitution.md
  - CONSTITUTION.md
tests: []
---

## Prompt

Create a clear and practical CONSTITUTION.md for my Final Year Project called "Communication AI".

Project summary:
An Agentic AI system that helps users manage communication overload. It receives messages (WhatsApp, Gmail, etc.), prioritizes them, extracts tasks and deadlines, and shows users only what needs their attention through a clean dashboard.

Tech stack:
- Frontend: Next.js + TypeScript + Tailwind + shadcn/ui
- Backend: FastAPI + MongoDB
- AI: Python + LLM API

Please create a professional but practical constitution that includes:

1. Core Mission
2. Development Principles (Simplicity First, Vertical Slices, AI is Assistive not Magical, User Control, Security & Privacy, Clean Code, Progressive Enhancement)
3. Technical Principles
4. Quality Bar
5. Decision Guidelines (when in doubt, what should we choose)

Keep the language clear, concise, and suitable for a university Final Year Project.
Save it as CONSTITUTION.md in the root of the project.

## Response snapshot

Created two files:
1. `.specify/memory/constitution.md` - Filled template with all placeholders replaced
2. `CONSTITUTION.md` - Clean user-facing version in project root

Constitution includes:
- Core Mission statement
- 7 Development Principles with rationales
- Technical Principles (Frontend, Backend, AI Layer, Infrastructure)
- Quality Bar (Definition of Done, Testing, Performance)
- Decision Guidelines (5 tiebreakers + technology/AI decisions)
- Governance section with amendment process and compliance checklist

## Outcome

- Impact: Established foundational governance document for FYP
- Tests: None required (documentation only)
- Files: .specify/memory/constitution.md, CONSTITUTION.md
- Next prompts: spec, plan, tasks (for feature implementation)
- Reflection: Constitution provides clear guardrails for FYP development

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results: N/A
- Prompt variant: N/A
- Next experiment: N/A
