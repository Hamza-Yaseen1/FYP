---
id: phr-plan-day28-analytics
title: "Day 28 Analytics Plan"
stage: plan
date: 2026-09-11
surface: cli
model: opencode/big-pickle
feature: 019-analytics
branch: 019-analytics
user: user
command: /sp.plan
labels: [plan, analytics, backend, recharts, day-28]
links:
  spec: specs/019-analytics/spec.md
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - specs/019-analytics/plan.md
  - specs/019-analytics/research.md
  - specs/019-analytics/data-model.md
  - specs/019-analytics/contracts/analytics.md
  - specs/019-analytics/quickstart.md
  - AGENTS.md
tests:
  - Backend: pytest suite (new test_analytics.py + ~197 existing)
  - Frontend: vitest for analytics page fetch/render/period-toggle
---

## Prompt

Create a practical technical implementation plan for Day 28 – Analytics.

### Context
- Project: Communication AI
- Frontend: Next.js + TypeScript + Tailwind + shadcn/ui
- Backend: FastAPI + MongoDB
- Messages, priorities, and tasks are already working
- User isolation is working

### Goal:
Add a professional Analytics section with:

Communication Overview – This Week
- Total Communications
- Urgent
- Important
- Normal
- Low Priority

Charts:
- Communications by source (WhatsApp vs Gmail)
- Priority distribution
- Tasks completed
- Response / attention trends

### Please include in the plan:
1. Goal of this phase
2. Technical approach
3. Backend API endpoints needed for analytics
4. How each metric will be calculated
5. Frontend components and chart library recommendation (keep it simple)
6. Implementation steps in order
7. Testing plan
8. Definition of Done

Keep it simple, clean, and realistic for a university FYP.
Prefer easy-to-use chart solutions.

## Response snapshot

Created `specs/019-analytics/plan.md` grounding every decision in the existing
codebase (FastAPI routes + `dependencies.get_current_user`, `messages`/
`tasks` collections, Next.js `(dashboard)` group, `lib/api/*` clients,
`components/`). Key decisions: single `GET /analytics?period=day|week|month`
with MongoDB aggregation ($match on `user_id` FIRST), recharts as the ONE new
frontend dependency, priority bucket mapping (urgent/important/normal/low →
pending fallback), tasks joined to parent message `received_at` for period
scoping, zero-filled trends. Constitution Check passes on all 8 gates
(Simplicity I, Slices II, Assistive III, Control IV, Security V, Progressive
Enhancement VII, Day 18 isolation, Day 28 rules) — no complexity tracking
needed. Produced research.md, data-model.md, contracts/analytics.md,
quickstart.md, and updated AGENTS.md via update-agent-context.ps1.

## Outcome

- ✅ Impact: Full implementation plan with 10 ordered steps, research
  decisions, API contract, read-only data model, testing plan, and
  Definition of Done. No constitution violations.
- 🧪 Tests: Backend pytest (new analytics suite) + frontend vitest for the
  page; quickstart.md manual validation steps.
- 📁 Files: plan.md, research.md, data-model.md, contracts/analytics.md,
  quickstart.md, AGENTS.md
- 🔁 Next prompts: /sp.tasks (task breakdown)
- 🧠 Reflection: The plan intentionally reuses existing patterns (auth
  dependency, collection names, component layout) so the feature stays a
  pure additive slice with zero schema changes. Recharts selected over
  Chart.js/custom SVG for the smallest learning curve.

## Evaluation notes (flywheel)

- Failure modes observed: None — no NEEDS CLARIFICATION left after spec stage
- Graders run and results (PASS/FAIL): PASS — 8/8 constitution gates pass,
  definitions of done map to spec success criteria
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A