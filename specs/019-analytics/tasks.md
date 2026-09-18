---

description: "Day 28 Analytics task list"
---

# Tasks: Analytics

**Input**: Design documents from `/specs/019-analytics/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/analytics.md, quickstart.md

**Tests**: Test tasks are included. Backend uses pytest (existing `backend/tests/` suite with conftest.py TestClient + fake collection pattern); frontend uses vitest (colocated `__tests__/` folders). Write test tasks FIRST, ensure they FAIL, then implement.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/routes/`, `backend/services/`, `backend/tests/`
- **Frontend**: `app/`, `components/`, `lib/` at repo root
- **Spec**: `specs/019-analytics/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] Install recharts chart library via `npm install recharts` (updates `package.json` + `package-lock.json`)
- [X] T002 Create analytics UI scaffold directories: `app/(dashboard)/analytics/`, `app/(dashboard)/analytics/__tests__/`, `components/analytics/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

> **CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Create `backend/routes/analytics.py`: APIRouter with `GET /analytics?period=week|day|month`, protected by `dependencies.get_current_user`, period validated (invalid → 400 `{"detail":"Invalid period. Must be day, week, or month."}`), unauthenticated → 401
- [X] T004 Register analytics router in `backend/main.py` via `app.include_router(analytics.router)` at the same prefix level as existing routers
- [X] T005 [P] Create `backend/services/analytics.py` with `_period_range(period) -> (from, to)` UTC helper: `day` = now−24h, `week` = now−7d, `month` = now−30d
- [X] T006 [P] Create typed client `lib/api/analytics.ts`: `AnalyticsPeriod`, `AnalyticsResponse` types + `analyticsFetch(period)` wrapper around the existing `apiFetch` in `lib/api.ts`
- [X] T007 [P] Add "Analytics" nav item to `components/Sidebar.tsx` navItems (lucide `BarChart3` icon, `href: "/analytics"`, placed after Attention and before Tasks)
- [X] T008 Create page shell `app/(dashboard)/analytics/page.tsx`: `"use client"`, page title "Communication Overview", subtitle showing the active period, `LoadingSkeleton` state while fetching, `EmptyState` ("No data yet") when `total === 0`; section host containers ready to receive story components

**Checkpoint**: Foundation ready — user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Communication Overview with Source Chart (Priority: P1) — MVP

**Goal**: See Total Communications plus Urgent / Important / Normal / Low Priority counts and a WhatsApp-vs-Gmail bar chart for the current period

**Independent Test**: Register a user, seed messages via the existing simulate webhook, open `/analytics` → the four cards + Total match the Dashboard counts and the source bars match simulated WhatsApp/Gmail messages

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Backend test for aggregation counts in `backend/tests/test_analytics.py` (fake collection per conftest pattern; asserts `total`, `by_priority` bucket mapping incl. unknown/`pending` → Pending bucket, and `by_source`; `user_id`-scoped)

### Implementation for User Story 1

- [X] T010 [P] [US1] Implement message aggregations in `backend/services/analytics.py`: `total`, `by_priority`, `by_source` MongoDB pipelines starting with `$match: { "user_id": <session uid> }`; priority buckets urgent/important/normal/low, anything else → `pending`
- [X] T011 [P] [US1] Create `components/analytics/OverviewCards.tsx`: five cards (Total, Urgent, Important, Normal, Low) using existing `Card`/shadcn components and theme-aware purple styling, primary accent on Total
- [X] T012 [P] [US1] Create `components/analytics/SourceChart.tsx`: recharts `BarChart` (Bar per source) for WhatsApp vs Gmail, colored via Tailwind theme vars so light/dark stay legible
- [X] T013 [US1] Wire `OverviewCards` and `SourceChart` into `app/(dashboard)/analytics/page.tsx`: fetch via `analyticsFetch("week")` in an effect, render cards from `by_priority`/`total` and chart from `by_source`, keep empty state for zero totals

**Checkpoint**: At this point, User Story 1 should be fully functional and independently testable (MVP demo)

---

## Phase 4: User Story 2 - Period Toggle Today / This Week / This Month (Priority: P2)

**Goal**: Switch the dashboard between Today, This Week (default), and This Month; every stat and chart re-queries for the selected window

**Independent Test**: Seed messages in different windows (today / this week / this month); each toggle updates Total + all cards + charts without a page reload

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T014 [P] [US2] Backend test for period windows in `backend/tests/test_analytics.py`: `day`/`week`/`month` return correct windowed counts; invalid period → 400; messages outside window excluded

### Implementation for User Story 2

- [X] T015 [P] [US2] Scope all analytics aggregations to the period window in `backend/services/analytics.py`: add `received_at` range from `_period_range` into each pipeline's `$match`
- [X] T016 [P] [US2] Create `components/analytics/PeriodToggle.tsx`: segmented control (Today / This Week / This Month) matching the purple/white design, calls `onChange(period)`
- [X] T017 [US2] Wire `PeriodToggle` state into `app/(dashboard)/analytics/page.tsx`: `useState<AnalyticsPeriod>("week")`, refetch on change, subtitle reflects active period
- [X] T018 [P] [US2] Frontend vitest in `app/(dashboard)/analytics/__tests__/page.test.tsx`: page fetches with default `week`, toggle triggers refetch with the new period, loading/empty states render

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Tasks Completed Statistic (Priority: P3)

**Goal**: Show extracted vs completed tasks for the active period

**Independent Test**: Complete a task on `/tasks`; open `/analytics` → `TasksProgress` reflects completed count increasing while total stays constant

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T019 [P] [US3] Backend test for tasks metric in `backend/tests/test_analytics.py`: `tasks.total` (period-scoped via parent message `received_at` resolved from `source_message_id`) and `tasks.completed` (`status == "completed"`)

### Implementation for User Story 3

- [X] T020 [P] [US3] Implement tasks aggregation in `backend/services/analytics.py`: load user's tasks, resolve parent message `received_at` for period scoping, count completed; return `{total, completed}`
- [X] T021 [P] [US3] Create `components/analytics/TasksProgress.tsx`: "Tasks Completed" card using a recharts `PieChart` donut (or Progress bar) showing `completed` / `total` with the purple accent
- [X] T022 [US3] Add `TasksProgress` to `app/(dashboard)/analytics/page.tsx` grid alongside OverviewCards

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Priority Distribution Chart (Priority: P3)

**Goal**: Visualize message volume across priority buckets as a chart

**Independent Test**: Seed messages with known priorities → donut segments match the Overview card counts exactly (including the Pending slice)

### Implementation for User Story 4

- [X] T023 [P] [US4] Create `components/analytics/PriorityChart.tsx`: recharts `PieChart`/`DonutChart` of `by_priority` (urgent/important/normal/low/pending) with theme-aware colors and legend
- [X] T024 [US4] Add `PriorityChart` to `app/(dashboard)/analytics/page.tsx`, reusing the `by_priority` data already fetched (no new endpoint)

**Checkpoint**: At this point, User Story 4 should be fully functional and testable independently

---

## Phase 7: User Story 5 - Response / Attention Trend Chart (Priority: P4)

**Goal**: Line chart of message volume over time (hourly today, daily week/month) to see attention trends

**Independent Test**: Seed messages spread across hours/days → the trend chart shows zero-filled buckets with no skipped gaps

### Tests for User Story 5

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T025 [P] [US5] Backend test for trend buckets in `backend/tests/test_analytics.py`: hourly buckets for `day`, daily for `week`/`month`, zero-filled range (no skipped buckets)

### Implementation for User Story 5

- [X] T026 [P] [US5] Implement trend aggregation in `backend/services/analytics.py`: `$group` messages by day/hour bucket then zero-fill the full `[from, to]` range in Python
- [X] T027 [P] [US5] Create `components/analytics/TrendChart.tsx`: recharts `AreaChart` (or `LineChart`) keyed on `trends[].date` → `count`
- [X] T028 [US5] Add `TrendChart` to `app/(dashboard)/analytics/page.tsx`

**Checkpoint**: All user stories functional; full page working end-to-end

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T029 [P] Run the manual validation in `specs/019-analytics/quickstart.md` (endpoint smoke tests, UI checks, isolation check) and fix any failures
- [X] T030 [P] Run the full backend pytest suite (`backend/tests/`, 200s+ timeout) and the frontend vitest suite — all green, no regressions in Dashboard/Inbox/Tasks/Connections
- [X] T031 Run lint + typecheck (`npm run lint`, `npx tsc --noEmit`) and fix any issues across new files
- [X] T032 Verify light/dark mode + responsive layout (desktop/tablet) across all new analytics components; chart colors must come from theme variables
- [X] T033 [P] Update `AGENTS.md` manual additions with analytics runtime notes (endpoint shape, priority bucket rule, trend granularity)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3 → P4)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) — Integrates with US1 page but uses its own component files (`PeriodToggle.tsx`, test file); independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) — Adds `tasks` key to response; independently testable
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) — Reuses US1's `by_priority` response data (dependency is data-only, not file-level)
- **User Story 5 (P4)**: Can start after Foundational (Phase 2) — Adds `trends` key to response; independently testable

### Within Each User Story

- Tests (where included) MUST be written and FAIL before implementation
- Backend aggregation before frontend component
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1–US5 can start in parallel (if team capacity allows): US1, US3, US5 write to distinct parts of `backend/services/analytics.py`/`backend/tests/test_analytics.py` (coordinate to avoid same-function conflicts), while US1/US2/US3/US4/US5 frontend components are separate files
- All tests for a user story marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch the test and all four implementation files together:
Task: "Backend test for aggregation counts in backend/tests/test_analytics.py"
Task: "Implement message aggregations in backend/services/analytics.py"
Task: "Create components/analytics/OverviewCards.tsx"
Task: "Create components/analytics/SourceChart.tsx"
# Then wire them together:
Task: "Wire OverviewCards and SourceChart into app/(dashboard)/analytics/page.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1 (Overview cards + source chart, This Week default)
4. **STOP and VALIDATE**: Test User Story 1 independently (T009 green; cards/chart match Dashboard counts)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 (period toggle) → Test independently → Deploy/Demo
4. Add User Story 3 (tasks), 4 (priority chart), 5 (trend) → Test each independently → Deploy/Demo
5. Final Polish phase (quickstart validation, full suite, lint/typecheck, theming)

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (backend pipeline + cards + source chart)
   - Developer B: User Story 2 (period toggle + window tests)
   - Developer C: User Story 3 (tasks metric) then User Story 5 (trend)
3. Stories complete and integrate independently; agree on merge order for `backend/services/analytics.py`

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence