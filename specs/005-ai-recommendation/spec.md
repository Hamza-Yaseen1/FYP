# Feature Specification: AI Recommended Action

**Feature Branch**: `005-ai-recommendation`  
**Created**: 2026-08-21  
**Status**: Draft  
**Input**: User description: "Create a clear and focused specification for the AI Recommendation feature (Day 13). Generate a short and useful recommended action when a message is analyzed."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Recommended Action on Dashboard (Priority: P1)

As a user, when I open my dashboard, I want to see a recommended action for each message so that I can quickly understand what to do next without reading the full message.

**Why this priority**: This is the core value of the feature. Users scan dashboards quickly, and a clear recommended action saves time and reduces cognitive load.

**Independent Test**: Can be fully tested by sending a test message and verifying the recommended action appears on the dashboard alongside priority, summary, and task information.

**Acceptance Scenarios**:

1. **Given** a user receives a message with a clear action request, **When** the message is analyzed, **Then** a recommended action is displayed on the dashboard.
2. **Given** a user receives an informational message with no action required, **When** the message is analyzed, **Then** a generic recommended action (e.g., "Review this message") is displayed.
3. **Given** the AI analysis fails, **When** the message is displayed, **Then** no recommended action is shown (empty) and the message still appears on the dashboard.

---

### User Story 2 - Recommended Action in Different Languages (Priority: P2)

As a user who receives messages in different languages, I want the recommended action to be in the same language as the original message so that I can understand it naturally.

**Why this priority**: Many users communicate in multiple languages. A recommendation in the wrong language reduces usability and trust.

**Independent Test**: Can be tested by sending messages in English and Arabic, verifying each recommendation matches the message language.

**Acceptance Scenarios**:

1. **Given** a user receives a message in English, **When** the message is analyzed, **Then** the recommended action is in English.
2. **Given** a user receives a message in Arabic, **When** the message is analyzed, **Then** the recommended action is in Arabic.

---

### User Story 3 - Recommended Action with Deadline Context (Priority: P3)

As a user, when a message includes a deadline, I want the recommended action to reference the deadline so that I can prioritize appropriately.

**Why this priority**: Deadline awareness helps users act with urgency when needed. This is valuable but builds on the basic recommendation feature.

**Independent Test**: Can be tested by sending messages with and without deadlines, verifying recommendations reference time context when present.

**Acceptance Scenarios**:

1. **Given** a message says "Send the report before Friday", **When** the message is analyzed, **Then** the recommended action references the Friday deadline.
2. **Given** a message has no deadline mentioned, **When** the message is analyzed, **Then** the recommended action focuses on the action itself without time reference.

---

### Edge Cases

- What happens when a message contains multiple possible actions? The system picks the ONE most important action.
- What happens when the message is in a language the AI cannot identify? The system defaults to the same language as the message content (best effort).
- What happens when the AI is uncertain about the action? The system returns "Review this message" as a safe fallback.
- What happens when the message is empty or contains only attachments? The system returns "Review this message".

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST generate a single recommended action for every analyzed message.
- **FR-002**: The recommended action MUST be a verb-first sentence (e.g., "Send the report", not "The report should be sent").
- **FR-003**: The recommended action MUST be under 15 words.
- **FR-004**: The recommended action MUST be in the same language as the original message.
- **FR-005**: When a message contains a clear action request, the recommended action MUST reflect that action.
- **FR-006**: When no clear action exists, the recommended action MUST be "Review this message".
- **FR-007**: The recommended action MUST NOT invent actions not present in the message.
- **FR-008**: The recommended action MUST be generated in the same LLM call as priority, summary, and task extraction (no additional latency).
- **FR-009**: System MUST store the recommended action alongside the message in the database.
- **FR-010**: Dashboard MUST display the recommended action for each message.
- **FR-011**: If recommendation generation fails, the system MUST return an empty string and still display the message.

### Key Entities

- **Message**: A communication received by the user (WhatsApp, Gmail, etc.) with attributes including: content, sender, timestamp, priority, summary, tasks, deadlines, and now recommended_action.
- **Recommended Action**: A single string field on the Message entity representing the suggested next step for the user.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 90% of messages with clear action requests produce a recommendation that directly reflects the message content (tested against 50 labeled messages).
- **SC-002**: 0% of recommendations invent actions not present in the message (zero hallucination).
- **SC-003**: Recommended actions appear on the dashboard without adding noticeable load time.
- **SC-004**: Users can scan a message's recommended action and understand the next step within 2 seconds.
- **SC-005**: Recommendations match the language of the original message in 100% of tested cases.

## Assumptions

- The AI analysis pipeline (priority, summary, task extraction, deadline detection) is already working and can be extended with recommendation generation.
- The dashboard UI has space to display the recommended action alongside existing fields.
- Users want a single recommended action, not multiple options.
- The feature is part of the existing message analysis flow, not a separate step.

## Out of Scope

- Auto-executing the recommended action (the feature is advisory only).
- Multiple recommendations per message.
- User-configurable recommendation preferences.
- Recommendation history or analytics.
