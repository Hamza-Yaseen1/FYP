---
id: phr-plan-001
title: Plan AI Intelligence Layer
stage: plan
date: 2026-08-19
surface: cli
model: big-pickle
feature: 1-baseline-spec
branch: 1-baseline-spec
user: user
command: plan
labels: [plan, ai, fyp]
links:
  spec: specs/1-baseline-spec/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - PLAN.md
  - specs/1-baseline-spec/research.md
  - specs/1-baseline-spec/data-model.md
  - specs/1-baseline-spec/contracts/messages-api.md
  - specs/1-baseline-spec/quickstart.md
tests: []
---

## Prompt

Create a practical technical implementation plan (PLAN.md) for my Final Year Project "Communication AI", based on the CONSTITUTION.md and SPEC.md.

### Current Status
- Week 1 is completed (Next.js frontend, FastAPI backend, MongoDB, fake WhatsApp webhook, messages appearing on dashboard)
- Now starting Week 2: AI Intelligence

### Tech Stack
- Frontend: Next.js + TypeScript + Tailwind + shadcn/ui
- Backend: FastAPI + MongoDB
- AI: Python + LLM API (OpenAI / Groq / Gemini – keep it flexible)

### Please create a clear implementation plan that covers:

1. Overall Architecture
2. AI Module Design
   - AI Analyzer
   - Priority Agent
   - Summary Agent
   - Task Extraction
   - Deadline Detection
   - Recommended Action
   - How they will work together (simple orchestrator)
3. Database changes needed for AI results
4. API endpoints required for AI features
5. Frontend changes needed to show AI results (priority, summary, tasks, etc.)
6. Week-by-week / Phase-by-phase implementation order
7. Risk areas and how to handle them (e.g. AI failure, hallucinated deadlines)
8. Testing approach for AI features

Follow the principles in CONSTITUTION.md (Simplicity First, Vertical Slices, AI is Assistive not Magical).
Keep the plan realistic for a university FYP.
Save it as PLAN.md in the root of the project.

## Response snapshot

Created comprehensive implementation plan with 5 supporting documents:

1. **PLAN.md** - Main implementation plan with:
   - Technical context (all fields resolved)
   - Constitution check (all 7 principles PASS)
   - Project structure (backend + frontend changes)
   - Implementation roadmap (Week 2-3, 6 phases)
   - Risk areas with mitigations
   - Testing approach

2. **research.md** - Phase 0 research covering:
   - LLM provider selection (OpenAI/Groq/Gemini)
   - Prompt engineering strategy
   - AI failure handling
   - Sync vs async analysis decision
   - Task model design
   - Confidence score thresholds

3. **data-model.md** - Phase 1 data model:
   - Updated Message entity with ai_analysis
   - New Task entity
   - State transitions
   - Indexes
   - Query patterns

4. **contracts/messages-api.md** - API contracts:
   - POST /messages (with AI analysis)
   - GET /messages (filtered)
   - GET /tasks, PUT /tasks/{id}, DELETE /tasks/{id}
   - Updated webhooks

5. **quickstart.md** - Development setup guide:
   - Backend/frontend setup
   - Environment variables
   - Testing examples
   - Provider switching

## Outcome

- Impact: Complete technical plan ready for implementation
- Tests: None required (planning only)
- Files: PLAN.md, research.md, data-model.md, contracts/messages-api.md, quickstart.md
- Next prompts: /sp.tasks (task breakdown)
- Reflection: Plan follows constitution principles - simple, vertical slices, AI assistive

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results: N/A
- Prompt variant: N/A
- Next experiment: N/A
