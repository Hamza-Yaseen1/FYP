# Feature Specification: Cross-Platform Dashboard

**Feature Branch**: `018-cross-platform-dashboard`
**Created**: 2026-09-11
**Status**: Draft
**Input**: User description: Create a clear and focused specification for Day 27 – Cross-Platform Dashboard. Project is Communication AI. Messages come from WhatsApp (simulate) and Gmail. AI analysis (priority, summary, task, deadline, recommended action) is working. Goal is a clean unified Dashboard that shows all communications together, grouped by priority (Urgent → Important → Normal → Low), with cards showing priority, main title (task/summary), source + sender, time, and optional deadline and recommended action. Only the logged-in user's messages are shown. Design stays clean and consistent with the current UI. "Needs Your Attention" still works well with this view.

## Feature Overview

The Cross-Platform Dashboard is the single home screen for all of a user's
communications. Today messages arrive from two channels — WhatsApp
(simulated) and Gmail — and each is analyzed by the AI pipeline (priority,
summary, tasks, deadline, recommended action). The Dashboard unifies these
channels into one priority-first view: every message appears as a card,
grouped top-to-bottom as URGENT, IMPORTANT, NORMAL, then LOW, so the user
instantly sees what deserves their attention first regardless of where the
message came from.

**Success means**: A user opens the Dashboard and, without opening any
individual page or message, sees everything they need — what's urgent,
what's important, and what can wait — with a clear source label
(WhatsApp / Gmail) on every card. The view is clean, consistent with the
rest of the app, and shows only the current user's data.

## User Scenarios & Testing *(mandatory)*

> User stories are prioritized as independently testable slices. Each story
> delivers value on its own, starting with the core grouping view.

### User Story 1 - Unified Priority-Grouped Dashboard (Priority: P1)

The user opens the Dashboard and sees all of their messages — WhatsApp and
Gmail together — in one place, grouped by priority. Groups are ordered
URGENT → IMPORTANT → NORMAL → LOW, and within each group the newest
messages appear first. This is the whole point of the feature: one place
for all platforms, priority-first.

**Why this priority**: This is the core deliverable. Without the unified
grouped view the feature does not exist; everything else is refinement.

**Independent Test**: Can be fully tested by creating one WhatsApp message
and one Gmail email with different priorities (via the message/simulate
API), then opening the Dashboard and confirming both appear side-by-side in
the correct priority groups inside a single view.

**Acceptance Scenarios**:

1. **Given** a user has messages from at least two sources (WhatsApp and
   Gmail) with different AI-assigned priorities, **When** they open the
   Dashboard, **Then** all messages appear together in one view, each placed
   in the group matching its stored priority.
2. **Given** messages with priorities spanning multiple levels, **When** the
   Dashboard renders, **Then** groups appear in the fixed order URGENT,
   IMPORTANT, NORMAL, LOW.
3. **Given** a group with no messages, **When** the Dashboard renders,
   **Then** that group section is not displayed at all (no empty headers).

---

### User Story 2 - Informative Message Cards (Priority: P2)

Each message on the Dashboard renders as a clean card showing what the user
needs at a glance: a priority indicator, a main title (the extracted task,
the AI summary, or a content preview), the source and sender, and the time
received. When available, the card also shows the deadline (in original
wording) and the recommended action.

**Why this priority**: The grouping view (US1) delivers the core value;
rich cards make it actionable. This story is independently testable since a
card renders correctly on its own.

**Independent Test**: Can be fully tested by rendering a single message of a
known source/sender with known stored analysis and confirming every expected
field appears, and then rendering a message missing optional fields to
confirm clean omission.

**Acceptance Scenarios**:

1. **Given** any message on the Dashboard, **When** its card renders,
   **Then** it shows the priority indicator, main title, source + sender, and
   time received.
2. **Given** a message with a stored deadline and recommended action,
   **When** its card renders, **Then** both appear (deadline in original
   wording, e.g., "Tonight" — not a computed date).
3. **Given** a message missing optional fields (no deadline, no subject, no
   recommended action), **When** its card renders, **Then** the missing
   fields are omitted cleanly — never "null", "undefined", or blank gaps.

---

### User Story 3 - Needs Your Attention Integration (Priority: P2)

Messages flagged "Needs Your Attention" still work well in this view. A
flagged card appears inside its priority group with a visible attention
badge and a truthful "Why it matters" explanation, and keeps the deadline
and recommended action readable — matching the existing attention page
behavior.

**Why this priority**: Attention flags are an existing, trusted feature. This
story keeps that promise inside the new unified view without breaking the
existing attention page.

**Independent Test**: Can be fully tested by creating a message that meets
the attention criteria (actionable task + near deadline, or urgent priority),
opening the Dashboard, and confirming the card shows the badge and a truthful
reason.

**Acceptance Scenarios**:

1. **Given** a message that meets the attention criteria, **When** the
   Dashboard renders, **Then** the card shows a "Needs Your Attention" badge
   with a "Why it matters" line naming the real trigger.
2. **Given** a flagged card, **When** the user reads it in the Dashboard,
   **Then** the recommended action and deadline remain visible, consistent
   with the `/attention` page.

---

### User Story 4 - User Isolation and Graceful States (Priority: P3)

The Dashboard only ever shows the authenticated user's messages. When there
are no messages at all, a friendly empty state is shown. Messages whose AI
analysis is pending or failed still render with the fields that exist, plus a
pending indicator — nothing breaks.

**Why this priority**: Isolation and graceful degradation are correctness and
security requirements, not new features. They harden US1–3 and are
independently verifiable.

**Independent Test**: Can be fully tested with a two-user check (each user
sees only their own messages) and by rendering the Dashboard for a user with
zero messages and for a user with a pending-analysis message.

**Acceptance Scenarios**:

1. **Given** two logged-in users with separate messages, **When** each opens
   the Dashboard, **Then** each sees only their own messages, in both the UI
   and direct API calls.
2. **Given** a user with no messages at all, **When** they open the
   Dashboard, **Then** a clear "No messages yet" empty state is shown.
3. **Given** a message whose AI analysis is pending or failed, **When** the
   Dashboard renders, **Then** the message still appears with whatever fields
   exist and a pending indicator — no layout break.

---

### Edge Cases

- **No messages at all**: Dashboard shows a clear "No messages yet" empty
  state, not a broken or blank layout.
- **Empty priority group**: Groups with zero messages are hidden entirely.
- **Pending / failed AI analysis**: Message still renders with available
  fields and a pending indicator; no blocking on AI availability.
- **Missing optional fields**: Cards omit deadline, subject, summary, or
  recommended action cleanly when absent.
- **Very long content**: Main title is truncated with an ellipsis; the full
  content remains available by opening the message.
- **Unknown / future channel**: A source outside WhatsApp and Gmail still
  renders a readable source label and an otherwise identical card.
- **Unread vs read**: The Dashboard shows all of the user's messages
  regardless of read state; an unread emphasis (e.g., a dot) MAY be added
  without changing grouping.
- **No AI analysis at all** (pre-Orchestrator or skipped): Card falls back to
  a content preview and a normal/pending treatment; nothing breaks.
- **Message deleted elsewhere**: The Dashboard reflects the current stored
  set on load; no stale-card artifacts.
- **Many messages in one group**: The group remains scrollable and the
  Dashboard stays responsive (performance target in Success Criteria).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display messages from all connected sources
  (WhatsApp, Gmail, and future channels) in a single unified Dashboard view
  — no separate pages per channel.
- **FR-002**: System MUST group messages into priority sections ordered
  URGENT, IMPORTANT, NORMAL, LOW based on the stored AI priority of each
  message.
- **FR-003**: System MUST order messages within each priority group by time
  received, newest first.
- **FR-004**: Each message card MUST display the priority, a main title
  (extracted task description, else AI summary, else content preview), the
  source + sender, and the time received.
- **FR-005**: When present in stored data, a card MUST display the deadline
  in original wording and the recommended action.
- **FR-006**: When a Gmail subject exists, the card SHOULD surface it (e.g.,
  as the title or a subtitle); it is absent for WhatsApp.
- **FR-007**: System MUST hide priority groups that contain no messages.
- **FR-008**: System MUST show only the authenticated user's messages; every
  Dashboard data request is scoped to that user and returns nothing from
  others.
- **FR-009**: System MUST render cards cleanly when optional fields are
  missing — never "null", "undefined", or blank gaps.
- **FR-010**: Messages with pending or failed AI analysis MUST still appear
  with available fields and a pending indicator.
- **FR-011**: "Needs Your Attention" flags MUST remain visible and truthful
  in this view — attention badge plus a "Why it matters" explanation.
- **FR-012**: When the user has no messages at all, the Dashboard MUST show a
  clear empty state.
- **FR-013**: The Dashboard MUST follow the app's existing design language
  (shared visual tokens, light/dark mode) and feel consistent with the Inbox,
  Tasks, and Attention pages.
- **FR-014**: The Dashboard MUST render from stored message data only — it
  MUST NOT invoke AI analysis or recompute priorities in the UI.

### Dashboard Layout Rules

- **Single view**: The Dashboard is one scrollable page. No tabs, no
  per-channel sections, no per-channel pages.
- **Priority sections top to bottom**: URGENT, IMPORTANT, NORMAL, LOW, in
  that fixed order. Section headers are simple and unobtrusive.
- **Cards flow within sections**: Cards stack vertically inside their
  priority section, newest first, with consistent spacing.
- **Attention stays visible**: A flagged card remains in its priority group
  and carries its attention badge — it is not moved into a separate section.
- **Empty state**: A no-messages Dashboard shows one friendly message in the
  center of the content area.

### Card Content Rules

- **Priority**: A small colored indicator matching the existing urgent /
  important / normal / low visual language.
- **Main title**: The extracted task description when tasks exist; otherwise
  the AI summary; otherwise a concise content preview. Truncated with an
  ellipsis when long.
- **Source + sender**: A recognizable label and/or icon for the channel
  (WhatsApp / Gmail) followed by the sender name ("Source • Sender").
- **Time**: Relative time ("2h ago") or a formatted date; raw ISO timestamps
  are never shown.
- **Optional - Deadline**: Shown only when stored, in the original wording
  (e.g., "Tonight").
- **Optional - Subject**: Shown for Gmail when present.
- **Optional - Recommended action**: Shown when stored, single verb-first
  sentence.
- **Optional - Attention**: Badge + "Why it matters" only when the stored
  analysis flags the message.

### Sorting and Grouping Logic

- **Group membership**: Determined solely by each message's stored AI
  priority (`urgent`, `important`, `normal`, `low`). The UI never reclassifies.
- **Group order**: URGENT → IMPORTANT → NORMAL → LOW, fixed and always in
  this order when non-empty.
- **Within-group order**: By time received, newest first. Equal timestamps
  preserve insertion order (stable).
- **Pending/unanalyzed messages**: Treated as a "pending" state; they can
  either appear within NORMAL with a pending indicator or in a dedicated
  tail section — but they MUST NOT collide with classified groups or shift
  them out of order.

### Key Entities *(include if feature involves data)*

- **Message**: The unified stored communication — `source`, `sender`,
  `content`, `subject` (Gmail only), `received_at`, owner `user_id`, and
  analysis reference. The Dashboard reads this and nothing else.
- **ai_analysis**: The stored analysis attached to a message — `priority`,
  `confidence`, `summary`, `tasks_extracted` (main title source), `deadlines`,
  `recommended_action`, `needs_attention`, `attention_reason`. All card fields
  are read from here; nothing is computed in the UI.
- **Priority group**: A derived view grouping messages by their stored
  priority (Urgent / Important / Normal / Low) — not a stored entity.
- **User**: The account that owns messages; the Dashboard is scoped to the
  authenticated user's `user_id` exclusively.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of a user's messages across all connected sources appear
  in one Dashboard view — verified by creating a WhatsApp message and a Gmail
  email and confirming both render together.
- **SC-002**: 100% of message cards are placed in the priority group matching
  their stored AI priority — verified against a set of messages spanning all
  four priorities.
- **SC-003**: The Dashboard loads and displays up to 100 messages within 2
  seconds on a typical connection, without blocking on AI availability.
- **SC-004**: Two-user isolation verified — each user sees only their own
  messages in both the UI and direct API calls, including guessed message IDs.
- **SC-005**: 100% of cards render without layout breakage when optional
  fields (deadline, subject, summary, recommended action) are missing.
- **SC-006**: 100% of "Needs Your Attention" cards carry a truthful "Why it
  matters" explanation — zero invented reasons.
- **SC-007**: WhatsApp and Gmail messages produce visually identical card
  quality from the same stored fields; the source is identifiable only by its
  label.
- **SC-008**: Existing Inbox, Tasks, and Attention pages continue to work
  unchanged after the Dashboard is introduced (no regression).