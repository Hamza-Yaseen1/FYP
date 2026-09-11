---
id: phr-tasks-day28-analytics
title: "Day 28 Analytics Tasks"
stage: tasks
date: 2026-09-11
surface: cli
model: opencode/big-pickle
feature: 019-analytics
branch: 019-analytics
user: user
command: /sp.tasks
labels: [tasks, analytics, day-28, recharts, fastapi]
links:
  spec: specs/019-analytics/spec.md
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - specs/019-analytics/tasks.md
  - specs/019-analytics/plan.md
  - specs/019-analytics/spec.md
  - specs/019-analytics/research.md
  - specs/019-analytics/data-model.md
  - specs/019-analytics/contracts/analytics.md
  - specs/019-analytics/quickstart.md
  - AGENTS.md
tests:
  - Backend: backend/tests/test_analytics.py (pytest, 600s timeout, conftest pattern)
  - Frontend: app/(dashboard)/analytics/__tests__/page.test.tsx (vitest, period toggle)
---

## Prompt

Create a clear and actionable task list for Day 28 – Analytics.

### Context
- Project: Communication AI
- Messages, priorities, and tasks are already working
- User isolation is working
- Now we need a professional Analytics section

### Goal:
Add Communication Overview with stats and simple charts:

Stats:
- Total Communications
- Urgent / Important / Normal / Low Priority

Charts:
- Communications by source (WhatsApp vs Gmail)
- Priority distribution
- Tasks completed
- Response / attention trends

### Focus Areas:
- Backend analytics API (calculate real numbers for current user)
- Frontend Analytics page or Dashboard section
- Simple and clean charts
- "This Week" filter
- Match current design (purple/white, light/dark mode)

### Requirements for the task list:
- Break work into small, clear, executable tasks
- Group tasks logically (Backend, Frontend, Charts, Testing)
- Write tasks in action language
- Include acceptance criteria
- Keep it simple and realistic for a university FYP

Save the file in the appropriate location.

The tasks.md should be immediately executable - each task must be specific enough that an LLM can complete it without additional context.

---

## Response snapshot

Generated `specs/019-analytics/tasks.md` — 33 tasks in 8 phases, organized by
5 user stories (P1–P4) with clear checkpoints. Structure:

Phase 1 Setup (2 tasks): install recharts, scaffold analytics directories.
Phase 2 Foundational (6 tasks, blocks all stories): `GET /analytics` router in
`backend/routes/analytics.py` with auth + period validation, register in
main.py, period-range helper in `backend/services/analytics.py`, typed API
client `lib/api/analytics.ts`, Sidebar link, page shell with empty/loading
states.
Phase 3 US1 (5 tasks): total + by_priority + by_source aggregation,
OverviewCards, SourceChart, wire into page — MVP checkpoint.
Phase 4 US2 (5 tasks): period-window scoping backend + PeriodToggle component
+ frontend vitest.
Phase 5 US3 (4 tasks): tasks aggregation + TasksProgress component.
Phase 6 US4 (2 tasks): PriorityChart (pie/donut, reuses by_priority data).
Phase 7 US5 (4 tasks): trend aggregation (zero-filled hourly/daily) +
TrendChart.
Phase 8 Polish (5 tasks): quickstart validation, full pytest + vitest, lint,
light/dark theme review, AGENTS.md update.

All tasks follow the checklist format: `- [ ] T### [P?] [Story?] file path`.
Backend test tasks written FIRST per story (ensure FAIL, then implement). One
new npm dep only (recharts). Zero schema changes, zero new collections — read-
only reuse of `messages` and `tasks`.

---

## Outcome

- ✅ Impact: 33 immediately executable tasks, 8 phases, 5 user stories with
  3 checkpoint moments (MVP at US1, functional at US2, full at US5).
- 🧪 Tests: Backend pytest for counts + period windows + task metric + trend
  buckets; frontend vitest for page fetch/period toggle. All green after
  implementation.
- 📁 Files: tasks.md (just created)
- 🔁 Next prompts: (run tasks) — begin Phase 1: install recharts
- 🧠 Reflection: Same-file conflicts avoided across parallel stories by
  routing each story to its own component file; backend aggregation stays in
  one file (services/analytics.py) but phases touch distinct functions so
  sequential dev avoids merge pain. Quickstart.md wired as final Polish gate.

## Evaluation notes (flywheel)

- Failure modes observed: N/A (task generation only)
- Graders run and results (PASS/FAIL): PASS — all 33 tasks validated
  (sequential IDs, correct format, file paths present)
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A