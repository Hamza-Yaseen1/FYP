# Implementation Plan: Analytics — Communication Overview

**Branch**: `019-analytics` | **Date**: 2026-09-11 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/019-analytics/spec.md`

## Summary

Add a read-only Analytics page (`/analytics`) that shows the logged-in user a
Communication Overview for Today / This Week / This Month: summary cards
(Total, Urgent, Important, Normal, Low, Pending) plus four charts
(Communications by Source, Priority Distribution, Tasks Completed, Response
Trend). All numbers are computed server-side with MongoDB aggregation filtered
by `user_id` — the frontend only renders pre-aggregated JSON. Two-user
isolation and real-data accuracy are the hard gates.

## Technical Context

**Language/Version**: Python 3.13 (FastAPI backend), TypeScript 5.x (Next.js 16.3.1, React 19)  
**Primary Dependencies**: motor (MongoDB aggregation), recharts (NEW — charts), existing shadcn/ui + Tailwind v4 + lucide-react  
**Storage**: MongoDB `messages` and `tasks` collections, **read-only reuse** — no schema or migration changes  
**Testing**: pytest (backend, ~197 existing tests), vitest + @testing-library/react (frontend)  
**Target Platform**: Web (localhost dev: backend :8000, frontend :3000)  
**Project Type**: Web application — monorepo with `backend/` (FastAPI) + frontend at repo root (Next.js App Router)  
**Performance Goals**: Analytics page renders accurate numbers within 2s for up to 10,000 messages; `GET /analytics` responds under 500ms  
**Constraints**: `user_id` filter is the FIRST condition in every aggregation; zero cross-user aggregation; numbers must exactly match a direct DB count; no permanent analytics collection (compute on demand)  
**Scale/Scope**: Single user per view (FYP demo); up to ~10k messages/user

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Verdict |
|---|---|---|
| I. Simplicity First | One new frontend dependency (recharts); single analytics endpoint; no analytics store | ✅ PASS |
| II. Vertical Slices | Backend aggregation endpoint + frontend page shipped as one slice | ✅ PASS |
| III. AI is Assistive, Not Magical | No AI-generated narrative insights; charts render from stored `ai_analysis.priority` | ✅ PASS |
| IV. User Control | Read-only view; no auto-actions, no data mutation | ✅ PASS |
| V. Security and Privacy | Per-user aggregation only; counts exposed, message content is not | ✅ PASS |
| VII. Progressive Enhancement | Analytics loads from stored analysis even when AI service is down | ✅ PASS |
| Day 18 User Isolation | Every aggregation matches `{user_id, ...}` first; cross-user stats forbidden | ✅ PASS |
| Day 28 Analytics (constitution) | Real data, server-side computation, no frontend computation of counts, no stale cache | ✅ PASS |

No violations — Complexity Tracking is left empty.

## Project Structure

### Documentation (this feature)

```text
specs/019-analytics/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (chart lib + aggregation approach)
├── data-model.md        # Phase 1 output (read-only views)
├── quickstart.md        # Phase 1 output (manual validation steps)
├── contracts/           # Phase 1 output (API contract)
│   └── analytics.md
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
backend/
├── routes/
│   └── analytics.py          # NEW — GET /analytics (aggregation endpoint)
├── tests/
│   └── test_analytics.py     # NEW — pytest suite
app/(dashboard)/
├── analytics/
│   └── page.tsx              # NEW — Analytics page (client component)
components/
├── analytics/
│   ├── OverviewCards.tsx     # NEW — summary stat cards
│   ├── SourceChart.tsx       # NEW — bySource bar chart
│   ├── PriorityChart.tsx     # NEW — byPriority pie/donut
│   ├── TasksProgress.tsx     # NEW — completed vs total
│   └── TrendChart.tsx        # NEW — volume over time line chart
lib/
└── api/
    └── analytics.ts          # NEW — typed API client
```

**Structure Decision**: Conventional web-app structure already in use — new route
in `backend/routes/`, new page under the `(dashboard)` App Router group, new
components in `components/analytics/`, new API client in `lib/api/analytics.ts`.
No new projects, workspaces, or packages.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations — table intentionally empty.

## Research Decisions

See [research.md](./research.md) for full rationale:

1. **Chart library: recharts** — declarative, React-native, covers bar/pie/line,
   simplest option; not currently installed.
2. **Aggregation: single `GET /analytics?period=...`** MongoDB aggregation
   pipeline (`$match` on `user_id` first, then `$group`/`$count`) — no per-metric
   round-trips.
3. **Pending bucket**: uses `ai_analysis.priority` values `urgent/important/
   normal/low`; anything else (including `pending`) buckets to "Pending".
4. **Task metric**: tasks joined to their message's `received_at` for period
   filtering; completed = `status == "completed"`.
5. **Trend granularity**: daily buckets for week/month, hourly for today.

## Implementation Steps (in order)

1. **Backend endpoint** — create `backend/routes/analytics.py` with
   `GET /analytics?period=week|month|day` guarded by `get_current_user`
   (dependencies.py). Register router in `main.py`.
2. **Aggregation service** — compute five buckets in `backend/services/
   analytics.py`: `total`, `by_priority`, `by_source`, `tasks`, `trends` from
   `messages_collection` + `tasks_collection` with `user_id` as first `$match`.
3. **Backend tests** — `backend/tests/test_analytics.py`: accuracy, period
   filtering, user isolation (two-user), pending bucket, empty data, 401.
4. **Install recharts** — `npm install recharts`.
5. **API client** — `lib/api/analytics.ts` typed client mirroring the contract.
6. **Analytics page** — `app/(dashboard)/analytics/page.tsx` with period toggle
   (Today / This Week / This Month), fetch, loading skeleton, empty state.
7. **Chart components** — OverviewCards, SourceChart, PriorityChart,
   TasksProgress, TrendChart in `components/analytics/`.
8. **Navigation** — add Analytics link to `components/Sidebar.tsx` navItems.
9. **Frontend tests** — vitest coverage for the page (fetch + render), chart
   empty states.
10. **Validation** — run full backend suite + frontend tests + quickstart.md
    manual checks.

## Testing Plan

### Backend (pytest — `backend/tests/test_analytics.py`)

- **Accuracy**: seed known messages → response counts equal direct DB cursor
  counts for the same `{user_id, received_at range}` filter.
- **Period filtering**: messages with known `received_at` today/week/month land
  only in the correct period result.
- **User isolation**: user A and user B see only their own totals/charts.
- **Pending bucket**: priorities `urgent/important/normal/low` map to their
  buckets; `pending`/missing analysis goes to `pending`.
- **Tasks metric**: completed vs total counts reflect `tasks` statuses scoped to
  the period.
- **Auth**: no cookie → 401.
- **Trends**: daily buckets contain correct counts; zero-filled days not skipped
  (server returns `{date, count}` for every bucket in range).

### Frontend (vitest — `app/(dashboard)/analytics/__tests__/`)

- Page fetches `/analytics` and renders cards + charts (mocked fetch).
- Period toggle triggers refetch with the right `period` param.
- Empty state renders "No data yet" when `total === 0`.

## Definition of Done

1. `GET /analytics?period=...` returns the contract shape; unauthenticated → 401.
2. Every count matches a direct DB count for the same filters (SC-002) — proven
   by tests.
3. Two-user isolation test passes (SC-005) — no cross-user metrics possible.
4. Analytics page loads in < 2s for 10k messages (SC-001); toggle updates in
   < 1s (SC-004).
5. Page renders in light and dark mode with purple/white theme (SC-007, FR-012,
   FR-013).
6. Empty states for no-messages / no-tasks / single-source / all-pending
   (FR-011, edge cases).
7. Charts readable at 1280px and 768px without horizontal scroll or overlap
   (SC-003).
8. No schema changes; `messages`/`tasks` collections untouched (read-only).
9. Full backend suite (~197 existing + new) passes; frontend lint + tests pass.