---
id: phr-spec-day28-analytics
title: "Day 28 Analytics Spec"
stage: spec
date: 2026-09-11
surface: cli
model: opencode/big-pickle
feature: 019-analytics
branch: 019-analytics
user: user
command: /sp.specify
labels: [spec, analytics, statistics, charts, day-28]
links:
  spec: specs/019-analytics/spec.md
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - specs/019-analytics/spec.md
  - specs/019-analytics/checklists/requirements.md
tests:
  - All 16 acceptance scenarios are independently testable
  - Checklist: 16/16 items pass
---

## Prompt

Create a clear and focused specification for Day 28 – Analytics.

### Context
- Project: Communication AI
- Messages from WhatsApp and Gmail are already working
- AI priority, tasks, and dashboard are working
- Now we need a professional Analytics section

### Goal:
Add a Communication Overview with clear stats and simple charts.

Example:
Communication Overview – This Week

Total Communications       247
Urgent                      12
Important                   38
Normal                     151
Low Priority                46

Charts needed:
- Communications by source (WhatsApp vs Gmail)
- Priority distribution
- Tasks completed
- Response / attention trends

### Requirements:
- Show data only for the logged-in user
- Support "This Week" view (can also prepare for Today / This Month if easy)
- Numbers must come from real database data
- Keep charts simple and clean
- Design must match the current purple/white theme
- Works in both light and dark mode

### Please include in the specification:
1. Feature Overview
2. User Stories
3. Metrics to display
4. Chart requirements
5. Data calculation rules
6. Acceptance Criteria
7. Edge cases (no data, etc.)

Keep it practical and professional for a university FYP.

## Response snapshot

Created branch `019-analytics` and wrote `specs/019-analytics/spec.md` with
5 user stories (P1: Communication Overview stats + source chart; P2: Today /
This Week / This Month period toggle; P3: Tasks Completed statistic and
Priority Distribution chart; P4: Response / Attention trend chart), 16
acceptance scenarios, 15 functional requirements, 8 edge cases, key entities,
and 6 measurable success criteria plus assumptions. Quality checklist:
16/16 items pass. Spec is aligned with the Day 28 Analytics constitution
section: user isolation, server-side aggregation, no frontend computation,
real data only, pending bucket for unanalyzed messages.

## Outcome

- ✅ Impact: Complete feature specification for Day 28 Analytics with 5
  prioritized user stories (MVP = overview stats + source chart), 16
  acceptance scenarios, 15 functional requirements, and 8 edge cases.
- 🧪 Tests: Checklist 16/16 pass. All acceptance scenarios independently
  testable.
- 📁 Files: specs/019-analytics/spec.md,
  specs/019-analytics/checklists/requirements.md
- 🔁 Next prompts: /sp.plan (implementation planning)
- 🧠 Reflection: Spec prioritizes the vertical slice correctly — the overview
  stats + source chart form the P1 MVP, with period toggle and additional
  charts added incrementally. All data rules (real database data, user-only,
  server-side aggregation) trace directly to the Day 28 constitution.

## Evaluation notes (flywheel)

- Failure modes observed: Initial validation caught just one issue — chart
  library names (recharts/Chart.js) leaked into the Assumptions section; removed
  to keep the spec technology-agnostic.
- Graders run and results (PASS/FAIL): PASS — all checklist items pass,
  no NEEDS CLARIFICATION markers, requirements testable and unambiguous
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A