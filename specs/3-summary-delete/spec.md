# Feature Specification: Summary Agent & Delete Message

**Feature Branch**: `3-summary-delete`
**Created**: 2026-08-20
**Status**: Draft
**Input**: User description: "Summary Agent for Communication AI - create short summaries + Delete Message feature on Dashboard"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Automatic Summary Generation (Priority: P1)

As a user, I want incoming messages to be automatically summarized
so that I can quickly understand what each message is about without
reading the full content.

**Why this priority**: This is the core value of the Summary Agent.
Without summaries, users must read every message to understand its content.

**Independent Test**: Can be tested by sending messages with different
content and verifying the agent produces accurate, concise summaries.

**Acceptance Scenarios**:

1. **Given** a message with a clear action item, **When** the agent
   analyzes it, **Then** a 1-2 sentence summary is generated that
   captures the main point.
2. **Given** a casual message with no action, **When** the agent
   analyzes it, **Then** a brief summary is generated that reflects
   the message content.
3. **Given** an AI summary, **When** the user views the message,
   **Then** the summary is displayed below the message content.

---

### User Story 2 - Delete Message (Priority: P2)

As a user, I want to delete messages from my dashboard so that I can
keep my inbox clean and remove messages I no longer need.

**Why this priority**: Users need to manage their message list. Deleting
unwanted messages keeps the dashboard focused on what matters.

**Independent Test**: Can be tested by deleting a message and verifying
it is permanently removed from MongoDB.

**Acceptance Scenarios**:

1. **Given** a message on the dashboard, **When** the user clicks the
   delete button, **Then** a confirmation dialog appears.
2. **Given** a confirmation dialog, **When** the user confirms deletion,
   **Then** the message is permanently removed from MongoDB.
3. **Given** a deleted message, **When** the dashboard refreshes,
   **Then** the message no longer appears in the list.

---

### User Story 3 - Summary Display (Priority: P3)

As a user, I want to see summaries on the dashboard so that I can
quickly scan messages and decide which ones need attention.

**Why this priority**: Summaries are only useful if they are visible
and easily accessible on the dashboard.

**Independent Test**: Can be tested by verifying summaries are displayed
on the message cards in the dashboard.

**Acceptance Scenarios**:

1. **Given** a message with a summary, **When** the user views the
   dashboard, **Then** the summary is displayed below the message content.
2. **Given** a message without a summary (AI failed), **When** the user
   views the dashboard, **Then** no summary is shown (not an error message).

---

### Edge Cases

- What happens when the summary agent is unavailable? The message
  appears without a summary (null value).
- What happens when the message is too short to summarize? The agent
  returns the original message as the summary.
- What happens when the user tries to delete a message while offline?
  The deletion fails and an error message is shown.
- What happens when two users try to delete the same message? The
  first deletion succeeds, the second fails (single-user system).
- What happens when the message has associated tasks? Deleting the
  message does not delete associated tasks.

## Requirements *(mandatory)*

### Functional Requirements - Summary Agent

- **FR-001**: Agent MUST generate a summary for each message within
  2 seconds for messages under 1000 characters.
- **FR-002**: Summary MUST be 1-2 sentences or under 30 words.
- **FR-003**: Summary MUST accurately reflect the message content
  without inventing information.
- **FR-004**: Summary MUST preserve action items, deadlines, and
  requests from the original message.
- **FR-005**: Agent MUST default to null when uncertain or when
  analysis fails.
- **FR-006**: Agent MUST NOT invent information not present in
  the original message.
- **FR-007**: Agent MUST handle messages from any channel (WhatsApp,
  Gmail, Simulated) identically.
- **FR-008**: Summary MUST be stored in the message's ai_analysis
  field in MongoDB.

### Functional Requirements - Delete Message

- **FR-009**: User MUST be able to delete any message from the dashboard.
- **FR-010**: System MUST show a confirmation dialog before deletion.
- **FR-011**: Deleted messages MUST be permanently removed from MongoDB.
- **FR-012**: Dashboard MUST update immediately after deletion.
- **FR-013**: System MUST handle deletion errors gracefully and show
  a user-friendly error message.
- **FR-014**: Deleting a message MUST NOT affect other messages or tasks.

### Key Entities

- **Summary**: The agent's output for a message. Key attributes:
  content (string), generated_at (timestamp), status (completed/pending).
- **Message**: The input to the agent. Key attributes: content (string),
  sender (string), source (channel), timestamp.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Agent generates summaries that accurately reflect message
  content at least 85% of the time when measured against human judgment.
- **SC-002**: Summaries are under 30 words for 90% of messages.
- **SC-003**: Agent completes analysis within 2 seconds for 95% of
  messages under 1000 characters.
- **SC-004**: Users can delete messages without errors 100% of the time.
- **SC-005**: Deleted messages are permanently removed from MongoDB
  100% of the time.
- **SC-006**: Dashboard updates within 1 second after message deletion.

## Summary Agent Behavior Rules

### What Agent MUST Do

- Extract the main point or request from the message
- Identify and include action items, deadlines, and requests
- Remove greetings, pleasantries, and filler content
- Preserve the urgency level implied by the message
- Return results quickly (within 2 seconds)
- Handle messages of any length (short or long)

### What Agent MUST NEVER Do

- Invent information not present in the message
- Add opinions, interpretations, or assumptions
- Change the meaning of the original message
- Include sender identity in the summary
- Auto-respond or take action based on the summary
- Store or log message content beyond the analysis
- Modify the original message content

## Delete Message Behavior Rules

### What Feature MUST Do

- Show a delete button on each message card
- Display a confirmation dialog before deletion
- Remove the message from MongoDB permanently
- Update the dashboard immediately after deletion
- Handle errors gracefully (show message if deletion fails)

### What Feature MUST NEVER Do

- Auto-delete messages without user action
- Delete multiple messages at once (batch delete)
- Soft-delete or archive messages
- Affect other messages, tasks, or system state
- Delete messages from external channels (WhatsApp, Gmail)

## Non-Functional Requirements

### Performance

- Summary agent MUST complete analysis within 2 seconds for messages
  under 1000 characters
- Delete operation MUST complete within 1 second
- Dashboard MUST update within 1 second after changes

### Reliability

- Summary agent MUST default to null on any failure
- Delete operation MUST handle errors gracefully
- System MUST log errors for debugging without exposing message content

### Security

- Summary agent MUST NOT log message content in plaintext
- Delete operation MUST require user confirmation
- System MUST NOT allow deletion without explicit user action

## Out of Scope (for this FYP)

- Learning from user feedback to improve summaries
- Custom summary length per user
- Bulk message deletion
- Message recovery after deletion
- Summary editing by user
- Multi-language summary generation

## Assumptions

- Messages are in English (FYP scope)
- Single user system (no multi-tenant deletion rules)
- LLM API is available for summary generation
- Messages are under 10,000 characters
- Users want to keep most messages (deletion is occasional)
