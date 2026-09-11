# Feature Specification: Day 26 Gmail Integration

**Feature Branch**: `017-gmail-integration`  
**Created**: 2026-09-10  
**Status**: Draft  
**Input**: User description: "Connect Gmail using official Google OAuth so new emails can be received and processed by the AI system."

## Feature Overview

Communication AI currently receives messages through WhatsApp (simulated and
real webhook). This feature adds a second real communication channel: Gmail.

Users connect their Gmail account through Google's official OAuth 2.0 flow —
**never by entering their Gmail password**. Once connected, new emails are
fetched, converted into the same normalized message format used by WhatsApp,
and processed by the existing AI pipeline (priority, summary, tasks,
deadlines, recommended action). The results appear on the dashboard and
inbox alongside WhatsApp messages, with no difference in treatment.

The connection is visible and manageable on the Connections page, and each
connection is strictly owned by the logged-in user who created it.

**Success means**: A user clicks "Connect Gmail", grants permission on
Google's screen, and new emails arriving in their Gmail start appearing on
their dashboard as fully analyzed message cards — indistinguishable in
treatment from their WhatsApp messages.

## User Scenarios & Testing *(mandatory)*

Each user story is an independent slice that can be implemented, tested, and
demonstrated on its own.

### User Story 1 - Connect Gmail via Google OAuth (Priority: P1)

A logged-in user opens the Connections page and clicks "Connect Gmail".
The system redirects them to Google's official permission screen. The user
approves the requested access and is returned to the app, where their
Connection now shows "Connected" for Gmail.

**Why this priority**: Without a working connection, no emails can be
received. This is the foundation of the entire feature.

**Independent Test**: Can be fully tested by clicking "Connect Gmail",
selecting a Gmail account on Google's consent screen, granting access, and
verifying the Connections page shows "Connected". Delivers account linking
as an MVP.

**Acceptance Scenarios**:

1. **Given** the user is logged in and on the Connections page, **When** they
   click "Connect Gmail", **Then** they are redirected to Google's official
   consent screen (never a password prompt from our app).
2. **Given** the user is on Google's consent screen, **When** they grant
   access, **Then** they are returned to the app and the Gmail connection
   status is "Connected".
3. **Given** the user is on Google's consent screen, **When** they cancel or
   deny access, **Then** they are returned to the app with connection status
   unchanged and no error is shown.

---

### User Story 2 - Receive New Emails as Normalized Messages (Priority: P2)

After connecting, and without any further action from the user, new emails
arriving in the connected Gmail account are received, converted into the
normalized message format, processed by the AI pipeline, and shown on the
dashboard and inbox as message cards.

**Why this priority**: This is the core value — emails become actionable,
prioritized messages in the user's unified communication view.

**Independent Test**: Can be fully tested by sending a real email to the
connected Gmail account and verifying it appears on the dashboard with AI
analysis (priority, tasks) in the same format as WhatsApp messages.

**Acceptance Scenarios**:

1. **Given** a user with an active Gmail connection, **When** a new email
   arrives in their Gmail, **Then** it appears on their dashboard as a
   message card with source "Gmail" within 5 minutes.
2. **Given** a new email is received, **When** it is processed, **Then** its
   content, sender, subject, and timestamp match the email — nothing
   invented.
3. **Given** the same email is detected more than once (e.g., overlapping
   checks), **When** processing runs, **Then** only one message card is
   created (no duplicates).
4. **Given** a Gmail email and a WhatsApp message, **When** both are
   processed, **Then** they produce cards in the same format, filterable by
   source.

---

### User Story 3 - Manage Connection Status and Disconnect (Priority: P3)

A user can see the current status of their Gmail connection on the
Connections page, and can disconnect at any time. Disconnecting removes the
app's access: the stored credentials are deleted and Google is told to
revoke the granted access. Reconnecting later starts a fresh OAuth flow.

**Why this priority**: User control over connections (Principle IV) is
required for a trustworthy system; status visibility lets users know when
something needs attention.

**Independent Test**: Can be fully tested by disconnecting a connected Gmail
account and verifying the status changes to "Disconnected", no new emails
arrive afterward, and reconnecting requires a new Google grant.

**Acceptance Scenarios**:

1. **Given** the user has a connected Gmail, **When** they click
   "Disconnect", **Then** the status changes to "Disconnected" and no new
   emails are received from that account afterward.
2. **Given** a disconnected Gmail connection, **When** the user clicks
   "Connect Gmail", **Then** they go through Google's consent screen again
   (the previous grant is not reused).
3. **Given** the connection is in an error state (e.g., access was revoked
   in Google settings), **When** the user views the Connections page,
   **Then** they see a clear error status and a way to reconnect.

---

### Edge Cases

- **OAuth flow cancelled/denied**: The user closes Google's screen or clicks
  "Deny". The connection stays in its previous state; a friendly message
  explains nothing was connected.
- **OAuth error responses**: Google returns an error (e.g., `access_denied`).
  The system shows a human-readable message; no raw error is exposed.
- **Expired or revoked token**: Google access is revoked by the user in
  Google settings, or the refresh token stops working. The connection
  transitions to an error state and prompts reconnection — it never crashes
  or silently stops.
- **Duplicate email detection**: The same email is seen more than once.
  Only one message is created (keyed on the email's unique identifier).
- **Email with no body text**: An email whose body is empty or only images.
  A message with empty content is still stored and shown (media-like), never
  dropped.
- **Email with only HTML body**: The visible text is extracted for the
  normalized content; markup is not stored.
- **Email with attachments**: The email is processed normally; the
  attachment itself is ignored for this feature (body text only).
- **No new emails**: While connected, if no new emails arrive, the system
  stays idle and shows no spurious messages.
- **Reconnect after disconnect**: Reconnecting runs a fresh OAuth flow and
  does not reuse the old, revoked credentials.
- **Two users, same Gmail account**: Each user connects and manages their
  own connection independently; neither can see the other's connection or
  emails.
- **Gmail service outage / temporary API failure**: Fetching fails
  gracefully; previously received messages remain visible and nothing
  breaks. Retrying after the outage works.
- **Rate limiting**: If Google limits request volume, the system backs off
  and resumes later without losing the connection.
- **Email arrives during the OAuth step**: A new email that arrives while the
  user is still granting access is picked up normally once connected.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST let a logged-in user connect a Gmail account using
  Google's official OAuth 2.0 flow; the system MUST NEVER ask for or accept
  a Gmail password.
- **FR-002**: System MUST redirect the user to Google's official consent
  screen and request only read access to emails (no send/modify
  permissions).
- **FR-003**: System MUST receive the OAuth authorization result, exchange
  it server-side for access and refresh tokens, and store both securely
  (encrypted at rest), never exposing them to the frontend, browser storage,
  or API responses.
- **FR-004**: Every Gmail connection MUST be associated with exactly one
  user, set server-side from the authenticated session; users see and manage
  only their own connection.
- **FR-005**: System MUST automatically detect new emails in the connected
  Gmail account and convert each into the normalized message format used by
  WhatsApp (`userId`, `source`, `sender`, `content`, `receivedAt`,
  `externalMessageId`, plus an optional subject).
- **FR-006**: System MUST ensure duplicate detection of the same email
  produces zero duplicate messages (uniqueness keyed on the email's
  provider message identifier).
- **FR-007**: System MUST run normalized Gmail emails through the same AI
  pipeline as WhatsApp messages, producing equivalent analysis stored in the
  same way.
- **FR-008**: System MUST show Gmail emails on the dashboard and inbox
  alongside WhatsApp messages, filterable by source, with the same card
  formatting rules.
- **FR-009**: System MUST show Gmail connection status on the Connections
  page (Connected / Disconnected / Error) with Connect and Disconnect
  actions.
- **FR-010**: System MUST automatically refresh expired access tokens using
  the stored refresh token, without user intervention.
- **FR-011**: When a user disconnects, System MUST revoke the Google access
  and delete all stored tokens for that connection.
- **FR-012**: System MUST keep Gmail-derived data isolated per user: requests
  for another user's connection or email return the same response as a
  non-existent resource.

### Key Entities *(include if feature involves data)*

- **Gmail Connection**: Represents one user's link to their Gmail account.
  Carries the owning user, connection status, and the securely stored access
  and refresh tokens. Created at first connection, updated on refresh or
  disconnect, deleted on disconnect.
- **Message**: The canonical, channel-agnostic record produced from an email
  (same shape as WhatsApp messages) so the AI pipeline, database, and
  dashboard never distinguish channels.

### OAuth Flow Steps

```text
1. User clicks "Connect Gmail" (Connections page)
2. System redirects to Google's official consent screen
   (read-only email scope; app never asks for a password)
3. User grants permission on Google's screen
4. Google redirects back to the system with an authorization code
5. System exchanges the code for an access token + refresh token (server-side)
6. Tokens are encrypted and stored, linked to the logged-in user
7. Connection status becomes "Connected"
8. From here, new emails are detected, normalized, and processed automatically
```

### Normalized Email Format

A Gmail email MUST be converted into the same canonical message record used
by WhatsApp before storage, processing, or display:

```json
{
  "userId": "64a1f2...",
  "source": "gmail",
  "sender": "teacher@example.com",
  "content": "Please submit the report.",
  "receivedAt": "2026-09-10T09:41:00Z",
  "externalMessageId": "1856f2d3...",
  "subject": "Project Submission"
}
```

Format rules:

1. `source` is the value `gmail` (an enum, never free text).
2. `sender` is human-readable — the sender's display name when available,
   otherwise the email address.
3. `content` is the email's visible text; empty body → empty string, never
   null, and the email is never dropped.
4. `receivedAt` is the system's UTC timestamp for when the email was
   detected.
5. `externalMessageId` is the email's unique provider identifier and keys
   duplicate prevention.
6. `userId` is set server-side from the authenticated session, never from
   request data.
7. `subject` is optional and Gmail-specific; the dashboard may show it when
   present.

### Security Rules

1. **OAuth only, no passwords.** The system MUST use Google's official
   OAuth 2.0 flow exclusively. Asking for, accepting, storing, or logging a
   Gmail password is forbidden.
2. **Least-privilege scope.** Only read access to emails is requested. Send,
   modify, or full-account scopes are forbidden for this feature.
3. **Encrypted at rest.** Access and refresh tokens MUST be encrypted before
   storage. Plaintext tokens in the database, logs, or code are blocking
   violations.
4. **Backend-only handling.** Token exchange, refresh, and all email access
   happen server-side. Tokens never appear in API responses, browser
   storage, URL parameters, or developer tools.
5. **Explicit consent.** The user MUST grant access on Google's official
   consent screen; access obtained without it is invalid.
6. **Server-side ownership.** `userId` always comes from the authenticated
   session; client-supplied user or user IDs are never trusted.
7. **Clean revocation.** Disconnecting revokes Google access and deletes all
   stored tokens for that connection.
8. **Receive-only.** The system reads emails; it never sends, replies,
   drafts, edits, or deletes emails in the user's mailbox.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user completes the Gmail connection flow (click through
  Google consent to "Connected") in under 2 minutes.
- **SC-002**: 100% of new emails arriving in a connected Gmail account
  appear on the dashboard; a new email is reflected within 5 minutes of
  arrival.
- **SC-003**: Zero duplicate message cards are produced when the same email
  is detected multiple times.
- **SC-004**: 100% of stored Gmail credentials are encrypted; zero tokens
  are visible in any user-facing interface, response, or developer tools.
- **SC-005**: Two-user isolation holds for Gmail: User A sees only A's
  Gmail connection and emails; User B sees only B's — verified through both
  the UI and direct requests for another user's resource.
- **SC-006**: Gmail emails produce dashboard cards identical in format and
  treatment to WhatsApp messages, distinguishable only by channel/source.
- **SC-007**: Disconnecting removes Google access and stored credentials
  within 1 minute, and no new emails arrive afterward.
- **SC-008**: Existing WhatsApp and simulated message flows continue to work
  exactly as before (no regression).

### Assumptions

- Only **new** emails arriving after connection are ingested; existing inbox
  history/backfill is out of scope.
- One Gmail connection per user is supported for this day (connecting again
  replaces or re-establishes that user's connection).
- Automatic detection of new emails is expected to run periodically; exact
  detection interval and mechanism are planning/implementation decisions as
  long as the "within 5 minutes" outcome is met.
- Body text is used for analysis; attachments are not processed.
- No sending, replying, editing, or deleting emails in Gmail.

### Out of Scope for This Day

- Sending, replying, or drafting emails
- Processing email attachments (content, previews, downloads)
- Ingesting historical/existing emails (backfill)
- Multiple Gmail accounts per user, or multiple Google providers (Workspace,
  other Google services)
- Gmail labels, categories, stars, or folder structures
- Editing, starring, archiving, or deleting emails in Gmail
- Cross-user email analytics or shared mailboxes