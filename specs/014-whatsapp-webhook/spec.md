# Feature Specification: Real WhatsApp Webhook (Day 23)

**Feature Branch**: `014-whatsapp-webhook`  
**Created**: 2026-08-28  
**Status**: Draft  
**Input**: User description: "Create a clear and focused specification for Day 23 – Real WhatsApp Webhook"

## Feature Overview

Day 23 converts the verified webhook from Day 22 research into a real
ingestion pipeline. Today a message sent to the WhatsApp Business test number
is only logged; after this feature it flows all the way to the Dashboard with
full AI analysis — the same journey a simulated message takes today.

The core principle is **source-agnosticity**: every channel (whatsapp,
simulate, future providers) is translated at the ingestion boundary into one
canonical message format. Neither the AI pipeline, the storage layer, nor the
Dashboard ever cares where a message came from.

**Goal**: When a real WhatsApp message is sent to the test number, it should:

1. Arrive at our webhook
2. Be validated
3. Be converted into a normalized format
4. Be saved in MongoDB
5. Go through the AI pipeline
6. Appear on the Dashboard

**Out of scope for Day 23**: sending/auto-replying to messages, reading
personal WhatsApp accounts, and connecting multiple users' WhatsApp numbers.
Day 23 makes the existing single test number receive real messages
end-to-end.

## Incoming Message Flow

A WhatsApp message moves through the system in one direction:

```text
WhatsApp (sender's phone)
  ↓  message sent to Business number
Webhook delivery from Meta Cloud API
  ↓  1. Verify provider signature
  ↓  2. Validate payload structure
  ↓  3. Extract message + normalize
  ↓  4. Deduplicate (by externalMessageId)
  ↓  5. Persist under the correct owning user
  ↓  6. Acknowledge quickly
AI Pipeline (async, off the request path)
  ↓  priority · summary · tasks · deadlines · recommendation
Dashboard
  ↓  reads stored data only — never re-runs the pipeline or webhook
```

The acknowledgement in step 6 MUST happen before any heavy processing so the
provider does not retry the same delivery (retries cause duplicates — handled
by step 4, but avoided in the first place).

## Normalized Message Format

This is the single canonical shape for every ingested message. All channels
produce it; nothing downstream reads provider-specific payloads.

```json
{
  "userId": "demo-user-id",
  "source": "whatsapp",
  "sender": "Ali",
  "content": "Send me the slides tonight.",
  "receivedAt": "2026-08-28T09:41:00Z",
  "externalMessageId": "wamid.ABC123..."
}
```

| Field | Meaning | Rules |
|---|---|---|
| `userId` | Owning user | Set server-side from verified connection credentials — never from request-supplied input |
| `source` | Channel enum | `whatsapp` for this feature; `simulate` for the fake endpoint; new channels added explicitly |
| `sender` | Human-readable name | Use the sender profile name when available, otherwise the phone number |
| `content` | Message text | Text messages carry their text; media-only messages carry an empty string and a media flag |
| `receivedAt` | Receive time | Server time in UTC ISO-8601, not the sender-reported timestamp |
| `externalMessageId` | Provider message ID | The deduplication key; no two stored messages share one |

## Validation Rules

1. **Signature first.** Every delivery MUST be verified using the provider's
   signature mechanism (Meta's `X-Hub-Signature-256`). Deliveries with
   missing or invalid signatures are rejected before any parsing or storage.
2. **Structure before trust.** The payload MUST match the expected provider
   structure before any field is read. Malformed payloads are rejected and
   never stored.
3. **Message events only.** Payloads containing non-message events (delivery
   receipts, status updates, errors, or empty notifications) MUST be
   acknowledged but not stored or analyzed.
4. **Deduplicate by `externalMessageId`.** The same message delivered twice
   MUST produce exactly one stored record.
5. **Acknowledge fast, process later.** The webhook responds to the provider
   promptly; the AI pipeline runs afterward, off the request path.
6. **Never trust client-supplied identity.** The owning user is resolved
   server-side only.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Real WhatsApp Message Reaches the Dashboard (Priority: P1)

As a user, when I send a WhatsApp message to the test number, the message
appears on my Dashboard with full AI analysis — with no manual step in
between.

**Why this priority**: This is the entire point of the feature. Everything
else (validation, dedup, attribution) serves this one journey.

**Independent Test**: Can be fully tested by sending a message to the
Business number and confirming a dashboard card appears with the correct
source, sender, content, and AI fields within 30 seconds.

**Acceptance Scenarios**:

1. **Given** the webhook is verified and the test number is connected,
   **When** a message is sent to the number, **Then** the system receives,
   validates, normalizes, and stores the message.
2. **Given** a stored normalized message, **When** the AI pipeline runs,
   **Then** the message receives priority, summary, task, deadline, and
   recommendation analysis.
3. **Given** a fully analyzed message, **When** I open the Dashboard,
   **Then** the message card is visible with source "WhatsApp", the sender's
   name, the message content, and the AI fields.

---

### User Story 2 - Incoming Deliveries Are Verified Before Processing (Priority: P1)

As a user, I want every incoming webhook delivery to be authenticated and
validated so that no unverified or malformed request ever lands in my data.

**Why this priority**: This is the security gate. It is non-negotiable and
must exist for real ingestion to be safe.

**Independent Test**: Can be tested by (a) completing the provider's webhook
verification challenge successfully, and (b) sending requests with missing or
wrong signatures and confirming they are rejected with nothing stored.

**Acceptance Scenarios**:

1. **Given** the webhook is configured, **When** the provider sends its
   verification challenge, **Then** the system responds correctly and the
   provider portal confirms verification.
2. **Given** an incoming delivery, **When** the signature is missing or
   invalid, **Then** the delivery is rejected and no data is stored.
3. **Given** an incoming delivery, **When** the payload is malformed or not
   a message event, **Then** it is acknowledged without storing or analyzing
   anything, and previously stored messages are unaffected.

---

### User Story 3 - Normalized Format and Simulation Parity (Priority: P2)

As a user, I want real and simulated messages to be indistinguishable so the
AI and Dashboard treat every channel alike, and I want the existing simulate
feature to keep working.

**Why this priority**: Parity proves the normalization principle works and
guards against regression of a working feature.

**Independent Test**: Can be tested by sending one simulated and one real
message with the same text and confirming both produce identical dashboard
cards, and that the simulate flow still works on its own.

**Acceptance Scenarios**:

1. **Given** a simulated message and a real message with the same text,
   **When** both are processed, **Then** both produce identical dashboard
   cards with the same AI analysis.
2. **Given** the existing simulation endpoint, **When** a message is sent
   through it, **Then** it still reaches the Dashboard exactly as before this
   feature (no regression).

---

### User Story 4 - Duplicate Deliveries Produce No Duplicate Records (Priority: P2)

As a user, I want the system to be safe against duplicate deliveries so my
Dashboard never shows the same message twice.

**Why this priority**: Providers redeliver events when they suspect a
timeout. Without deduplication, a single WhatsApp message could appear
several times.

**Independent Test**: Can be tested by delivering the same message payload
twice (simulating a provider retry) and confirming only one record exists
and the AI pipeline is not re-run.

**Acceptance Scenarios**:

1. **Given** a message already stored, **When** the same message is
   delivered again, **Then** the duplicate is acknowledged but not stored.
2. **Given** a duplicate delivery, **When** it is processed, **Then** the AI
   pipeline is not re-run for it and no duplicate dashboard card appears.

---

### User Story 5 - Messages Land Under the Correct User (Priority: P2)

As a user, I want every ingested message to belong to my account and be
invisible to everyone else.

**Why this priority**: Attribution completes the connection between the
webhook and the multi-user system. It is a security invariant, not a
convenience.

**Independent Test**: Can be tested by ingesting a message through the
webhook and confirming from a second account that it is not visible.

**Acceptance Scenarios**:

1. **Given** a webhook message for an owned number, **When** it is stored,
   **Then** it is associated with the correct owning user via server-side
   resolution.
2. **Given** two user accounts, **When** either user views messages, **Then**
   each sees only their own messages — the webhook message never appears
   under the other account.

### Edge Cases

- **Duplicate delivery (provider retry)**: Same `externalMessageId` redelivered
  → acknowledged, not stored, not re-analyzed.
- **Invalid or missing signature**: Rejected before parsing; nothing stored.
- **Malformed payload**: Rejected cleanly; previously stored data unaffected.
- **Verification challenge failure**: Wrong or missing verify token → the
  challenge is not echoed and the portal stays unverified.
- **Non-message events**: Delivery receipts, status updates, and empty
  notifications are acknowledged and ignored.
- **Batched payloads**: One delivery containing several messages → every
  message is extracted and processed; one acknowledgement covers the batch.
- **Media-only messages** (image, audio, document, video): Stored with empty
  content and a media flag; never dropped.
- **Unknown sender without a profile name**: Stored with the phone number as
  the sender.
- **Provider sends the number's phone number ID that differs from ours**:
  Payload is ignored (not ours) unless it matches the configured number.
- **ngrok tunnel is down when a message is sent**: Meta retries delivery; the
  deduplication rule makes eventual delivery safe.
- **Very long message**: Stored in full; no truncation.
- **Message arrives with no resolvable owning user**: Not stored; the
  delivery is acknowledged so the provider does not retry forever.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST respond correctly to the provider's webhook
  verification challenge (subscribe mode + matching verify token) by echoing
  the challenge back.
- **FR-002**: System MUST verify the signature of every incoming delivery and
  reject deliveries with invalid or missing signatures before any other
  processing.
- **FR-003**: System MUST validate the structure of every payload before
  processing; malformed payloads MUST be rejected without storing data.
- **FR-004**: System MUST extract each text message from a delivery and
  convert it to the normalized message format (`userId`, `source`, `sender`,
  `content`, `receivedAt`, `externalMessageId`).
- **FR-005**: System MUST set `source` to `whatsapp` for webhook-derived
  messages.
- **FR-006**: System MUST prevent duplicate records by keying on
  `externalMessageId`; redelivered messages MUST be acknowledged but not
  stored or re-analyzed.
- **FR-007**: System MUST persist each normalized message under the correct
  owning user, resolved server-side from verified connection credentials.
- **FR-008**: System MUST NOT derive user identity from any request-supplied
  input (query parameters, headers, or body fields).
- **FR-009**: System MUST route every stored normalized message through the
  same AI pipeline as simulated messages (priority, summary, tasks,
  deadlines, recommendation).
- **FR-010**: System MUST make ingested messages appear on the Dashboard
  without any manual action by the user.
- **FR-011**: System MUST keep the simulation feature working through the
  same normalized ingest path (no regression).
- **FR-012**: System MUST store media-only messages with empty content and a
  media marker instead of dropping them.
- **FR-013**: System MUST acknowledge valid deliveries promptly and run the
  AI pipeline after acknowledging, keeping the delivery response fast.
- **FR-014**: System MUST acknowledge and ignore non-message events
  (delivery receipts, status updates, errors) without storing them.
- **FR-015**: System MUST NOT send, broadcast, or auto-reply to any message.

### Key Entities

- **Webhook Delivery**: An incoming provider event containing zero or more
  messages plus non-message events. Key attributes: signature, payload
  structure, message events, phone number identifier.
- **Normalized Message**: The canonical communication record shared by all
  channels. Key attributes: `userId`, `source`, `sender`, `content`,
  `receivedAt`, `externalMessageId`. Maps directly onto the existing message
  record consumed by the AI pipeline and Dashboard.
- **Messaging Connection**: The server-side mapping that resolves a WhatsApp
  Business number to its owning user (already established in the connection
  architecture).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A real message sent to the Business number appears on the
  Dashboard with source, sender, content, and full AI analysis within 30
  seconds of being sent.
- **SC-002**: Simulated messages continue to reach the Dashboard exactly as
  before — the simulate flow has zero regressions.
- **SC-003**: Delivering the same message event twice produces exactly one
  Dashboard card and one pipeline run — zero duplicates.
- **SC-004**: Zero deliveries with missing or invalid signatures are stored
  (100% of unverified deliveries rejected).
- **SC-005**: 100% of successfully ingested messages belong to the correct
  owning user and are invisible to all other users.
- **SC-006**: Media-only messages are never lost; each appears as a
  media-marked card.
- **SC-007**: The provider's delivery acknowledgement is returned fast
  enough that no portal configuration change is needed to keep receiving
  messages.
- **SC-008**: Real and simulated messages with the same text produce
  identical Dashboard cards and AI analysis.

## Assumptions

- The Day 22 setup is active: Meta app, test number, ngrok tunnel, and a
  verified webhook endpoint.
- The webhook verification challenge (Day 22) remains in place and is
  retained, not replaced.
- Day 23 keeps a single WhatsApp Business number owned by the demo account;
  personal multi-user WhatsApp connections remain future work.
- The server-side connection mapping decides ownership; for this FYP the
  test number maps to the demo user.
- Receiving is in scope; sending is not, so the temporary access token from
  Day 22 is sufficient.
- Meta may redeliver events, batch multiple messages in one delivery, or send
  non-message events; all are handled gracefully.
- The provider's free test-message quota is sufficient for manual testing.

## Out of Scope

- Sending, broadcasting, or auto-replying to messages
- Reading or connecting personal WhatsApp accounts
- Multi-user WhatsApp number connections (beyond the single demo number)
- Webhook payload encryption
- Production deployment (removing the ngrok dependency)
- Long-lived token management beyond what receiving requires