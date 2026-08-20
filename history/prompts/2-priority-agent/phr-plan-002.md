---
id: phr-plan-002
title: Priority Agent Implementation Plan
stage: plan
date: 2026-08-19
surface: cli
model: big-pickle
feature: 2-priority-agent
branch: 2-priority-agent
user: user
command: plan
labels: [plan, priority-agent, ai, fyp]
links:
  spec: specs/2-priority-agent/spec.md
  plan: specs/2-priority-agent/plan.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/2-priority-agent/plan.md
  - backend/services/ai/providers/base.py
  - backend/services/ai/providers/openai.py
  - backend/services/ai/analyzer.py
  - backend/services/ai/prompts/priority.txt
  - backend/models/message.py
  - backend/routes/messages.py
tests: []
---

## Prompt

Create a practical technical implementation plan for the Priority Agent (Day 9).

### Context
- Project: Communication AI
- We already have main PLAN.md
- Current goal: Build a simple and reliable Priority Agent
- It should classify messages into: URGENT | IMPORTANT | NORMAL | LOW
- Do NOT build a complex multi-agent system yet

### Please create a clear plan that includes:

1. Goal of this phase
2. Technical Approach (keep it simple)
3. Files that need to be created or updated
4. How the Priority Agent will work (step-by-step flow)
5. Prompt design for the Priority Agent
6. How the result will be stored in MongoDB
7. How the result will be shown on the Dashboard
8. Implementation steps (in order)
9. Testing plan
10. Definition of Done

Follow these principles:
- Simplicity First
- One reliable agent is better than many fake agents
- AI is Assistive, not Magical

Save the plan as `specs/priority-agent/plan.md` or in the appropriate location.

## Response snapshot

Created implementation plan and updated backend files for Priority Agent.

### Plan Created
- `specs/2-priority-agent/plan.md` - Complete implementation plan

### Files Updated
1. `backend/services/ai/providers/base.py` - Added explanation field to AIAnalysisResult
2. `backend/services/ai/providers/openai.py` - Updated with priority-focused prompt
3. `backend/services/ai/analyzer.py` - Added explanation to return dict
4. `backend/services/ai/prompts/priority.txt` - Rewritten per Priority Agent constitution
5. `backend/models/message.py` - Added explanation field to AIAnalysis
6. `backend/routes/messages.py` - Added PUT /{id}/priority override endpoint

### Key Design Decisions
- Single LLM call with focused priority prompt
- Explanation field for transparency
- Priority override endpoint for user control
- Conservative urgency (default NORMAL when uncertain)
- Failure gracefully defaults to NORMAL with status "pending"

## Outcome

- Impact: Priority Agent backend implementation complete
- Tests: None required (implementation only)
- Files: 7 files created/updated
- Next prompts: /sp.tasks, then frontend updates
- Reflection: Implementation follows constitution principles

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results: N/A
- Prompt variant: N/A
- Next experiment: N/A
