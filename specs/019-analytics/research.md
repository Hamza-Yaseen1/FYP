# Research — Analytics (Day 28)

**Date**: 2026-09-11 | **Branch**: 019-analytics

## 1. Charting library

- **Decision**: Use **recharts** for all four charts.
- **Rationale**: recharts is the de-facto declarative charting library for React
  (bar, pie/donut, and line chart components map 1:1 to our needs). It renders
  client-side as pure SVG, is themeable via CSS variables (good for the
  purple/white light/dark design), and has the smallest learning curve of the
  viable options. Not currently installed → one new dependency only.
- **Alternatives considered**:
  - **Chart.js (react-chartjs-2)**: powerful, but canvas-based and requires
    manual responsive/theme wiring; more code for the same result.
  - **Custom SVG charts**: zero dependencies but significant hand-rolled work
    (axes, tooltips, empty states) — violates Simplicity First.
  - **Nivo/Victory**: heavier, more opinionated; overkill for 4 simple charts.

## 2. Metric computation approach

- **Decision**: One backend endpoint `GET /analytics?period=...` using a single
  MongoDB aggregation pipeline per data family (`messages` → totals/priority/
  source/trends; `tasks` → completion), all `$match`-filtered by `user_id`
  first.
- **Rationale**: Matches the Day 28 constitution rules — numbers must come from
  real stored data, computed server-side, never cached beyond a session. A
  single endpoint keeps the frontend thin and keeps isolation in one place.
- **Alternatives considered**:
  - **Multiple endpoints per metric**: more round-trips, more surface area for
    isolation bugs.
  - **Frontend computation from `GET /messages`**: explicitly forbidden by the
    constitution (leaks data + performance at scale).
  - **Denormalized analytics store / scheduled aggregation**: adds drift and
    complexity; rejected — FYP scale makes on-demand aggregation trivial.

## 3. Priority classification for the "Pending" bucket

- **Decision**: Bucket by the stored `ai_analysis.priority` label. Recognized
  labels map to their group: `urgent`, `important`, `normal`, `low`. Any other
  value (including `pending`) — or a missing/absent `ai_analysis` — maps to a
  single "Pending" bucket.
- **Rationale**: The AI pipeline (Day 24 Orchestrator) already stamps a priority
  on every analyzed message; parity with the Dashboard's four-group + pending
  tail (Day 27) keeps the product consistent.
- **Alternatives considered**: excluding pending entirely (loses visibility of
  unanalyzed volume) or guessing a priority for pending messages (fabrication —
  forbidden).

## 4. Task completion metric

- **Decision**: Total extracted tasks = documents in `tasks` for the period;
  completed = those with `status == "completed"`. Period comes from the linked
  message's `received_at`.
- **Rationale**: Tasks store `source_message_id`; `received_at` lives on the
  parent message. Joining via `$lookup` (or resolving ids server-side) keeps the
  "This Week" story consistent across message and task cards.
- **Alternatives considered**: using task `created_at` for period scoping
  (diverges from the message periods and is confusing) — rejected.

## 5. Trend granularity

- **Decision**: Daily buckets for `week` and `month`; hourly buckets for `day`.
  The response includes every bucket in range (zero-filled), so gaps are visible
  as zeros rather than missing points.
- **Rationale**: Spec acceptance scenario requires zero days not be skipped;
  zero-filling server-side avoids client-side date-math bugs.
- **Alternatives considered**: client-side binning (leaks raw data; more code).

## 6. Auth & isolation

- **Decision**: Reuse `dependencies.get_current_user` (JWT cookie). `user_id`
  derived from the verified session is the first `$match` in every pipeline.
- **Rationale**: Identical to all existing endpoints; the constitution mandates
  `user_id` as the first query condition and forbids cross-user aggregation.

## Resolved unknowns

No `NEEDS CLARIFICATION` remained after spec stage. All technical choices above
are grounded in the existing codebase (auth dependency, storage fields) and the
Day 28 constitution section.