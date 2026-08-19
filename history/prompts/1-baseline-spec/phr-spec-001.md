---
id: phr-spec-001
title: Create Communication AI Baseline Spec
stage: spec
date: 2026-08-19
surface: cli
model: big-pickle
feature: 1-baseline-spec
branch: 1-baseline-spec
user: user
command: spec
labels: [spec, baseline, fyp]
links:
  spec: specs/1-baseline-spec/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/1-baseline-spec/spec.md
  - specs/1-baseline-spec/checklists/requirements.md
  - SPEC.md
tests: []
---

## Prompt

Create a clear and practical baseline specification (SPEC.md) for my Final Year Project called "Communication AI".

### Project Overview
An Agentic AI system that helps users manage communication overload. It receives messages from different sources (starting with simulated WhatsApp, later real WhatsApp and Gmail), prioritizes them, extracts tasks and deadlines, generates summaries and recommended actions, and shows users only what needs their attention through a clean dashboard.

### Current Status (Week 1 Completed)
- Next.js frontend with dashboard, sidebar, and basic pages
- FastAPI backend
- MongoDB connected
- Fake WhatsApp webhook working
- Messages can be simulated and appear on the dashboard

### What we need to specify now
Please create a complete but practical specification that covers:

1. Product Vision & Goals
2. Core Features (prioritized)
   - Message Ingestion (simulated + real)
   - AI Analysis (Priority, Summary, Task Extraction, Deadline Detection, Recommended Action)
   - Dashboard & Attention System
   - Task Management
   - User Authentication & Isolation
   - Future Integrations (WhatsApp Business, Gmail)
3. User Stories (clear and realistic)
4. Priority Levels Definition (Urgent, Important, Normal, Low)
5. AI Behavior Rules (what the AI should and should not do)
6. Data Models (Messages, Tasks, Users, etc.)
7. Non-Functional Requirements (security, performance, privacy)
8. Out of Scope (for this FYP)

Follow the principles defined in CONSTITUTION.md.
Keep the specification realistic for a university Final Year Project (not over-engineered).
Save it as SPEC.md in the root of the project.

## Response snapshot

Created three files:
1. `specs/1-baseline-spec/spec.md` - Full feature specification following template
2. `specs/1-baseline-spec/checklists/requirements.md` - Quality validation checklist
3. `SPEC.md` - Root copy as requested

Specification includes:
- 8 user stories (P1-P4 priority levels)
- 10 functional requirements
- 8 success criteria
- 4 priority level definitions
- AI behavior rules (MUST do, MUST NOT do, fallback)
- 4 key entities (Message, Task, User, Channel)
- Non-functional requirements (security, performance, privacy, reliability)
- Clear out-of-scope section
- Assumptions documented

## Outcome

- Impact: Established baseline specification for entire FYP
- Tests: None required (specification only)
- Files: specs/1-baseline-spec/spec.md, specs/1-baseline-spec/checklists/requirements.md, SPEC.md
- Next prompts: plan, tasks (for feature implementation)
- Reflection: Spec follows constitution principles - simple, practical, FYP-appropriate

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results: N/A
- Prompt variant: N/A
- Next experiment: N/A
