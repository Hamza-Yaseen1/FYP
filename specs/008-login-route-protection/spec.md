# Feature Specification: Login, Protected Routes & Auth UI Polish

**Feature Branch**: `008-login-route-protection`  
**Created**: 2026-08-24  
**Status**: Draft  
**Input**: User description: "Create a clear and focused specification for
Day 16 and Day 17: 1. Login 2. Protect Routes 3. Beautiful Login & Signup
pages. Context: Project Communication AI; Signup is already working; now we
need full authentication flow. Day 16 – Login: /login page, POST /auth/login,
secure authentication (JWT recommended), redirect to Dashboard after login,
user sees only their own data. Day 17 – Protect Routes: GET /auth/me,
protect all private pages (/dashboard, /inbox, /attention, /tasks,
/connections, /settings), protect important backend APIs, redirect
unauthenticated users to /login, keep session working after refresh. UI:
beautiful, modern, professional Login and Signup pages, dark theme preferred,
clean layout, good spacing, nice form inputs, clear error messages,
responsive, consistent with the rest of the dashboard style."

## Feature Overview

Complete the authentication flow started by Day 15 signup. Today a person
can register but cannot return: there is no way to log back in, and every
page is wide open to anyone who types its URL. This feature delivers the
remaining two pieces of Week 3 — **Login** (Day 16) and **Protected
Routes** (Day 17) — plus the finished visual treatment for both auth pages.

After this feature: a registered user logs in with email and password,
lands on their own dashboard, and stays signed in across refreshes and
return visits. Anyone not signed in is redirected away from every
workspace page and receives no data from any endpoint. The login and
signup pages look intentional — modern, dark-themed, and consistent with
the rest of the product.

This feature implements the previously specified capabilities from
`007-user-auth` (User Story 2: Log In, User Story 4: Protected Access);
it changes no AI pipeline behavior.

**Success means**: Hamza closes his laptop, comes back tomorrow, logs in
in seconds, and finds exactly his messages, tasks, and connections — while
another user (or an anonymous stranger) can see none of them, even by
guessing URLs or record identifiers.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Log In with Email and Password (Priority: P1)

As a returning user, I want to enter my email and password on the /login
page and be taken straight to my dashboard, so that I can regain access to
my own workspace whenever I return to the application.

**Why this priority**: Login is the gateway to everything else in this
feature — route protection is meaningless until sessions exist, and the
UI polish is decoration until the flow underneath works. It converts
signup from a one-time event into a reusable identity.

**Independent Test**: Can be fully tested by registering a user, opening
/login in a fresh browser session, submitting correct credentials, and
verifying arrival at a dashboard showing only that user's data. Wrong
credentials are verified independently by submitting them and observing
the single generic error.

**Acceptance Scenarios**:

1. **Given** I have a registered account, **When** I submit my correct
   email and password on the login page, **Then** I am signed in and
   redirected to MY dashboard, which shows only MY messages, tasks, and
   connections.
2. **Given** I am on the login page, **When** I submit a wrong password
   for an existing email, **Then** I see one generic error ("Invalid
   email or password") and remain on the login page.
3. **Given** I am on the login page, **When** I submit an email that was
   never registered, **Then** I see exactly the same generic error as for
   a wrong password — nothing reveals whether the email exists.
4. **Given** I am on the login page, **When** I leave a field empty or
   enter a malformed email, **Then** the specific problem is identified
   next to the offending field before any request is sent.
5. **Given** the login request is in flight, **When** the submission is
   being processed, **Then** the button shows a loading state and cannot
   be clicked again.

---

### User Story 2 - Locked Workspace (Priority: P2)

As a system, I want every workspace page and every data endpoint locked
behind a valid session, so that an anonymous visitor — or a visitor whose
session expired — can never reach anyone's workspace, even by typing a
URL directly or calling an endpoint directly.

**Why this priority**: Protection consumes the identity established by
Story 1 but is what makes login meaningful in practice. Ranked second
because it depends on Story 1 existing, though in security importance it
is the highest-stakes guarantee of the phase.

**Independent Test**: Can be fully tested by logging out (or using a
private/incognito browser), attempting to reach each known page URL and
data endpoint directly, and verifying every attempt redirects or rejects;
then logging in and verifying each page loads normally.

**Acceptance Scenarios**:

1. **Given** I am not signed in, **When** I type the URL of any workspace
   page (dashboard, inbox, attention, tasks, connections, settings),
   **Then** I am redirected to the login page instead of seeing content.
2. **Given** I am not signed in, **When** any data endpoint is called
   without a valid session, **Then** it responds with an unauthorized
   error and returns no data.
3. **Given** I am signed in viewing my dashboard, **When** I refresh the
   page, **Then** I remain signed in on the same page — no re-login and
   no bounce to the login screen.
4. **Given** my session has expired while I was viewing a page, **When**
   I take my next action, **Then** I am sent to the login page and no
   private data remains visible after the redirect.
5. **Given** I am already signed in, **When** I open /login or /signup,
   **Then** I am redirected to my dashboard instead of seeing the forms.
6. **Given** the public pages (login, signup), **When** an anonymous
   visitor opens them, **Then** they load normally without an account.
7. **Given** I click log out, **When** the action completes, **Then** my
   session ends immediately and revisiting any workspace URL sends me to
   login.

---

### User Story 3 - Auth Pages That Look Like a Real Product (Priority: P3)

As a visitor evaluating the product, I want the login and signup pages to
look modern, professional, and visually consistent with the dashboard, so
that my first impression builds trust that this is polished software worth
entering.

**Why this priority**: Pure presentation value — the flows beneath must
work first (Stories 1–2). Ranked third because it can be layered onto
working pages without changing behavior, but it directly shapes demo and
evaluation impressions.

**Independent Test**: Can be fully tested by opening /login and /signup
at phone, tablet, and desktop widths and confirming a coherent centered
card layout, readable inputs, working password visibility toggle, visible
focus and loading states, and clear error presentation — with zero layout
breakage.

**Acceptance Scenarios**:

1. **Given** I open either auth page, **When** it renders, **Then** I see
   a single centered card on a dark background containing the product
   name, a short heading, labelled form fields, one primary action
   button, and a link to the sibling page.
2. **Given** I am filling a form, **When** I focus any input, **Then** a
   clear focus indicator appears; when I type a password, **Then** I can
   toggle its visibility.
3. **Given** I submit invalid input, **When** validation fails, **Then**
   the specific problem appears next to the offending field; when
   credentials fail, **Then** one readable banner states the generic
   error.
4. **Given** I view either page at mobile width (~360px) through desktop
   width, **When** the page renders, **Then** all elements remain
   readable, spaced, and tappable with no overflow or cramping.
5. **Given** both auth pages side by side, **When** I compare them,
   **Then** they share identical typography, spacing, colors, and button
   styles, visibly matching the dashboard's design language.

---

### Edge Cases

- What happens when a wrong password is entered for an existing email vs
  an unknown email? Both produce the identical generic error and
  indistinguishable response timing intent — no user enumeration.
- What happens when the session expires mid-session and the user clicks
  something? The next request is rejected as unauthenticated and the user
  lands on /login; no partially-rendered private data remains.
- What happens when a forged, tampered, or expired credential is
  presented? Treated exactly as unauthenticated — rejected, never
  partially trusted.
- What happens when a signed-in user presses browser-back after logout?
  Workspace pages re-check the session and send them to login; cached
  pages reveal no private content.
- What happens when the login button is double-clicked quickly? Only one
  request is sent (button disables during flight).
- What happens when a user guesses another user's record identifier and
  requests it directly? Response behaves as not-found; existence is never
  confirmed.
- What happens when a client-supplied user identifier disagrees with the
  session identity? The session wins; the supplied value is ignored for
  authorization.
- What happens when a password contains spaces or unusual unicode? Valid
  — only minimum length applies; no character restrictions.
- What happens when the network is slow or the backend is briefly
  unreachable? The button stays in loading state, then a human-readable
  error appears ("Something went wrong. Please try again.") — never a raw
  exception.
- What happens when a user refreshes while on /login or /signup? The
  public page simply reloads; no redirect loops occur.

## Requirements *(mandatory)*

### Functional Requirements

**Login & Session (Day 16)**

- **FR-001**: The system MUST provide a login page where a returning user
  enters Email and Password, with a visible link to the signup page.
- **FR-002**: The system MUST expose a single login endpoint
  (`POST /auth/login`) accepting email and password; on success it MUST
  establish a session and return the account identity WITHOUT any secret
  material (no hash, no token in the body).
- **FR-003**: On successful login the system MUST issue a signed,
  tamper-proof session credential stored in a secure, http-only cookie —
  never in browser storage accessible to scripts — that authenticates the
  user automatically across page refreshes and return visits within the
  session lifetime.
- **FR-004**: After successful login the system MUST redirect the user to
  their dashboard showing exclusively their own data.
- **FR-005**: The system MUST respond to failed logins with ONE generic
  error message regardless of whether the email or password was wrong,
  and MUST NOT reveal whether an email is registered.
- **FR-006**: The system MUST verify passwords against the stored salted
  hash using the hashing library's comparison mechanism; plaintext
  comparison is forbidden.
- **FR-007**: The system MUST provide logout (`POST /auth/logout`) that
  immediately invalidates the session and directs the user to the login
  page.

**Route Protection (Day 17)**

- **FR-008**: The system MUST provide a session endpoint (`GET /auth/me`)
  that returns the current user's identity derived ONLY from the verified
  session credential; missing/expired/invalid credentials yield an
  unauthorized response. The interface uses this as the sole source of
  truth for "who is signed in".
- **FR-009**: Every workspace page (`/dashboard`, `/inbox`, `/attention`,
  `/tasks`, `/connections`, `/settings`) MUST require an authenticated
  session; anonymous visits MUST redirect to `/login`.
- **FR-010**: Every data endpoint (messages, tasks, connections, and all
  future data operations) MUST require a valid session; anonymous calls
  MUST receive an unauthorized response with no data.
- **FR-011**: Enforcement MUST happen server-side through a shared,
  uniform protection mechanism applied to all routes and endpoints;
  hiding navigation elements in the interface alone is never sufficient.
- **FR-012**: Only `/login`, `/signup`, and health checks MAY be accessed
  anonymously; every other surface denies by default.
- **FR-013**: Signed-in visitors opening `/login` or `/signup` MUST be
  redirected to the dashboard.
- **FR-014**: Client-supplied user identifiers MUST be ignored for
  authorization; identity comes only from the verified session, and every
  read/write is scoped to that user (cross-user requests behave as
  not-found).

**Auth Pages UI/UX**

- **FR-015**: Both auth pages MUST share one cohesive dark-theme design —
  deep neutral background, high-contrast text, subtle card elevation —
  and appear unmistakably part of the same product as the dashboard.
- **FR-016**: Each auth page MUST present a vertically-centered card
  (max width ≈400px) containing: product name/logo, short heading,
  labelled inputs, one primary action, and the sibling-page link.
- **FR-017**: Inputs MUST have visible labels, placeholder hints, clear
  focus indicators, disabled states, and a password visibility toggle.
- **FR-018**: Each page MUST have exactly one prominent full-width primary
  button that shows a loading state and blocks duplicate submissions
  while the request is in flight.
- **FR-019**: Validation problems MUST appear next to the offending field;
  credential failures MUST show one banner-level generic message; raw
  exceptions and technical codes MUST NEVER be shown.
- **FR-020**: Both pages MUST be responsive and comfortable from small
  mobile (~360px) to desktop widths.
- **FR-021**: The signup page's appearance MUST be brought to the same
  standard (this feature restyles it; its working behavior is unchanged).

### Acceptance Criteria (summary)

| #   | Criterion                                                                     | Verified by |
|-----|-------------------------------------------------------------------------------|-------------|
| AC-1 | Correct credentials → signed in → own dashboard                              | US1.1 |
| AC-2 | Wrong password and unknown email produce identical generic error             | US1.2, US1.3 |
| AC-3 | Field-level validation before request; loading state during flight           | US1.4, US1.5 |
| AC-4 | Anonymous visit to any workspace page → redirect to /login                   | US2.1 |
| AC-5 | Anonymous call to any data endpoint → unauthorized, no data                  | US2.2 |
| AC-6 | Session survives refresh; user stays on current page                         | US2.3 |
| AC-7 | Expired session → next action lands on /login, no residual private data      | US2.4 |
| AC-8 | Logged-in visits to /login or /signup → dashboard                            | US2.5 |
| AC-9 | Logout ends session immediately                                              | US2.7 |
| AC-10 | Auth pages: dark card design, focus/visibility/loading states, responsive   | US3.1–US3.5 |

### API Endpoints

Capability-level contract (implementation details deferred to planning).
`POST /auth/register` from Day 15 already exists and is unchanged.

| Endpoint | Purpose | Auth required |
|----------|---------|---------------|
| `POST /auth/login` | Verify credentials → session credential + account identity | No |
| `POST /auth/logout` | End the current session | Yes |
| `GET /auth/me` | Return current user's identity from the session | Yes |
| All `/messages`, `/tasks`, `/connections`, dashboard data operations | Existing behavior, reachable only with a valid session | Yes |

### Security Rules

1. Deny by default: a surface is public only if explicitly allowlisted
   (`/login`, `/signup`, health checks).
2. Server-side enforcement only: interface hiding is cosmetic, never
   sufficient.
3. Identity from session only: client-supplied identity is never trusted
   for authorization decisions.
4. Fail closed: missing, expired, malformed, or tampered credentials mean
   denial — never degraded or read-only access.
5. Generic authentication errors; zero user-enumeration hints.
6. Secrets stay secret: passwords, hashes, tokens, and other users' ids
   never appear in responses, logs, or browser-script-accessible storage.
7. Cross-user access answers "not found", confirming neither existence
   nor content.
8. Session credentials are signed and expiry-bounded; unsigned or
   self-declared identity is rejected.

### Key Entities

- **User** (exists since 007): unique id, name, unique normalized email,
  salted password hash, creation timestamp. Unchanged by this feature.
- **Session Credential** (activated by this feature): signed,
  expiry-bounded proof of identity issued at login, carried in a secure
  http-only cookie, verified on every protected request. Contains the
  user reference and expiration — never the password or hash.
- **Owned Record** (Message / Task / Analysis, exists since 007): carries
  its owner reference set at creation; all queries filter by it.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A returning user signs in and reaches their dashboard in
  under 10 seconds including typing time; the login request itself
  completes in under 2 seconds for correct credentials.
- **SC-002**: 100% of anonymous attempts to reach any of the six
  workspace pages end in a redirect to /login within 2 seconds.
- **SC-003**: 100% of anonymous calls to any data endpoint receive an
  unauthorized response with zero data returned.
- **SC-004**: Zero data leakage: users A and B, each with their own
  messages and tasks, observe 0 of each other's records through the UI
  AND direct requests, including guessed identifiers.
- **SC-005**: 100% of page refreshes by a signed-in user preserve the
  session (no forced re-login within the session lifetime).
- **SC-006**: Wrong-password and unknown-email failures are externally
  indistinguishable: same message, same response shape.
- **SC-007**: Both auth pages render correctly at 360px, 768px, and
  1280px widths with zero horizontal overflow; every interactive element
  (inputs, toggle, buttons, links) is operable by keyboard.
- **SC-008**: Zero occurrences of plaintext passwords or session tokens
  in storage, responses, logs, or script-accessible browser storage.

## Assumptions

- Session lifetime defaults to 7 days (carried over from the 007 spec).
- After login users always land on the dashboard; "return to the page you
  originally wanted" is deferred (Out of Scope).
- JWT-in-secure-cookie is the anticipated session mechanism per the
  project constitution; the requirement level is "signed, expiry-bounded,
  http-only credential", leaving the exact scheme to planning.
- Dark theme applies to the auth pages as the preferred direction; shared
  components keep them consistent with the dashboard's design language
  even if the dashboard later adjusts palettes.
- Signup's functional behavior is frozen; this feature only restyles it.
- Logout is included because the 007 specification committed to it
  (FR-008 there) and a full authentication flow is undemonstrable without
  it; it is deliberately minimal (one endpoint, one button placement).
- Email + password remains the only authentication method; the existing
  two-user isolation guarantees continue to apply unchanged.

## Out of Scope

- Password reset / forgot-password flows.
- Email verification or confirmation emails.
- Social login and two-factor authentication.
- "Remember me" toggles or user-configurable session lifetimes.
- Redirecting back to the originally-requested page after login.
- Rate limiting or account lockout policies.
- User roles, teams, or admin capabilities.
