# Feature Specification: User Authentication & Multi-User System

**Feature Branch**: `007-user-auth`  
**Created**: 2026-08-21  
**Status**: Draft  
**Input**: User description: "Create a clear and focused specification for
Week 3 – Authentication (starting with Day 15 – Signup). Context: Project
Communication AI; AI Pipeline already working; now make it a real
multi-user application. Day 15 – Signup: /signup page (Name, Email,
Password, Confirm Password), POST /auth/register, securely hashed
passwords, basic validation. Week 3 goals: register and login, JWT or
secure cookie-based authentication, protected routes, strong user
isolation, every message and task belongs to a specific user."

## Feature Overview

Turn Communication AI from a single-user prototype into a real multi-user
application. Each person registers an account, logs in, and sees ONLY
their own messages, tasks, and analysis results. The AI pipeline built in
Weeks 1–2 keeps working exactly as today — authentication adds the
question "whose data is this?" to every read and write.

Day 15 delivers the entry point: a working signup page and registration
endpoint with securely stored passwords. The remaining days add login,
session handling, and locked-down routes.

**Success means**: Two people can use the system at the same time and
neither can see, modify, or even detect the other's data — while
everything they DO own works exactly as it did before.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Sign Up for an Account (Priority: P1)

As a new visitor, I want to create an account by providing my name, email,
and a password (confirmed by re-typing it), so that I get my own private
workspace inside the application.

**Why this priority**: This is the Day 15 deliverable and the entry point
for every other story — nothing else in Week 3 can be demonstrated
without registered users.

**Independent Test**: Can be fully tested by opening /signup, submitting
valid details, and verifying the account is created with a usable
credential and the user lands in their (empty) workspace.

**Acceptance Scenarios**:

1. **Given** I am on the signup page, **When** I submit a valid name,
   valid email, and matching passwords of sufficient length, **Then** my
   account is created, I am signed in automatically, and I see my
   workspace with zero messages and zero tasks.
2. **Given** I am on the signup page, **When** I submit a password and a
   different confirm-password value, **Then** my submission is rejected
   and I am told the passwords do not match — nothing is created.
3. **Given** I am on the signup page, **When** I submit a password
   shorter than the minimum length, **Then** my submission is rejected
   with a specific message stating the minimum requirement.
4. **Given** an account already exists for an email address, **When** I
   try to sign up again with that email, **Then** my submission is
   rejected with a clear message that this email is already registered.
5. **Given** I am on the signup page, **When** I submit an invalid email
   format or leave any field empty, **Then** my submission is rejected
   and the specific problem is identified next to the offending field.

---

### User Story 2 - Log In to My Account (Priority: P2)

As a returning user, I want to log in with my email and password, so that
I regain access to my own messages and tasks from any browser session.

**Why this priority**: Login converts a one-time registration into a
reusable identity; every later story (protected routes, isolation)
depends on being able to establish who the current user is.

**Independent Test**: Can be fully tested by registering a user, logging
out (or using a fresh browser session), and logging back in with the same
credentials.

**Acceptance Scenarios**:

1. **Given** I have a registered account, **When** I log in with the
   correct email and password, **Then** I am signed in and see MY
   dashboard with MY data.
2. **Given** I am on the login page, **When** I submit a wrong password
   for an existing email, **Then** I see one generic error ("Invalid
   email or password") that does not reveal whether the email exists.
3. **Given** I am on the login page, **When** I submit an email that was
   never registered, **Then** I see the same generic error as a wrong
   password.
4. **Given** I am signed in, **When** I close the browser and return
   within the session lifetime, **Then** I am still signed in and do not
   need to log in again.

---

### User Story 3 - Strong User Isolation (Priority: P3)

As a user, I want an absolute guarantee that no other user can ever see,
modify, or detect my messages and tasks, so that I can trust the system
with real, private communications.

**Why this priority**: Ranked below Signup/Login only because those must
exist first; in importance it is the highest-stakes guarantee of Week 3 —
an isolation failure is a critical security defect, not a cosmetic bug.

**Independent Test**: Can be fully tested by registering two users A and
B, having each send messages, then verifying through BOTH the UI and
directly-crafted requests that B sees zero of A's records — including
when guessing record identifiers.

**Acceptance Scenarios**:

1. **Given** users A and B are registered and each has received
   messages, **When** B opens any page or list, **Then** B sees only
   B's messages and tasks — none of A's records appear anywhere.
2. **Given** user A's record identifier is known to B, **When** B
   requests that specific record directly, **Then** the system responds
   as if the record does not exist (not found) and reveals no content.
3. **Given** user B attempts any action on A's data (read, update,
   delete), **When** the request completes, **Then** A's data is
   unchanged and B receives an error or not-found response.
4. **Given** a new message arrives for user A, **When** the AI pipeline
   processes it, **Then** the resulting analysis and extracted tasks
   belong to A alone and never appear in B's views.

---

### User Story 4 - Protected Access (Priority: P4)

As a system, I want every page and data endpoint locked behind login, so
that an anonymous visitor can never reach anyone's workspace — including
by typing a URL directly.

**Why this priority**: Delivered after the identity stories because it
consumes them, but it is what makes the previous stories enforceable in
practice.

**Independent Test**: Can be fully tested by logging out and attempting
to reach each known page URL and data endpoint directly, verifying every
attempt is redirected or rejected.

**Acceptance Scenarios**:

1. **Given** I am not signed in, **When** I type the URL of any
   workspace page (dashboard, inbox, tasks, attention, connections,
   settings), **Then** I am redirected to the login page instead of
   seeing the page.
2. **Given** I am not signed in, **When** any data endpoint is called
   without credentials, **Then** it responds with an unauthorized error
   and returns no data.
3. **Given** I am signed in and I log out, **When** I press the browser
   back button or revisit a workspace URL, **Then** I cannot view
   workspace content until I log in again.
4. **Given** the public pages (login, signup), **When** an anonymous
   visitor opens them, **Then** they load normally without requiring an
   account.

---

### Edge Cases

- What happens when two users try to register the same email at nearly
  the same time? Exactly one succeeds; the second receives the
  duplicate-email error. The account list never contains two accounts
  with the same email.
- What happens when an email is submitted with different letter casing
  ("Ali@x.com" vs "ali@x.com")? Casing is normalized for uniqueness
  checks so the same address cannot register twice.
- What happens when a name contains leading/trailing spaces or unusual
  characters? Input is trimmed; the display name is stored as entered
  after trimming.
- What happens when a session expires while the user is viewing a page?
  The next action sends them to login; no partial or cached private data
  remains visible after the redirect.
- What happens when a request includes a forged or tampered credential?
  It is treated as unauthenticated — rejected, never partially trusted.
- What happens when a user id is supplied in the request itself that
  differs from the authenticated identity? The authenticated identity
  always wins; the client-supplied value is ignored for authorization.
- What happens when the password contains spaces or unicode characters?
  They are valid; only the minimum length rule applies (no character
  restrictions beyond length).
- What happens to the pre-existing single-user demo data (messages and
  tasks created before this feature)? See Assumptions — it is assigned
  to the first registered account or cleared before launch; it is never
  shown to users who do not own it.

## Requirements *(mandatory)*

### Functional Requirements

**Registration**

- **FR-001**: The system MUST provide a signup page where a new user
  submits Name, Email, Password, and Confirm Password.
- **FR-002**: The system MUST reject registration when any field is
  empty, the email format is invalid, the password is shorter than 8
  characters, or Password and Confirm Password differ — identifying each
  specific problem to the user.
- **FR-003**: On successful registration the system MUST create exactly
  one account with a unique email (uniqueness enforced by the store, not
  just by a pre-check) and sign the user in immediately.
- **FR-004**: The system MUST store passwords only in hashed form;
  plaintext passwords MUST NEVER be stored, logged, or returned by any
  response.
- **FR-005**: Registration MUST be exposed as a single well-defined
  registration endpoint (`POST /auth/register`) accepting name, email,
  and password, returning the created account (without any secret
  material) plus an established session.

**Login & Session**

- **FR-006**: The system MUST let a registered user log in with email
  and password and MUST respond to failed attempts with one generic
  error regardless of whether the email or the password was wrong.
- **FR-007**: The system MUST maintain the signed-in state across page
  visits for a limited session lifetime (default: 7 days) using a
  secure, http-only credential mechanism (per project constitution:
  JWT-based with secure cookie storage).
- **FR-008**: The system MUST provide a way to sign out that immediately
  ends access to protected content in that browser.
- **FR-009**: The system MUST provide a way for pages and endpoints to
  determine the current user's identity from the session alone
  (`GET /auth/me`), with no reliance on client-supplied identity.

**Protected Surface**

- **FR-010**: Every workspace page (dashboard, inbox, tasks, attention,
  connections, settings) MUST require an authenticated session;
  anonymous visits MUST redirect to the login page.
- **FR-011**: Every data endpoint (messages, tasks, and all future data
  reads/writes) MUST require an authenticated session; anonymous calls
  MUST receive an unauthorized response with no data.
- **FR-012**: Only the login page, signup page, and health checks MAY be
  accessed anonymously; every other surface is denied by default.

**User Isolation**

- **FR-013**: Every message, task, and analysis record MUST belong to
  exactly one user (owner recorded server-side at creation).
- **FR-014**: Every read or write of user data MUST be scoped to the
  authenticated user; requesting another user's record MUST behave as
  if the record does not exist.
- **FR-015**: Incoming messages and pipeline outputs (analysis, tasks)
  MUST inherit the ownership of the account that received the message.
- **FR-016**: Client-supplied user identifiers MUST be ignored for
  authorization decisions; identity comes only from the verified
  session.

### API Endpoints

Capability-level contract (implementation details deferred to planning):

| Endpoint | Purpose | Auth required |
|----------|---------|---------------|
| `POST /auth/register` | Create account (name, email, password) → account + session | No |
| `POST /auth/login` | Establish session (email, password) | No |
| `POST /auth/logout` | End the current session | Yes |
| `GET /auth/me` | Return the current user's identity | Yes |
| All existing `/messages`, `/tasks` operations | Unchanged behavior, now scoped to the authenticated user | Yes |

### Signup Acceptance Criteria (summary)

| # | Criterion | Result |
|---|-----------|--------|
| AC-1 | Valid submission creates account + signs user in | Success |
| AC-2 | Any empty field blocks submission with field-specific message | Rejected |
| AC-3 | Invalid email format rejected with clear message | Rejected |
| AC-4 | Password < 8 characters rejected with stated minimum | Rejected |
| AC-5 | Mismatched confirm-password rejected | Rejected |
| AC-6 | Already-registered email rejected clearly | Rejected |
| AC-7 | Stored account contains hashed password only — no plaintext anywhere | Verified |

### Security Rules

1. Deny by default: a surface is public only if explicitly allowlisted.
2. Server-side enforcement only: hiding UI elements is never sufficient
   protection.
3. Identity from session only: client-supplied identity is never trusted
   for authorization.
4. Fail closed: missing/expired/invalid credentials mean denial, never
   degraded access.
5. Passwords hashed with a modern salted algorithm (e.g., bcrypt);
   hashing cost is the standard library default (Simplicity First).
6. Generic authentication errors; no user-enumeration hints.
7. No secrets in code or logs: plaintext passwords, tokens, and hashes
   never appear in logs or responses.
8. Cross-user access returns "not found", confirming neither existence
   nor content.

### Key Entities

- **User**: One account. Attributes: unique identifier, name, email
  (unique, casing-normalized), password hash (never the password
  itself), creation timestamp. Persisted in the project's database
  (MongoDB, per project convention) in a new `users` collection.
- **Session Credential**: Short-lived proof of identity issued at
  login/registration, stored browser-side in a secure cookie and
  verified server-side on every request.
- **Owned Record (Message / Task / Analysis)**: Existing entities gain a
  mandatory owner reference (`user_id`) set server-side at creation;
  every query serving a request filters by it.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new user can complete signup in under 2 minutes,
  including reading validation errors and correcting them.
- **SC-002**: 100% of stored accounts contain a hashed password; zero
  occurrences of plaintext passwords in storage, responses, or logs.
- **SC-003**: 100% of anonymous attempts to reach workspace pages end in
  a redirect to login within 2 seconds.
- **SC-004**: Zero data leakage: after registering users A and B with
  separate messages, B observes 0 of A's records through the UI AND
  through directly-crafted requests (including guessed identifiers).
- **SC-005**: Login succeeds within 2 seconds for correct credentials.
- **SC-006**: 100% of duplicate-email registrations are rejected with a
  clear error; the store never contains two accounts with the same
  normalized email.
- **SC-007**: Existing functionality is unchanged for a signed-in user:
  message arrival, AI analysis, and task extraction all still work with
  ownership attached.

## Assumptions

- Email + password is the only authentication method for the FYP; no
  social/OAuth login.
- No email verification step: registration activates the account
  immediately (acceptable for a university prototype).
- Minimum password length is 8 characters; no complexity rules beyond
  length (Simplicity First).
- Session lifetime defaults to 7 days.
- Pre-existing single-user demo data is assigned to the first registered
  account (or cleared) during development; it is never exposed to
  non-owners.
- The AI pipeline, message store, and dashboard from Weeks 1–2 continue
  to work unchanged; this feature adds ownership, it does not modify
  analysis behavior.

## Out of Scope

- Password reset / forgot-password flows.
- Email verification or confirmation emails.
- Social login (Google, etc.) and two-factor authentication.
- User roles, teams, or admin capabilities (single role only).
- Profile editing beyond what signup captures.
- Rate limiting or lockout policies beyond generic error responses.
