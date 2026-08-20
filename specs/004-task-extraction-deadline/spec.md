# Feature Specification: Task Extraction & Deadline Detection

**Feature Branch**: `004-task-extraction-deadline`  
**Created**: 2026-08-20  
**Status**: Draft  
**Input**: User description: "Create a clear and focused specification for two related features: Task Extraction and Urgency + Deadline Detection for Communication AI"

## Clarifications

### Session 2026-08-20

- Q: Should extracted tasks appear on a dedicated Tasks page or inline on the dashboard? → A: Both — tasks are stored in the `tasks` collection and shown on the Tasks page; messages with extracted tasks show a task indicator on the dashboard.
- Q: Should the system convert relative deadlines ("tomorrow") to exact dates? → A: Only when unambiguous and the current date is available. Otherwise preserve the original expression.
- Q: Can a single message produce multiple extracted tasks? → A: Yes, if the message contains multiple distinct actionable items.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Extract Tasks from Messages (Priority: P1)

As a user, I want the AI to automatically identify actionable tasks from
my incoming messages so that I can see what I need to do without reading
every message fully.

**Why this priority**: Task extraction is the core new capability. Without
it, the system only classifies priority — it does not tell the user what
to actually do. This is the primary value proposition of Day 11.

**Independent Test**: Can be fully tested by sending messages with clear
action items (e.g., "Send me the FYP slides tonight") and verifying that
the AI extracts the correct task with description, deadline, and priority
indicator. Also test with non-actionable messages to confirm no false tasks.

**Acceptance Scenarios**:

1. **Given** a message containing "Please send the report by Friday",
   **When** the AI analyzes the message, **Then** a task is extracted
   with description "Send the report", deadline "Friday", and
   requires_action = true.
2. **Given** a message containing "Can you review this document?",
   **When** the AI analyzes the message, **Then** a task is extracted
   with description "Review document", deadline = null, and
   requires_action = true.
3. **Given** a message containing "I'll send you the files tomorrow",
   **When** the AI analyzes the message, **Then** no task is extracted
   (the sender's promise is not the recipient's task).
4. **Given** a message containing "Hey, just FYI the server will be
   down tomorrow", **When** the AI analyzes the message, **Then** no
   task is extracted (informational, no action required).
5. **Given** a message with multiple action items (e.g., "Review the
   slides and send feedback by Thursday"), **When** the AI analyzes it,
   **Then** either one combined task or two separate tasks are extracted,
   each with correct deadline.

---

### User Story 2 - Detect Deadlines and Urgency (Priority: P1)

As a user, I want the system to understand relative time expressions
in my messages (like "ASAP", "tonight", "next week") so that deadlines
are captured accurately and priority is assigned correctly.

**Why this priority**: Deadline detection is tightly coupled with task
extraction and directly affects priority classification. It must ship
together with Task Extraction for the features to be useful. Without
correct deadline understanding, the AI cannot reliably classify Urgent
vs Important messages.

**Independent Test**: Can be tested by sending messages with various time
expressions ("ASAP", "tonight", "tomorrow", "next week", "before the
meeting") and verifying the system correctly classifies urgency and
preserves the deadline expression.

**Acceptance Scenarios**:

1. **Given** a message containing "Submit the form right now",
   **When** the AI analyzes it, **Then** the deadline is captured as
   "right now" and the message is classified as Urgent.
2. **Given** a message containing "Send me the slides tonight",
   **When** the AI analyzes it, **Then** the deadline is captured as
   "Tonight" (preserved exactly as stated).
3. **Given** a message containing "Review this by tomorrow",
   **When** the AI analyzes it, **Then** the deadline is captured as
   "tomorrow" and the message is classified as Important.
4. **Given** a message containing "Prepare the presentation next week",
   **When** the AI analyzes it, **Then** the deadline is captured as
   "next week" and the message is classified as Normal.
5. **Given** a message containing "Send docs before the meeting",
   **When** the AI analyzes it and no meeting date is known, **Then**
   the deadline is preserved as "before the meeting" (not converted
   to an invented date).
6. **Given** a message with no time expression, **When** the AI
   analyzes it, **Then** deadline is null and priority is not
   artificially elevated.

---

### User Story 3 - View Extracted Tasks on Dashboard (Priority: P2)

As a user, I want to see which messages have extracted tasks and view
my tasks in a dedicated section so that I can track what needs to be
done across all my messages.

**Why this priority**: This provides the visible output of task
extraction. Without a way to view tasks, the extraction has no user-facing
value. This is Day 12 work — depends on extraction working first.

**Independent Test**: Can be tested by sending messages that produce
tasks, then verifying the dashboard shows task indicators on those
messages and the Tasks page lists all extracted tasks with source
message references.

**Acceptance Scenarios**:

1. **Given** a message with extracted tasks, **When** the user views
   the dashboard, **Then** the message card shows a task indicator
   with the number of extracted tasks.
2. **Given** extracted tasks exist, **When** the user navigates to
   the Tasks page, **Then** all tasks are listed with description,
   deadline, priority indicator, status (pending), and source message.
3. **Given** a task on the Tasks page, **When** the user clicks the
   source message link, **Then** the system navigates to or highlights
   the original message.
4. **Given** no tasks have been extracted, **When** the user views the
   Tasks page, **Then** a friendly empty state is shown.

---

### Edge Cases

- What happens when a message contains a deadline but no clear task?
  → No task is extracted. The deadline informs priority classification
  only. Example: "The deadline for the project is Friday" is informational.
- What happens when the AI is uncertain whether a sentence is a task?
  → Extract it with low confidence. The user can dismiss false positives.
- What happens when a message is in a language the AI does not support?
  → No task is extracted. The message appears normally without task data.
  English-only is an explicit project scope limitation.
- What happens when a message is extremely long (10,000+ characters)?
  → Task extraction runs on the full content. If it fails due to length,
  the message is stored without tasks and the status is set to "pending".
- What happens when the AI service is unavailable?
  → Messages are stored without task extraction (empty tasks array).
  The dashboard shows the message without task indicators. No errors
  are shown to the user.
- What happens when two tasks in the same message have the same
  description?
  → They are combined into one task. Duplicate tasks from a single
  message are not created.
- What happens when a deadline expression is ambiguous ("before the
  meeting")?
  → The original expression is preserved as-is. No date is invented.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST extract actionable tasks from incoming messages
  during AI analysis, producing a task description, deadline (or null),
  and priority indicator for each task found.
- **FR-002**: System MUST detect relative time expressions (ASAP, today,
  tonight, tomorrow, next week, before the meeting, etc.) and preserve
  them as deadline values exactly as stated in the message.
- **FR-003**: System MUST convert relative time expressions to exact
  dates ONLY when the expression is unambiguous and the current date
  context is available. When conversion is unreliable, the original
  expression MUST be preserved.
- **FR-004**: System MUST store extracted tasks in the `tasks` collection
  with a reference to the source message.
- **FR-005**: System MUST link each extracted task to its source message
  so users can trace back to the original context.
- **FR-006**: System MUST NOT extract tasks from informational,
  social, or automated messages that do not request action from the
  recipient.
- **FR-007**: System MUST NOT invent deadlines. If no deadline is
  mentioned in the message, the deadline field MUST be null.
- **FR-008**: System MUST show a task count indicator on message cards
  in the dashboard when tasks have been extracted.
- **FR-009**: System MUST provide a Tasks page listing all extracted
  tasks with description, deadline, priority indicator, status, and
  source message reference.
- **FR-010**: System MUST classify messages with urgent time expressions
  (ASAP, right now, today, tonight) as Urgent priority. Messages with
  near-term expressions (tomorrow, this week) SHOULD be classified as
  Important.
- **FR-011**: System MUST complete task extraction and deadline detection
  within the same AI analysis call as priority classification (no
  additional API round-trip).
- **FR-012**: System MUST gracefully handle task extraction failures by
  storing messages with empty task arrays and "pending" status. No
  user-facing errors MUST be shown.

### Key Entities

- **Task**: Represents an actionable item extracted from a message.
  Key attributes: description (what needs to be done), deadline (when,
  as a string expression or null), priority_indicator (urgency words
  from the message or null), requires_action (boolean), status
  (pending/completed), source_message (reference to the originating
  message).
- **Message** (extended): The existing Message entity gains an
  `ai_analysis.tasks_extracted` field containing extracted task objects
  and an `ai_analysis.deadlines` field containing detected deadline
  expressions. These are embedded in the message document alongside
  priority, summary, and other AI analysis fields.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Task extraction correctly identifies actionable items in
  at least 85% of messages containing clear action requests (tested
  against a labeled set of 50 messages).
- **SC-002**: False positive rate is at most 10% — messages without
  actionable content do not produce extracted tasks.
- **SC-003**: Relative time expressions are correctly classified in at
  least 90% of messages containing varied time expressions (tested
  against a labeled set of 30 messages).
- **SC-004**: Zero invented deadlines across all test messages — any
  deadline value in an extracted task must come directly from the
  message text or be null.
- **SC-005**: Task extraction and deadline detection complete within the
  same analysis call, adding no measurable latency compared to priority
  classification alone.
- **SC-006**: Users can view all extracted tasks on the Tasks page with
  source message references within 3 seconds of page load.
- **SC-007**: Dashboard shows task indicators on messages within the
  10-second auto-poll interval after message ingestion.
- **SC-008**: System remains fully functional when AI analysis is
  unavailable — messages appear without tasks, no errors are shown.

## AI Analysis Flow

These features integrate into the existing AI analysis pipeline:

1. **Message arrives** via `POST /messages` or `POST /webhooks/whatsapp`.
2. **Synchronous AI analysis** triggers immediately on ingestion.
3. **Single LLM call** performs all analysis in one request:
   - Priority classification (existing — Urgent/Important/Normal/Low)
   - Summary generation (existing — under 30 words)
   - Task extraction (new — structured task objects)
   - Deadline detection (new — time expressions in deadline field)
4. **Results stored** in the message's `ai_analysis` embedded document.
5. **Tasks extracted** are also stored in the `tasks` collection with
   source message references.
6. **Dashboard displays** task indicators on message cards. Tasks page
   lists all extracted tasks.

The key constraint is that task extraction and deadline detection MUST
NOT require a separate LLM call. They are part of the single analysis
request to keep latency acceptable.

## Out of Scope (for this feature)

- Task completion/editing UI (covered by User Story 7 in baseline spec)
- Task deadline calendar integration
- Multi-language task extraction (English only)
- Automatic task reminders or notifications
- Task assignment to other users
