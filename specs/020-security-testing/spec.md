# Feature Specification: Security & Reliability Hardening

**Feature Branch**: `020-security-testing`  
**Created**: 2026-09-11  
**Status**: Draft  
**Input**: User description: "Create a clear and focused specification for Day 29 – Security + Testing."

## Feature Overview

All of the system's core features are built and working: authentication, messaging,
AI analysis, Gmail integration, the dashboard, and analytics. Day 29 does not add new
user-visible features. Instead, it hardens the system by verifying four critical
behaviors — proving they hold under attack and under failure — and fixing anything
that does not hold:

1. **Authentication & User Isolation** — a user can only ever see and use their own
   messages, tasks, and connections.
2. **Webhook Security** — invalid or unsigned webhook requests are rejected and never
   processed.
3. **AI Reliability** — if the AI service is unavailable or fails, the message is
   still saved safely and its analysis can be completed later; nothing is lost and
   nothing crashes.
4. **Duplicate Prevention** — the same message received twice results in a single
   stored copy, using a unique external message identifier to detect repeats.

**Success means**: After this phase, the system demonstrably rejects unauthorized
access, rejects bad webhook input at the door, survives AI failure without data loss,
and never creates duplicate messages — verified through a clear, repeatable test
suite.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A user sees only their own data (Priority: P1)

Two users, A and B, use the system. Each has their own messages, tasks, and connected
accounts. No matter what A tries — using the interface, calling the API directly, or
guessing the ID of B's records — A must never see, modify, or detect B's data.

**Why this priority**: Data isolation is the security invariant everything else
builds on. A single leak is a release-blocking defect and the fastest way to destroy
user trust.

**Independent Test**: Register users A and B. Create messages, tasks, and connections
for each. Verify A sees only A's data and B sees only B's data, through both the
interface and direct API calls — including attempts using guessed record IDs.

**Acceptance Scenarios**:

1. **Given** users A and B each have messages, tasks, and connections,
   **When** A requests any of B's records by exact or guessed ID,
   **Then** the request is denied in a way identical to "record not found" and never
   returns B's content.
2. **Given** A is signed in,
   **When** A lists messages, tasks, or connections,
   **Then** only A's records are returned, and counts total exactly A's data.
3. **Given** an API request that claims to belong to a different user,
   **When** the request is sent,
   **Then** the claimed identity is ignored and the authenticated user's identity is
   used instead.

---

### User Story 2 - Bad webhook requests are rejected (Priority: P1)

External channels deliver incoming messages through webhooks. Any request that is not
authenticated as coming from a trusted sender — missing signature, wrong signature,
or malformed content — is rejected outright and is never stored or analyzed.

**Why this priority**: Webhooks are an unauthenticated entry point into the system. If
an attacker can inject unverified payloads, they can poison the message stream,
bypass isolation, or flood storage — the next two stories protect against the
consequences.

**Independent Test**: Send webhook requests with (a) a valid signature and (b) an
invalid, missing, or tampered signature. Confirm only (a) is stored/processed.

**Acceptance Scenarios**:

1. **Given** a webhook request with an invalid, missing, or tampered signature,
   **When** it is received,
   **Then** it is rejected with an explicit error and no message is stored or analyzed.
2. **Given** a webhook request with a valid signature but a malformed payload,
   **When** it is received,
   **Then** it is rejected and no partial or empty message is stored.
3. **Given** a webhook request with a valid signature and well-formed payload,
   **When** it is received,
   **Then** it is accepted and processed normally.

---

### User Story 3 - The system survives AI failure without data loss (Priority: P2)

A message arrives while the AI analysis service is down, slow, or returning errors.
The message is still stored and visible to the user immediately. Its analysis is
marked as not yet available and is completed later, in the background, without the
user doing anything. Nothing is lost and nothing crashes.

**Why this priority**: Core value (storing and showing communications) already exists
without AI. Losing a message because an optional analysis service failed would
violate the principle that the system degrades gracefully, never destructively.

**Independent Test**: Simulate an AI failure at the moment a message arrives. Confirm
the message is stored and visible; then restore the AI and confirm the analysis is
later completed on the same stored message.

**Acceptance Scenarios**:

1. **Given** the AI service is unavailable,
   **When** a valid message arrives,
   **Then** the message is stored and visible immediately with analysis marked as not
   yet available; the request is acknowledged normally.
2. **Given** the analysis is marked not yet available,
   **When** the AI service becomes available again,
   **Then** the analysis for that same stored message is completed and updated in
   place, with no duplicate message created.
3. **Given** the AI service returns an error mid-analysis,
   **When** a message is being processed,
   **Then** the system does not crash, the stored message is not lost, and the
   analysis is retried later.

---

### User Story 4 - The same message is never stored twice (Priority: P2)

Messages can legitimately arrive more than once: a delivery retry, an overlap between
two polling cycles, or a replay. Each message carries a unique external identifier
recorded on first receipt; any repeat identified by that identifier is acknowledged
but not stored again.

**Why this priority**: Duplicates inflate the message list, double-count analytics,
and can trigger duplicate analysis and duplicate tasks — corrupting every feature
built on messages.

**Independent Test**: Deliver the same external message identifier twice (through any
channel or path). Confirm exactly one stored message exists and the second delivery
is acknowledged but skipped.

**Acceptance Scenarios**:

1. **Given** a message was already received and stored,
   **When** the same message (same external identifier) arrives again,
   **Then** exactly one stored copy exists and the repeat is acknowledged but not
   stored or re-analyzed.
2. **Given** two messages with the same external identifier arrive simultaneously,
   **When** both are processed,
   **Then** exactly one copy is stored (duplicate insertion is prevented, not just
   detected after the fact).
3. **Given** an analysis was retried after a failure,
   **When** the analysis is completed,
   **Then** it updates the one stored message rather than creating a new one.

---

### Edge Cases

- A webhook request with a valid signature but a valid signature for *old or
  expired* credentials — must be rejected, not processed.
- Two valid webhook deliveries for the same external identifier in quick
  succession — must produce one stored message, not two.
- A message with no external identifier at all (e.g., older or simulated data) —
  must still be stored exactly once using a deterministic server-derived identity,
  never silently duplicated.
- The AI service recovers between a failure and a retry — the pending analysis must
  complete on the existing message, not a copy.
- The AI service is slow rather than down — the user must still see the message
  immediately; the analysis completes when ready.
- A user requests another user's record that genuinely does not exist versus one
  that exists but is not theirs — both must be answered identically so existence is
  never revealed.
- Session expires mid-session (token missing, invalid, or expired) — subsequent
  requests fail closed (denied), with no degraded read-only access.

## Security Rules

1. **Every data request is scoped to the authenticated user.** All retrieval of
   messages, tasks, and connections is filtered by the authenticated user's identity.
   A user NEVER receives or modifies another user's data.
2. **User identity comes from the server session only.** Identity supplied in
   request bodies, query strings, or headers is ignored. The server's verified
   session is the single source of truth.
3. **"Not yours" is answered as "not found."** Requests for another user's records
   return the same result as requests for records that do not exist — no status or
   message ever reveals that a record exists but belongs to someone else.
4. **Webhook requests are authenticated before anything else.** Every webhook
   request must carry verifiable proof it comes from a trusted sender (a signature or
   secret issued to the sender, kept server-side and never exposed). Requests
   without such proof are rejected and never stored, analyzed, or partially processed.
5. **Malformed payloads are rejected, not guessed.** Webhook payloads that fail
   structural validation are rejected with an explicit error; the system does not
   attempt to salvage or partially process them.
6. **Failure always defaults to denial.** Missing, invalid, or expired credentials —
   for sessions and webhooks — result in explicit rejection. There is no fallback to
   unsigned access, degraded access, or silent acceptance.
7. **Secrets are never exposed.** Signing secrets and verification credentials are
   stored server-side only, never returned to browsers, visible in logs, or stored in
   plain text.

## Reliability Rules

1. **Store first, analyze later.** A valid incoming message is saved (with its owner,
   metadata, and external identifier) before any analysis is attempted. Analysis
   failure can never prevent storage.
2. **A message without analysis is still a message.** If analysis is not yet
   available, the message remains visible with a clearly-marked "analysis pending"
   status. It is not hidden, dropped, or turned into an error.
3. **Analysis is retried in the background.** When the AI service was unavailable or
   failed, analysis is retried later automatically. Retrying updates the already-
   stored message; it never inserts a second copy.
4. **The system never crashes on AI failure.** AI timeouts, errors, or malformed
   outputs are contained: the stored message is preserved, the failure is recorded,
   and processing continues without bringing down the surrounding system.
5. **No silent degradation.** "Pending analysis" and blocked processing are explicit
   and observable — to the user in the interface and in the stored record. A failure
   never masquerades as success.

## Test Cases & Expected Results

| # | Test Case | Expected Result |
|---|---|---|
| TC-01 | User A requests User B's message by exact ID | Denied, identical to "not found"; never yields B's content |
| TC-02 | User A attempts User B's record with a guessed ID | Denied, identical to "not found" |
| TC-03 | User A lists messages / tasks / connections | Only A's records; totals match exactly A's data |
| TC-04 | Request body claims to belong to another user | Claimed identity ignored; authenticated identity used |
| TC-05 | Webhook request with missing signature | Rejected; nothing stored or analyzed |
| TC-06 | Webhook request with invalid/tampered signature | Rejected; nothing stored or analyzed |
| TC-07 | Webhook request with valid signature, malformed payload | Rejected; no partial/empty message stored |
| TC-08 | Webhook request with valid signature, well-formed payload | Accepted and processed normally |
| TC-09 | Message arrives while AI service is down | Stored and visible immediately, analysis marked pending; acknowledged |
| TC-10 | AI restored after a failure | Pending analysis completes on the same stored message; no duplicate |
| TC-11 | AI returns an error mid-analysis | No crash; message preserved; analysis retried later |
| TC-12 | Same external identifier delivered twice | Exactly one stored message; repeat acknowledged but skipped |
| TC-13 | Same external identifier delivered concurrently | Exactly one stored copy; no duplicate insertion |
| TC-14 | Analysis retried after failure | One stored message updated in place; no new message |
| TC-15 | Message with no external identifier | Stored exactly once via a deterministic server-derived identity |

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST restrict every retrieval of messages, tasks, and
  connections to the authenticated user and never return another user's records.
- **FR-002**: System MUST ignore any user identity supplied in request bodies, query
  strings, or headers and derive identity from the verified server session only.
- **FR-003**: System MUST respond to requests for another user's records in a way
  indistinguishable from "record not found."
- **FR-004**: System MUST require verifiable proof of origin (e.g., a signature or
  secret issued to the sender) on every webhook delivery.
- **FR-005**: System MUST reject webhook requests whose proof of origin is missing,
  invalid, or tampered with, without storing or analyzing the payload.
- **FR-006**: System MUST reject webhook payloads that fail structural validation,
  without storing partial or empty messages.
- **FR-007**: System MUST store a valid incoming message before attempting any
  analysis, so analysis failure cannot prevent storage.
- **FR-008**: System MUST keep messages without complete analysis visible and clearly
  marked as pending analysis, never dropping or hiding them.
- **FR-009**: System MUST later complete pending analysis on the already-stored
  message, updating it in place, once analysis becomes possible again.
- **FR-010**: System MUST contain AI failures (timeouts, errors, malformed output) so
  they never crash the system or lose a stored message.
- **FR-011**: System MUST record a unique external identifier for every incoming
  message on first receipt and use it to detect repeated deliveries.
- **FR-012**: System MUST store only one copy of a message for a given external
  identifier, acknowledging but skipping repeats — including simultaneous deliveries.
- **FR-013**: System MUST store messages that lack an external identifier exactly
  once, using a deterministic server-derived identity.
- **FR-014**: System MUST mark pending-analysis and rejected-request states
  explicitly and observably, never silently.

### Key Entities *(include if feature involves data)*

- **User**: the account that owns data; the authenticated session is the only source
  of a user's identity.
- **Message**: one stored communication; carries its owner, metadata, and a unique
  external identifier (or a deterministic server-derived one) used to prevent
  duplicates and to track analysis state.
- **Analysis**: the AI result attached to a message — may be complete, pending
  (awaiting retry), or explicitly unavailable; only ever attached to the one stored
  message it belongs to.
- **Task / Connection**: user-owned records extracted or linked per user; subject to
  the same isolation guarantees as messages.
- **Webhook**: an external delivery into the system that must prove its origin before
  its payload is accepted.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of cross-user access attempts (direct and by guessed IDs across
  messages, tasks, and connections) are denied in a way indistinguishable from "not
  found."
- **SC-002**: 100% of webhook deliveries lacking valid proof of origin are rejected
  without storing or analyzing content.
- **SC-003**: 100% of valid messages arriving during an AI outage are stored and
  visible; 0 messages are lost or corrupted by the failure.
- **SC-004**: 100% of pending analyses are completed on their original stored message
  after AI recovery; 0 duplicate messages are created by retries.
- **SC-005**: Repeated delivery of the same external identifier produces exactly 1
  stored message in 100% of cases, including simultaneous deliveries.
- **SC-006**: No regression — the message flow, AI analysis, dashboard, inbox, tasks,
  connections, and analytics continue to work as they did before hardening.

## Assumptions

- Authentication via secure session (signed token) already exists and remains the
  mechanism used to establish the authenticated user; this phase verifies and
  enforces it, it does not replace it.
- Webhook delivery already involves a sender-issued secret/signature channel; this
  phase verifies the rejection rules and treats the scheme as an established domain
  concept.
- Duplicate prevention is enforced at both the application layer (check before
  insert) and the storage layer (unique constraint backing the external identifier),
  because application-only checks fail under simultaneous deliveries.
- "Retried later" means an automatic background retry; manual user retry is not in
  scope for this phase.
- Performance targets, retention, and error-message wording follow existing system
  conventions; this phase adds no new data retention or UX requirements beyond those
  already documented.
- This phase intentionally makes no changes to user-visible workflows — it is
  verification and enforcement of existing critical behaviors.