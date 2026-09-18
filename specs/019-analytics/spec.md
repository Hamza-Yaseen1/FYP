# Feature Specification: Analytics — Communication Overview

**Feature Branch**: `019-analytics`  
**Created**: 2026-09-11  
**Status**: Draft  
**Input**: "Add a professional Analytics section with a Communication Overview showing real-time stats and simple charts for the logged-in user's messages."

## User Scenarios & Testing

### User Story 1 — Overview Stats with Source Chart (Priority: P1)

As a logged-in user, I want to open the Analytics page and see my Communication Overview for this week: total messages received, a breakdown by priority (Urgent / Important / Normal / Low), and a bar chart showing how many messages came from WhatsApp versus Gmail. All numbers are real, calculated from the messages in my account.

**Why this priority**: This is the core of the Analytics feature — a user who sees only this section already gets immediate, actionable insight into their communication volume and source mix. It is the minimum viable analytics view.

**Independent Test**: Register a user, send messages via simulate (WhatsApp and Gmail), open Analytics → confirm total count, priority breakdown, and source chart all match the stored message data exactly. Can be tested with zero analytics code beyond the overview stats and one chart.

**Acceptance Scenarios**:

1. **Given** I am logged in and have 247 messages this week, **When** I open the Analytics page, **Then** I see "Total Communications: 247" with correct breakdowns: Urgent 12, Important 38, Normal 151, Low 46.
2. **Given** I am logged in and have 180 WhatsApp and 67 Gmail messages, **When** I view the Analytics page, **Then** the "Communications by Source" bar chart shows WhatsApp at 180 and Gmail at 67, with bars correctly sized proportionally.
3. **Given** I have messages with pending or skipped analysis, **When** I view the priority breakdown, **Then** pending messages appear in a clearly labeled "Pending" category and are NOT merged into any priority group.
4. **Given** I am not logged in, **When** I navigate to the Analytics page, **Then** I am redirected to the login page and see no data.
5. **Given** I am logged in as User A, **When** I view Analytics, **Then** I see only my own data — none of User B's messages appear in any count or chart.

---

### User Story 2 — Period Toggle: Today / This Week / This Month (Priority: P2)

As a logged-in user, I want to toggle between "Today", "This Week", and "This Month" on the Analytics page so I can see how my communication volume changes over different time ranges. All numbers update instantly when I switch periods.

**Why this priority**: A single fixed time range (this week) is useful, but being able to zoom in (today) or zoom out (this month) multiplies the insight the user can extract without adding significant complexity.

**Independent Test**: Send messages with known timestamps (some today, some this week but not today, some this month but not this week). Toggle between periods → confirm counts and charts update to reflect only the messages within the selected period. Can be tested independently after P1.

**Acceptance Scenarios**:

1. **Given** I am on the Analytics page with "This Week" selected, **When** I click "Today", **Then** all summary cards and charts update to show only messages received today, and the page title changes to "Communication Overview — Today".
2. **Given** I am on the Analytics page with "This Week" selected, **When** I click "This Month", **Then** all summary cards and charts update to show only messages received in the last 30 days.
3. **Given** I have 12 messages today and 247 this week, **When** I switch to "Today", **Then** the total shows 12 and all charts reflect only those 12 messages.
4. **Given** I have zero messages today but 247 this week, **When** I switch to "Today", **Then** the page shows "No data yet — try a different period" or an appropriate empty state for each section, rather than broken charts or misleading zeros.

---

### User Story 3 — Tasks Completed Statistic (Priority: P3)

As a logged-in user, I want to see a "Tasks Completed" counter or progress indicator on the Analytics page so I can understand what fraction of my extracted tasks I have acted on versus what remains outstanding.

**Why this priority**: Task completion is a key signal of how effectively the user is acting on their communications. It adds a productivity dimension to the volume/priority stats already shown.

**Independent Test**: Send messages that produce extracted tasks, complete some of them via the Tasks page, open Analytics → confirm the completed and total task counts match. Can be tested after P1.

**Acceptance Scenarios**:

1. **Given** I have 42 extracted tasks and have completed 28, **When** I view the Analytics page, **Then** a "Tasks Completed" section shows "28 of 42" (or a progress bar at ~67%).
2. **Given** I have zero extracted tasks, **When** I view the Analytics page, **Then** the Tasks Completed section shows "No tasks extracted yet" rather than "0 of 0" or a misleading layout.
3. **Given** I have tasks from multiple time periods, **When** I select "Today", **Then** only tasks extracted from today's messages are counted in the Tasks Completed section for that period.

---

### User Story 4 — Priority Distribution Chart (Priority: P3)

As a logged-in user, I want a chart on the Analytics page showing the distribution of my messages across priority levels (Urgent, Important, Normal, Low, Pending) so I can visually see whether my communication load is mostly urgent, mostly routine, or mixed.

**Why this priority**: A visual priority breakdown makes patterns visible at a glance (e.g., "most of my messages are urgent this week") that a numbers-only view does not communicate as effectively. It completes the analytics picture started by the source chart.

**Independent Test**: Send messages with known priorities, open Analytics → confirm the priority distribution chart reflects the exact counts for each priority level. Can be tested independently after P1.

**Acceptance Scenarios**:

1. **Given** I have 12 urgent, 38 important, 151 normal, 46 low, and 0 pending messages, **When** I view the Analytics page, **Then** the Priority Distribution chart shows segments sized to reflect those exact proportions.
2. **Given** all my messages are marked "normal" (no urgent or important), **When** I view the chart, **Then** only the Normal segment is visible; Urgent, Important, Low, and Pending sections do not appear or show as zero-length.
3. **Given** I select "Today" and have 3 urgent and 9 normal messages, **When** I view the chart, **Then** it reflects only those 12 messages, not my full dataset.

---

### User Story 5 — Response / Attention Trend Chart (Priority: P4)

As a logged-in user, I want a line chart or bar chart on the Analytics page showing my message volume over time (daily buckets within the selected period) so I can see whether my communication load is increasing, stable, or decreasing.

**Why this priority**: Trend data helps users spot patterns (e.g., Mondays are always heavy, or my load spiked after a deadline). It is informative but not essential to the core analytics view.

**Independent Test**: Send messages with known timestamps spread across multiple days, open Analytics → confirm the trend chart shows the correct number of messages per day bucket. Can be tested independently after P1.

**Acceptance Scenarios**:

1. **Given** I have 34 messages on Sep 5, 41 on Sep 6, and 28 on Sep 7, **When** I view the Analytics page for "This Week", **Then** the trend chart shows three data points at those exact counts with correct date labels.
2. **Given** I select "Today", **When** I view the trend chart, **Then** it shows hourly buckets (or a single aggregated total) for the current day, not multi-day data.
3. **Given** I have no messages in a particular day bucket, **When** I view the trend chart, **Then** that day is shown as a zero point on the chart (not skipped), so the user can see the gap.

---

### Edge Cases

- **No messages at all (new user)**: Analytics page loads with a clear "No data yet — start by connecting WhatsApp or Gmail" message. No charts or stats are rendered. No errors.
- **No messages in the selected period**: Each section (Total, Charts) shows an appropriate empty state for the selected period (e.g., "No messages today — try This Week"). The page does not show "0" counts in a misleading way.
- **All messages have pending analysis**: The priority breakdown chart shows 100% in the "Pending" segment. Summary cards show "Pending: [N]" prominently. No other priority categories appear.
- **Only one source connected (e.g., WhatsApp only, no Gmail)**: The source chart shows a single bar for WhatsApp. No empty Gmail bar is rendered. The chart is still readable.
- **Tasks extracted but none completed**: Tasks Completed shows "0 of N" with clear messaging. No misleading progress bar at 0%.
- **Very high message volume (1,000+ messages)**: All numbers and charts render within a reasonable time (under 3 seconds on a local machine). No timeout or performance degradation visible to the user.
- **Analysis failed for some messages**: Messages whose analysis failed appear in the "Pending" bucket. They do not inflate any priority count.
- **User switches periods rapidly**: Charts and numbers update smoothly without flickering, double-loading, or showing stale data from a previous period.
- **Dark mode vs light mode**: All charts, text, and backgrounds are legible in both modes. Chart colors maintain sufficient contrast in each mode.

## Requirements

### Functional Requirements

- **FR-001**: System MUST display a dedicated Analytics page accessible via a navigation link in the sidebar or top navigation, reachable only by authenticated users.
- **FR-002**: System MUST compute all analytics metrics server-side from the logged-in user's actual stored messages, not estimated or sampled data.
- **FR-003**: System MUST show summary statistics: Total Communications, Urgent count, Important count, Normal count, and Low Priority count for the selected time period.
- **FR-004**: System MUST display a "Communications by Source" chart showing message counts grouped by source (WhatsApp, Gmail, or any future channel).
- **FR-005**: System MUST display a "Priority Distribution" chart showing message counts grouped by priority level (Urgent, Important, Normal, Low, Pending).
- **FR-006**: System MUST allow the user to toggle between "Today" (last 24 hours), "This Week" (last 7 days), and "This Month" (last 30 days); default view is "This Week".
- **FR-007**: System MUST update all summary cards and charts instantly when the user switches time period, without a full page reload.
- **FR-008**: System MUST display a "Tasks Completed" counter showing completed tasks vs total extracted tasks for the selected period.
- **FR-009**: System MUST display a "Response / Attention Trends" chart showing message volume over time in daily buckets within the selected period.
- **FR-010**: System MUST show only the authenticated user's data in every metric and chart; cross-user aggregation is forbidden.
- **FR-011**: System MUST handle empty states gracefully — when a section has no data, it shows a meaningful message rather than a broken layout or misleading zero.
- **FR-012**: System MUST work correctly in both light mode and dark mode, with chart colors maintaining sufficient contrast in each.
- **FR-013**: System MUST match the current purple/white design language across all charts, cards, and text.
- **FR-014**: System MUST NOT cache analytics data beyond the current session; numbers must reflect the current state of the database.
- **FR-015**: System MUST compute analytics server-side; the frontend MUST NOT fetch raw message lists and compute counts client-side.

### Key Entities

- **Message**: A communication received from WhatsApp, Gmail, or any future channel. Key attributes for analytics: `user_id` (owner), `source` (channel), `receivedAt` (timestamp), `ai_analysis.priority` (Urgent/Important/Normal/Low/pending), `ai_analysis.tasks_extracted` (array), `ai_analysis.status`.
- **Task (extracted)**: An actionable item extracted from a message. Key attributes for analytics: `user_id` (owner), `status` (active/completed), `extractedAt` (when it was created), associated message's `receivedAt` for period filtering.
- **AnalyticsAggregation**: Not a stored entity — computed on demand from Message and Task data for the selected period and user. Returned as a read-only snapshot.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A user opening the Analytics page sees accurate summary numbers within 2 seconds of page load (for up to 10,000 messages in the user's account).
- **SC-002**: Every count on the Analytics page exactly matches a direct database count on the user's messages for the same period and filters — zero discrepancy.
- **SC-003**: Charts render correctly and are readable at standard desktop widths (1280px+) and tablet widths (768px+) without horizontal scrolling or overlapping labels.
- **SC-004**: Toggling between Today / This Week / This Month updates all numbers and charts without a visible page reload or flicker within 1 second.
- **SC-005**: Two different users viewing Analytics at the same time see entirely separate data — no metric, chart segment, or count from one user is visible to the other.
- **SC-006**: When a user has zero messages, the Analytics page loads without errors and displays a clear empty-state message with guidance.
- **SC-007**: In dark mode, all chart colors, text, and card backgrounds maintain a contrast ratio of at least 4.5:1 against their backgrounds (WCAG AA standard).

## Assumptions

- The existing message schema (with `user_id`, `source`, `receivedAt`, and `ai_analysis` fields) is sufficient to compute all analytics metrics without schema changes.
- "This Week" defaults to the last 7 calendar days (not Monday–Sunday); "This Month" defaults to the last 30 days.
- Task completion is tracked via an existing `status` field on extracted tasks (active vs completed).
- The current purple/white theme applies to the Analytics page without modification to the design system.
- Charts are rendered client-side using a lightweight charting solution — no server-side image generation is used.
- The Analytics page is a single new page in the navigation (e.g., `/analytics`), not an overlay or modal.
