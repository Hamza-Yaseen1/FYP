# Feature Specification: Communication AI Baseline

**Feature Branch**: `1-baseline-spec`
**Created**: 2026-08-19
**Status**: Draft
**Input**: User description: "Baseline specification for Communication AI FYP"

## Clarifications

### Session 2026-08-19

- Q: When should AI analysis run on incoming messages? → A: Synchronous - analyze immediately on receive, return results in response
- Q: What states can a message be in? → A: Active / Archived (2 states, minimal — active = visible on dashboard)
- Q: How does the dashboard get updated with new messages? → A: Auto-poll every 10 seconds

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Message Dashboard (Priority: P1)

As a user, I want to see all my incoming messages on a single dashboard so
that I can quickly understand what needs my attention without switching
between apps.

**Why this priority**: This is the core value proposition. Without a
dashboard, the system has no visible output.

**Independent Test**: Can be fully tested by sending simulated messages
and verifying they appear on the dashboard with correct content and metadata.

**Acceptance Scenarios**:

1. **Given** the user is on the dashboard, **When** a new message arrives,
   **Then** it appears in the message list within 10 seconds (auto-poll interval).
2. **Given** the user is on the dashboard, **When** messages exist,
   **Then** they are displayed with sender, preview, timestamp, and channel.
3. **Given** the user is on the dashboard, **When** no messages exist,
   **Then** a friendly empty state is shown.

---

### User Story 2 - Simulate Incoming Messages (Priority: P1)

As a developer/tester, I want to simulate messages from different channels
(WhatsApp, Gmail) so that I can test the system without real integrations.

**Why this priority**: Simulation enables development and demo without
external API dependencies. This is essential for an FYP.

**Independent Test**: Can be tested by sending a simulation request and
verifying the message appears in the system with correct channel attribution.

**Acceptance Scenarios**:

1. **Given** the simulation endpoint is available, **When** a simulated
   message is sent, **Then** it is stored and appears on the dashboard.
2. **Given** a simulated message, **When** the channel is specified,
   **Then** the message is attributed to that channel (WhatsApp, Gmail, etc.).
3. **Given** multiple simulated messages, **When** they are sent in sequence,
   **Then** they appear in chronological order.

---

### User Story 3 - AI Priority Classification (Priority: P2)

As a user, I want messages to be automatically prioritized so that I can
focus on urgent items first.

**Why this priority**: Priority classification is the core AI feature
that differentiates this from a simple message viewer.

**Independent Test**: Can be tested by sending messages with different
content and verifying the AI assigns appropriate priority levels.

**Acceptance Scenarios**:

1. **Given** a message containing a deadline, **When** the AI analyzes it,
   **Then** it is classified as Urgent or Important.
2. **Given** a casual message, **When** the AI analyzes it,
   **Then** it is classified as Normal or Low.
3. **Given** an AI classification, **When** the user views the message,
   **Then** the priority level is clearly displayed with a visual indicator.

---

### User Story 4 - AI Task Extraction (Priority: P2)

As a user, I want the AI to extract actionable tasks from messages so
that I can see what I need to do without reading every message fully.

**Why this priority**: Task extraction transforms passive message reading
into active task management.

**Independent Test**: Can be tested by sending messages with clear action
items and verifying the AI extracts them correctly.

**Acceptance Scenarios**:

1. **Given** a message containing "Please send the report by Friday",
   **When** the AI analyzes it, **Then** a task is extracted with the
   deadline "Friday".
2. **Given** an extracted task, **When** the user views it,
   **Then** it shows the source message, extracted action, and deadline.
3. **Given** a message with no actionable content, **When** the AI analyzes it,
   **Then** no task is extracted (no false positives).

---

### User Story 5 - AI Message Summary (Priority: P3)

As a user, I want a brief summary of each message so that I can quickly
understand the content without reading the full text.

**Why this priority**: Summaries reduce cognitive load and speed up
triage, but are less critical than priority and task extraction.

**Independent Test**: Can be tested by sending long messages and verifying
the AI generates concise, accurate summaries.

**Acceptance Scenarios**:

1. **Given** a long message, **When** the AI generates a summary,
   **Then** it is under 100 words and captures the key points.
2. **Given** a short message, **When** the AI generates a summary,
   **Then** it is proportionally shorter or shows the full text.
3. **Given** a summary, **When** the user clicks to expand,
   **Then** the full message is revealed.

---

### User Story 6 - Recommended Actions (Priority: P3)

As a user, I want the AI to suggest what I should do next for each message
so that I can act quickly without thinking.

**Why this priority**: Recommended actions enhance the experience but
require high AI accuracy to be useful.

**Independent Test**: Can be tested by sending different message types
and verifying the AI suggests appropriate actions.

**Acceptance Scenarios**:

1. **Given** a message requesting a response, **When** the AI analyzes it,
   **Then** it suggests "Reply" as a recommended action.
2. **Given** a message with a meeting request, **When** the AI analyzes it,
   **Then** it suggests "Schedule" or "Confirm" as a recommended action.
3. **Given** a recommended action, **When** the user sees it,
   **Then** it is clearly marked as a suggestion, not an automated action.

---

### User Story 7 - Task Management (Priority: P3)

As a user, I want to view, complete, and manage tasks extracted from
messages so that I can track my progress.

**Why this priority**: Task management builds on task extraction and
provides a complete workflow.

**Independent Test**: Can be tested by extracting tasks and verifying
the user can mark them complete, edit, or delete them.

**Acceptance Scenarios**:

1. **Given** extracted tasks, **When** the user views the task list,
   **Then** they see all tasks with status, deadline, and source message.
2. **Given** a task, **When** the user marks it complete,
   **Then** the status updates and it moves to the completed section.
3. **Given** a task, **When** the user deletes it,
   **Then** it is removed from the list (but the source message remains).

---

### User Story 8 - User Authentication (Priority: P4)

As a user, I want to create an account and log in so that my messages
and tasks are private and isolated from other users.

**Why this priority**: Authentication is essential for production but
can be deferred during development with a single-user mode.

**Independent Test**: Can be tested by creating an account, logging in,
and verifying that messages are isolated between users.

**Acceptance Scenarios**:

1. **Given** a new user, **When** they register with email and password,
   **Then** an account is created and they are logged in.
2. **Given** a logged-in user, **When** they view the dashboard,
   **Then** they only see their own messages.
3. **Given** two different users, **When** each has messages,
   **Then** neither can see the other's messages.

---

### Edge Cases

- What happens when the AI service is unavailable? The system shows messages
  without AI analysis and displays a "AI analysis pending" indicator.
- What happens when a message is extremely long (10,000+ characters)?
  The system truncates the preview and provides a "Read more" option.
- What happens when the AI confidence is low? The system shows the
  classification with a "Needs review" flag for user confirmation.
- What happens when duplicate messages arrive? The system deduplicates
  based on message content and timestamp within a 5-minute window.
- What happens when a user has no messages? The system shows a welcome
  screen with instructions to simulate a message.
- What happens when all messages are archived? The system shows an empty
  active state with a link to view archived messages.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display all user messages in a chronological
  dashboard view with sender, preview, timestamp, and channel. The dashboard
  MUST auto-poll for updates every 10 seconds.
- **FR-002**: System MUST accept simulated messages via an API endpoint
  with configurable channel, sender, and content. Analysis runs synchronously
  and results are returned in the response.
- **FR-003**: System MUST classify messages into priority levels
  (Urgent, Important, Normal, Low) using AI analysis executed at ingestion time.
- **FR-004**: System MUST extract actionable tasks from messages
  including action description and deadline when present.
- **FR-005**: System MUST generate concise summaries (under 100 words)
  for messages longer than 200 characters.
- **FR-006**: System MUST suggest recommended actions (Reply, Schedule,
  Archive, etc.) based on message content.
- **FR-007**: System MUST allow users to mark tasks as complete,
  edit task details, or delete tasks.
- **FR-008**: System MUST isolate user data so each user only sees
  their own messages and tasks.
- **FR-009**: System MUST gracefully handle AI service unavailability
  by showing messages without analysis.
- **FR-010**: System MUST provide a single-user development mode
  without authentication for local testing.

### Key Entities

- **Message**: Represents an incoming communication. Key attributes:
  content, sender, channel (WhatsApp/Gmail/Simulated), timestamp,
  priority (AI-generated), summary (AI-generated), tasks (extracted),
  state (Active/Archived, default: Active).
- **Task**: Represents an actionable item extracted from a message.
  Key attributes: description, deadline, status (pending/completed),
  source message reference.
- **User**: Represents a system user. Key attributes: email, password
  (hashed), display name, created timestamp.
- **Channel**: Represents a communication source. Key attributes:
  name (WhatsApp, Gmail, Simulated), status (active/inactive),
  configuration.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can view all messages on a single dashboard in
  under 3 seconds from page load.
- **SC-002**: Simulated messages appear on the dashboard within
  10 seconds of being sent (auto-poll interval).
- **SC-003**: AI priority classification matches human judgment
  at least 80% of the time on a test set of 50 messages.
- **SC-004**: Task extraction correctly identifies actionable items
  in at least 85% of messages containing clear action requests.
- **SC-005**: Message summaries capture key points and are under
  100 words for 90% of messages tested.
- **SC-006**: Users can complete the full workflow (view message,
  see priority, review task, mark complete) in under 2 minutes.
- **SC-007**: System handles 100 simulated messages without
  performance degradation or errors.
- **SC-008**: Dashboard remains functional when AI service is
  unavailable, showing messages with "Analysis pending" status.

## Priority Levels Definition

### Urgent

Messages requiring immediate attention within hours. Examples:
- Deadline today or tomorrow
- Time-sensitive request from a person of authority
- System alerts or security notifications
- Escalated issues

**Visual**: Red indicator, top of queue, notification badge.

### Important

Messages requiring attention within 1-3 days. Examples:
- Meeting requests for this week
- Action items with deadlines within the week
- Requests from colleagues or clients
- Documents requiring review

**Visual**: Orange indicator, near top of queue.

### Normal

Messages requiring attention but not time-sensitive. Examples:
- FYI emails with potential action items
- Newsletter with relevant content
- Casual requests without deadlines
- Social messages requiring response

**Visual**: Blue indicator, middle of queue.

### Low

Messages requiring minimal or no immediate action. Examples:
- Automated notifications
- Marketing emails
- Social media notifications
- Group chat messages not addressed to user

**Visual**: Gray indicator, bottom of queue.

## AI Behavior Rules

### What AI MUST Do

- Analyze message content synchronously at ingestion time to determine priority level
- Extract actionable tasks when clear action requests exist
- Generate concise summaries for long messages
- Suggest appropriate next actions based on message type
- Provide confidence levels for all classifications
- Log analysis decisions for improvement tracking

### What AI MUST NOT Do

- Auto-send responses without user confirmation
- Auto-delete or archive messages without user action
- Make assumptions about sender intent without evidence
- Access messages from other users
- Store raw API keys or secrets in analysis results
- Override user-defined priority settings

### Fallback Behavior

When AI confidence is below 70%:
- Show the classification with "Needs review" flag
- Present the full message for manual review
- Allow user to correct the classification
- Log the discrepancy for prompt improvement

When AI service is unavailable:
- Show all messages without analysis
- Display "AI analysis pending" indicator
- Queue messages for analysis when service recovers
- Never block the dashboard from loading

## Non-Functional Requirements

### Security

- User passwords MUST be hashed using industry-standard algorithms
- API keys and secrets MUST be stored in environment variables
- Message content MUST NOT be logged in plaintext in production
- User data MUST be isolated at the database query level
- The system MUST use HTTPS for all production deployments

### Performance

- Dashboard MUST load in under 3 seconds on localhost
- API responses MUST return in under 500ms (excluding AI calls)
- AI-powered features MUST show loading states, never block UI
- The system MUST handle 100 concurrent messages without degradation
- Dashboard MUST auto-poll for new messages every 10 seconds (configurable)

### Privacy

- Users MUST be able to export their data
- Users MUST be able to delete their account and all associated data
- Message content MUST NOT be shared with third parties
- AI analysis MUST happen server-side, never exposed to client

### Reliability

- The system MUST gracefully handle AI service unavailability
- The system MUST not lose messages during processing
- The system MUST provide meaningful error messages to users
- The system MUST log errors for debugging without exposing secrets

## Out of Scope (for this FYP)

- Real WhatsApp Business API integration (simulated only)
- Real Gmail API integration (simulated only)
- Mobile application (web dashboard only)
- Multi-language support (English only)
- Advanced analytics and reporting
- Team collaboration features
- Email composition and sending
- Calendar integration
- Natural language query interface
- Offline mode
- Real-time notifications (polling or manual refresh only)

## Assumptions

- The primary user is a single person using the system for personal
  communication management
- Simulated messages are sufficient for FYP demonstration
- AI analysis does not need to be perfect (80%+ accuracy is acceptable)
- The system will be deployed locally or on a free-tier cloud service
- MongoDB is available for data storage
- The LLM API has sufficient rate limits for development and demo
