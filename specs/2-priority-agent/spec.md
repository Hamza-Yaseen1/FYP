# Feature Specification: Priority Agent

**Feature Branch**: `2-priority-agent`
**Created**: 2026-08-19
**Status**: Draft
**Input**: User description: "Priority Agent for Communication AI - classify messages into URGENT/IMPORTANT/NORMAL/LOW"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Automatic Priority Classification (Priority: P1)

As a user, I want incoming messages to be automatically classified by
priority so that I can focus on what matters first without reading
every message.

**Why this priority**: This is the core value of the Priority Agent.
Without automatic classification, users must manually triage every message.

**Independent Test**: Can be tested by sending messages with different
content and verifying the agent assigns appropriate priority levels.

**Acceptance Scenarios**:

1. **Given** a message with a deadline today, **When** the agent analyzes it,
   **Then** it is classified as URGENT with a confidence score.
2. **Given** a casual message with no deadline, **When** the agent analyzes it,
   **Then** it is classified as NORMAL.
3. **Given** an AI classification, **When** the user views the message,
   **Then** the priority level is clearly displayed with a visual indicator.

---

### User Story 2 - Priority Override (Priority: P2)

As a user, I want to change the priority of a message when the agent
gets it wrong so that I retain control over my workflow.

**Why this priority**: The agent will make mistakes. Users must be able
to correct classifications to maintain trust and accuracy.

**Independent Test**: Can be tested by changing a message's priority
and verifying the override persists.

**Acceptance Scenarios**:

1. **Given** a message classified as NORMAL, **When** the user changes it
   to URGENT, **Then** the new priority is saved and displayed.
2. **Given** a user override, **When** the dashboard refreshes,
   **Then** the overridden priority persists.

---

### User Story 3 - Confidence Visibility (Priority: P3)

As a user, I want to see how confident the agent is in its classification
so that I know when to pay extra attention.

**Why this priority**: Transparency builds trust. Users should know when
the agent is uncertain.

**Independent Test**: Can be tested by verifying confidence scores are
displayed and low-confidence items are flagged.

**Acceptance Scenarios**:

1. **Given** a high-confidence classification (>=80%), **When** the user
   views the message, **Then** no special flag is shown.
2. **Given** a low-confidence classification (<50%), **When** the user
   views the message, **Then** a "Needs review" flag is displayed.

---

### Edge Cases

- What happens when the agent is unavailable? The message is classified
  as NORMAL (safe default) with status "pending".
- What happens when the message is empty or too short? The agent
  classifies as NORMAL with low confidence.
- What happens when the message is very long (10,000+ chars)? The agent
  analyzes the first 2000 characters and classifies based on that.
- What happens when the agent times out? The message is classified
  as NORMAL with status "pending".
- What happens when two priority signals conflict (deadline today but
  casual tone)? The agent uses the higher priority (deadline wins).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Agent MUST classify messages into exactly one of four
  levels: URGENT, IMPORTANT, NORMAL, LOW.
- **FR-002**: Agent MUST return a confidence score between 0.0 and 1.0
  for each classification.
- **FR-003**: Agent MUST provide a brief explanation for each
  classification (1-2 sentences).
- **FR-004**: Agent MUST complete analysis within 2 seconds for messages
  under 1000 characters.
- **FR-005**: Agent MUST default to NORMAL when uncertain or when
  analysis fails.
- **FR-006**: Agent MUST NOT classify messages as URGENT without explicit
  evidence of time pressure.
- **FR-007**: Users MUST be able to override any classification.
- **FR-008**: Agent MUST handle messages from any channel (WhatsApp,
  Gmail, Simulated) identically.

### Key Entities

- **Priority Classification**: The agent's output for a message.
  Key attributes: level (URGENT/IMPORTANT/NORMAL/LOW), confidence (0.0-1.0),
  explanation (string), analyzed_at (timestamp).
- **Message**: The input to the agent. Key attributes: content (string),
  sender (string), source (channel), timestamp.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Agent classifies messages correctly at least 80% of the
  time when measured against human judgment on a test set of 50 messages.
- **SC-002**: Agent completes analysis within 2 seconds for 95% of
  messages under 1000 characters.
- **SC-003**: Users can override classifications without errors 100%
  of the time.
- **SC-004**: Agent gracefully handles failures by defaulting to NORMAL
  100% of the time (no crashes or errors shown to user).
- **SC-005**: Low-confidence items (<50%) are correctly flagged as
  "Needs review" 100% of the time.

## Priority Level Definitions

### URGENT

Messages requiring immediate attention within hours.

**Evidence required** (must have at least one):
- Explicit time pressure: "right now", "immediately", "ASAP", "urgent"
- Deadline within 24 hours
- Clear consequence of delay: "client will leave", "system down"
- Request from direct authority (boss, manager)

**Examples**:
- "URGENT: Client demo in 2 hours, need the final presentation now!"
- "Server is down, all customers affected, need fix ASAP"

### IMPORTANT

Messages requiring attention within 1-3 days.

**Evidence required** (must have at least one):
- Deadline within 1-7 days
- Action required from the user
- Some consequence of delay (but not immediate/critical)

**Examples**:
- "Please send me the project report by Friday"
- "We have a meeting tomorrow at 3pm, please prepare slides"

### NORMAL

Messages requiring attention but not time-sensitive.

**Default classification when evidence is ambiguous.**

**Examples**:
- "Hey, want to grab lunch sometime this week?"
- "FYI, I updated the shared document"

### LOW

Messages requiring minimal or no immediate action.

**Evidence required** (must have at least one):
- No action required
- Automated/system message
- Informational only

**Examples**:
- "Your subscription has been renewed"
- "Weekly newsletter: Top 10 productivity tips"

## AI Behavior Rules

### What Agent MUST Do

- Analyze message content for explicit urgency signals
- Return exactly one priority level per message
- Include confidence score with every classification
- Include brief explanation for every classification
- Default to NORMAL when uncertain
- Handle failures gracefully (no crashes)

### What Agent MUST NOT Do

- Invent urgency that isn't present in the message
- Over-classify as URGENT to "be safe"
- Use sender identity alone to determine priority
- Block or delay message delivery while analyzing
- Modify the original message content
- Auto-respond or take action based on priority
- Return multiple priority levels for one message

## Non-Functional Requirements

### Performance

- Agent MUST complete analysis within 2 seconds for messages under
  1000 characters
- Agent MUST not block the message ingestion pipeline
- Agent MUST handle 100 concurrent analyses without degradation

### Reliability

- Agent MUST default to NORMAL on any failure
- Agent MUST log errors for debugging without exposing message content
- Agent MUST never crash or raise unhandled exceptions

### Security

- Agent MUST NOT log message content in plaintext
- Agent MUST NOT send message content to third parties
- Agent MUST process all analysis server-side

## Out of Scope (for this FYP)

- Learning from user overrides to improve accuracy
- Custom priority rules per user
- Priority-based auto-archiving
- Priority-based notification routing
- Multi-language priority detection
- Sentiment analysis (separate from priority)

## Assumptions

- Messages are in English (FYP scope)
- Single user system (no multi-tenant priority rules)
- LLM API is available for analysis
- Messages are under 10,000 characters
- Priority signals are explicit in the message content
