# Feature Specification: Day 18 – User Isolation

**Feature Branch**: `009-user-isolation`  
**Created**: 2026-08-25  
**Status**: Draft  
**Input**: User description: "Every message, task, and AI analysis must belong to a specific userId. User A must never see User B's data."

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Messages Are Private to Each User (Priority: P1)

As a registered user, I want to know that every message I send or receive
through the system belongs exclusively to me, so that I can trust the
system with sensitive communications without worrying about other users
seeing them.

**Why this priority**: Message isolation is the foundation of the entire
system. If messages leak between users, every other feature (tasks,
priority, dashboard) is compromised. This is the minimum viable security
guarantee.

**Independent Test**: Register two users (A and B). User A sends a
message via the simulate endpoint. User A sees it on their dashboard.
User B's dashboard shows zero messages from User A. Verified through
both the UI and direct API calls.

**Acceptance Scenarios**:

1. **Given** User A is logged in, **When** User A creates a message via
   `POST /messages`, **Then** the message is saved with User A's user
   ID and appears only on User A's dashboard.
2. **Given** User A and User B both have messages, **When** User B calls
   `GET /messages`, **Then** the response contains only User B's
   messages — zero messages from User A.
3. **Given** User A creates a message, **When** User B calls
   `GET /messages/{id}` with User A's message ID, **Then** the response
   is 404 — not 403, not a different error, but the same response as
   requesting a non-existent message.
4. **Given** User A creates a message, **When** User B calls
   `PUT /messages/{id}` with User A's message ID, **Then** the request
   is rejected and User A's message is unchanged.

---

### User Story 2 – Tasks Are Private to Each User (Priority: P1)

As a registered user, I want to know that tasks extracted from my
messages belong exclusively to me, so that my task list shows only my
action items and no one else's.

**Why this priority**: Tasks are derived from messages. If messages are
isolated but tasks are not, users would see each other's action items
— a privacy breach with real consequences (missing deadlines, seeing
sensitive task descriptions).

**Independent Test**: Register two users (A and B). User A sends a
message that contains an actionable task. User A sees the task on their
Tasks page. User B's Tasks page shows zero tasks from User A's message.
Verified through both the UI and direct API calls.

**Acceptance Scenarios**:

1. **Given** User A is logged in and sends a message with a task, **When**
   the AI analysis completes, **Then** the extracted task is saved with
   User A's user ID.
2. **Given** User A has extracted tasks, **When** User B calls
   `GET /tasks`, **Then** the response contains only User B's tasks.
3. **Given** User A has a task, **When** User B calls
   `PUT /tasks/{id}/status` with User A's task ID, **Then** the request
   is rejected and User A's task is unchanged.
4. **Given** User A has a task, **When** User B calls
   `DELETE /tasks/{id}` with User A's task ID, **Then** the request is
   rejected and User A's task is unchanged.

---

### User Story 3 – AI Analysis Stays With Its Owner (Priority: P1)

As a registered user, I want the AI analysis of my messages (priority,
summary, recommendations) to be visible only to me, so that the system's
intelligent features do not accidentally expose my communication content
to other users.

**Why this priority**: AI analysis is embedded inside message documents.
If message isolation works, analysis isolation is automatic. But this
story explicitly verifies that the analysis fields (priority, summary,
recommended action, tasks extracted) are never leaked through any API
response to another user.

**Independent Test**: Register two users (A and B). User A sends a
message. The AI analysis runs and produces a summary, priority, and
recommended action. User B calls `GET /messages` — the response contains
zero entries, so no analysis is visible. User B calls
`GET /messages/{id}` with User A's message ID — the response is 404.
Verified through direct API calls with captured response bodies.

**Acceptance Scenarios**:

1. **Given** User A sends a message and AI analysis completes, **When**
   User B calls `GET /messages`, **Then** the response contains no
   message documents from User A, and therefore no AI analysis data.
2. **Given** User A sends a message, **When** User B calls
   `GET /messages/{id}` with User A's message ID, **Then** the response
   is 404 and contains no AI analysis fields.

---

### User Story 4 – Webhook Messages Are Scoped to the Owner (Priority: P2)

As a registered user, I want messages arriving through webhooks
(WhatsApp, Gmail) to be automatically assigned to my account, so that
I do not have to manually route incoming messages.

**Why this priority**: Webhooks are the primary ingestion path for
real-world messages. If webhook messages are not scoped to the
authenticated user, the isolation guarantee is broken for the most
common use case.

**Independent Test**: User A authenticates a webhook. A message arrives
via the webhook. User A sees it on their dashboard. User B's dashboard
shows nothing. Verified through the UI and API.

**Acceptance Scenarios**:

1. **Given** User A is authenticated, **When** a message arrives via
   `POST /webhooks/whatsapp`, **Then** the message is saved with
   User A's user ID.
2. **Given** User A receives a webhook message, **When** User B calls
   `GET /messages`, **Then** User B sees zero messages from User A's
   webhook.

---

### User Story 5 – Dashboard Shows Only My Data (Priority: P2)

As a registered user, I want my dashboard to display only my messages,
tasks, and priorities, so that I can focus on my own communications
without seeing anyone else's.

**Why this priority**: The dashboard is the primary user-facing surface.
If it displays cross-user data, the isolation breach is immediately
visible and damaging.

**Independent Test**: Register two users with different messages and
tasks. Each user opens their dashboard. User A sees only A's data.
User B sees only B's data. Verified visually and through API responses.

**Acceptance Scenarios**:

1. **Given** User A is logged in, **When** User A loads `/dashboard`,
   **Then** every message card, task item, and priority indicator
   belongs exclusively to User A.
2. **Given** User B is logged in, **When** User B loads `/dashboard`,
   **Then** every message card, task item, and priority indicator
   belongs exclusively to User B.

---

### User Story 6 – Logout Clears All Cross-User State (Priority: P2)

As a user switching between accounts on a shared device, I want all my
data to be completely cleared from the browser when I log out, so that
the next user who logs in sees only their own data — never mine.

**Why this priority**: Stale client-side state after logout is a common
source of data leakage in single-page applications. This story ensures
the browser is clean between sessions.

**Independent Test**: User A logs in, views messages, then logs out.
User B logs in on the same browser. User B's dashboard shows zero
messages from User A. Verified through the UI after logout/login.

**Acceptance Scenarios**:

1. **Given** User A is logged in and has viewed messages, **When**
   User A logs out, **Then** all React state, URL parameters, and
   cached data are cleared from the browser.
2. **Given** User A logged out, **When** User B logs in on the same
   browser, **Then** User B's dashboard shows only User B's data —
   no stale messages, tasks, or analysis from User A.

---

### Edge Cases

- What happens if a message arrives via webhook while the user's session
  has expired? The system MUST reject the webhook with 401 — messages
  MUST NOT be stored without a valid user session.
- What happens if the AI analyzer creates tasks for a message but the
  user_id is missing from the message document? The system MUST skip
  task creation and log a warning — tasks MUST NOT be created without
  a user_id.
- What happens if a user guesses another user's message ID and tries to
  access it? The system MUST return 404 with no indication that the
  resource exists under another user.
- What happens if a database migration temporarily removes user_id from
  documents? The system MUST reject the migration — user_id MUST be
  present on every document at all times.
- What happens if two users have messages with the same sender name and
  content? Each user's message is independently owned — matching content
  does not create any relationship between the two.
- What happens if the frontend caches messages from User A and User A
  logs out, then User B logs in? The cache MUST be cleared on logout.
  Stale cached data is a breach.
- What happens if a bulk operation (e.g., mark all as read) is called
  without a user_id filter? The system MUST reject the operation — bulk
  operations MUST be scoped to the authenticated user.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every document in the `messages` collection MUST carry a
  `user_id` field set at creation time from the authenticated user's
  session.
- **FR-002**: Every document in the `tasks` collection MUST carry a
  `user_id` field set at creation time from the authenticated user's
  session.
- **FR-003**: When creating a message (via `POST /messages` or
  `POST /webhooks/whatsapp`), the system MUST set `user_id` to the
  authenticated user's ID — never from the request body.
- **FR-004**: When the AI analyzer extracts tasks from a message, the
  system MUST pass the message's `user_id` to the task documents. Tasks
  MUST NOT be created without a `user_id`.
- **FR-005**: Every `GET /messages` request MUST return only messages
  where `user_id` matches the authenticated user.
- **FR-006**: Every `GET /messages/{id}` request MUST return the
  message only if it belongs to the authenticated user. Otherwise, 404.
- **FR-007**: Every `PUT /messages/{id}` request MUST update the
  message only if it belongs to the authenticated user. Otherwise, 404.
- **FR-008**: Every `DELETE /messages/{id}` request MUST delete the
  message only if it belongs to the authenticated user. Otherwise, 404.
- **FR-009**: Every `GET /tasks` request MUST return only tasks where
  `user_id` matches the authenticated user.
- **FR-010**: Every `PUT /tasks/{id}/status` request MUST update the
  task only if it belongs to the authenticated user. Otherwise, 404.
- **FR-011**: Every `DELETE /tasks/{id}` request MUST delete the task
  only if it belongs to the authenticated user. Otherwise, 404.
- **FR-012**: The system MUST NOT return 403 for cross-user resource
  access. All cross-user access returns 404 to prevent confirming
  resource existence.
- **FR-013**: Error responses MUST NOT include another user's data,
  IDs, names, email addresses, or message content.
- **FR-014**: After logout, all client-side state (React state, URL
  params, browser caches) MUST be cleared before the next user's
  session begins.
- **FR-015**: The system MUST define an ownership model for every
  collection before the first write to it.
- **FR-016**: Webhook ingestion endpoints MUST resolve the owning user
  from server-side credentials — never from user-supplied query
  parameters or headers.
- **FR-017**: Bulk operations (mark all read, delete all) MUST be
  scoped to the authenticated user's `user_id`. Unscoped bulk
  operations are forbidden.

### Key Entities

- **User**: A registered account with name, email, and password hash.
  Owns all messages, tasks, and analyses. Identified by `_id`
  (ObjectId).
- **Message**: A communication from a channel (WhatsApp, Gmail,
  simulated). Owned by exactly one user via `user_id`. Contains
  embedded AI analysis (priority, summary, tasks, recommendations).
- **Task**: An actionable item extracted from a message. Owned by
  exactly one user via `user_id`. Linked to its source message via
  `source_message_id`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Registering two users and creating messages for each
  produces complete isolation — each user sees only their own messages
  through every API endpoint.
- **SC-002**: Registering two users and extracting tasks for each
  produces complete isolation — each user sees only their own tasks
  through every API endpoint.
- **SC-003**: Requesting another user's message or task by ID returns
  404 with a response body identical to requesting a non-existent
  resource.
- **SC-004**: AI analysis data (priority, summary, recommendation) is
  never visible to any user other than the message owner — verified
  through direct API calls with captured response bodies.
- **SC-005**: After logout and login as a different user, zero stale
  data from the previous user is visible in the browser.
- **SC-006**: Every database query in every API endpoint includes a
  `user_id` filter — verified by code review or automated audit.
- **SC-007**: No plaintext user data (emails, names, message content)
  appears in error logs visible to other users.
- **SC-008**: The two-user isolation test passes end-to-end: register
  A and B, create messages and tasks for each, verify complete
  separation through the UI and all API calls including guessed IDs.

## Data Ownership Rules

### Ownership Model

| Collection | Ownership Field | Set By | Filtered By |
|---|---|---|---|
| `users` | `_id` | System (registration) | N/A (identity) |
| `messages` | `user_id` | Server (route handler, from JWT) | Every query |
| `tasks` | `user_id` | Server (analyzer, from message) | Every query |

### Rules

1. The `user_id` field MUST be present on every document in `messages`
   and `tasks`. No exceptions.
2. The `user_id` MUST be set server-side from the verified JWT at the
   moment of document creation. It MUST NOT come from the request body.
3. Every database query in a request path MUST include a `user_id`
   filter as its first condition.
4. Bulk operations MUST apply `user_id` scope to prevent cross-user
   mutations.
5. Any new collection MUST define its ownership model before the first
   write.

## API Changes Required

### Messages

- `POST /messages`: No API change. The route already sets `user_id`
  from `current_user`. Verify it works correctly.
- `GET /messages`: No API change. The route already filters on
  `user_id`. Verify it returns only the user's messages.
- `GET /messages/{id}`: No API change. The route already includes
  `user_id` in the query. Verify cross-user access returns 404.
- `PUT /messages/{id}`: No API change. The route already includes
  `user_id` in the query. Verify cross-user updates return 404.
- `DELETE /messages/{id}`: No API change. The route already includes
  `user_id` in the query. Verify cross-user deletes return 404.

### Tasks

- `GET /tasks`: No API change. The route already filters on `user_id`.
  Verify it returns only the user's tasks.
- `PUT /tasks/{id}/status`: No API change. The route already includes
  `user_id` in the query. Verify cross-user updates return 404.
- `DELETE /tasks/{id}`: No API change. The route already includes
  `user_id` in the query. Verify cross-user deletes return 404.

### AI Analyzer

- **Critical fix required**: The `analyze_message()` function in the
  AI analyzer MUST receive the `user_id` from the message and pass it
  to extracted task documents. Currently, tasks are created without
  `user_id`, making them invisible to the owning user's task list.

### Database

- Add a MongoDB index on `messages.user_id` to support efficient
  per-user queries.
- Add a MongoDB index on `tasks.user_id` to support efficient
  per-user queries.

## Security Rules

1. **Deny by default.** Every resource is inaccessible until the
   authenticated user proves ownership.
2. **404 for cross-user access.** The system MUST return 404 — never
   403 — when a user requests another user's resource. The response
   body MUST be identical to requesting a non-existent resource.
3. **Server-side ownership.** The `user_id` is extracted from the
   verified JWT session. Client-supplied user IDs are never trusted.
4. **No data leakage in errors.** Error responses MUST NOT include
   another user's IDs, names, email addresses, or message content.
5. **No cross-user caching.** Client-side caches MUST be cleared on
   logout. Server-side caches MUST be scoped by `user_id`.
6. **No cross-user logs.** Log entries MUST NOT include another user's
   email, name, message content, or IDs.
7. **Webhook ownership.** Webhook endpoints MUST resolve the owning
   user from server-side credentials — never from user-supplied
   parameters.
8. **Bulk operation scoping.** All bulk operations (mark all read,
   delete all) MUST be scoped to the authenticated user.

## Assumptions

- Authentication (signup, login, JWT sessions, route protection) is
  already working and will not be modified by this feature.
- The existing `user_id` field on messages is correctly set by the
  route handlers. This has been verified in existing tests.
- The AI analyzer currently creates tasks without `user_id`. This is
  the primary bug to fix.
- MongoDB is the sole data store. No external caching layer (Redis)
  is in scope.
- The frontend already reads data from the authenticated user's
  session. No frontend data-fetching changes are required beyond
  ensuring logout clears all state.
