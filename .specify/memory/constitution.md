<!--
Sync Impact Report
==================
Version change: 1.6.0 → 1.7.0 (MINOR: new Day 19 Connection Architecture
section added covering token security, user isolation for connections,
frontend/backend display rules, connection status contract, quality bar)
Modified principles:
  - None existing principles modified
Added sections:
  - Day 19 Connection Architecture (purpose, security principles for
    token storage, user isolation for connections, frontend vs backend
    display rules, connection status contract, quality bar)
Removed sections: N/A
Templates requiring updates:
  - .specify/templates/plan-template.md ✅ no changes needed
    (Constitution Check gates derive from constitution file)
  - .specify/templates/spec-template.md ✅ no changes needed
    (requirements format compatible with connection constraints)
  - .specify/templates/tasks-template.md ✅ no changes needed
    (task structure compatible; connection tasks follow standard patterns)
  - .specify/templates/commands/*.md ✅ N/A — no command templates exist
Follow-up TODOs: None
-->

# Communication AI Constitution

## Core Mission

Build an Agentic AI system that helps users manage communication overload.
The system receives messages from multiple channels (WhatsApp, Gmail, etc.),
prioritizes them intelligently, extracts tasks and deadlines, and presents
users with a clean dashboard showing only what needs their attention.

**Success means**: Users spend less time triaging messages and more time
acting on what matters.

## Development Principles

### I. Simplicity First

Every feature MUST start with the simplest viable implementation. Complexity
is only added when proven necessary by real requirements, not anticipated
needs. Prefer straightforward solutions over clever ones. If a solution
requires explanation, it is too complex.

**Rationale**: A university FYP has fixed timelines. Simple code ships faster,
is easier to demo, and is easier to maintain under deadline pressure.

### II. Vertical Slices

Build features end-to-end before moving to the next feature. Each slice
MUST deliver visible, testable value independently. Avoid building
horizontal layers (all models, then all services, then all UI) in isolation.

**Rationale**: Vertical slices produce demo-able progress at every stage,
reduce integration risk, and align with agile iteration.

### III. AI is Assistive, Not Magical

AI components MUST augment human judgment, never replace it silently.
Every AI-generated output (priority scores, task extraction, summaries)
MUST be explainable and dismissible by the user. Never assume the AI
is correct without user confirmation for critical actions.

**Rationale**: Trust is earned through transparency. Users must understand
why the system made a recommendation and retain final authority.

### IV. User Control

Users MUST retain full control over their data, priorities, and workflow.
The system MUST NOT auto-delete, auto-send, or auto-respond without
explicit user action. All AI suggestions are advisory by default.

**Rationale**: Communication is personal and high-stakes. Automated mistakes
(draft sent to wrong person, missed deadline) have real consequences.

### V. Security and Privacy

User messages contain sensitive information. The system MUST:
- Never log message content in plaintext in production
- Encrypt data at rest and in transit
- Use environment variables for all API keys and secrets
- Follow OWASP Top 10 guidelines for web application security
- Provide users with data export and deletion capabilities

**Rationale**: Communication data is among the most personal data
a system can handle. Privacy is non-negotiable.

### VI. Clean Code

Code MUST be readable, well-structured, and consistent. Follow these rules:
- Use TypeScript for all frontend code, Python for all backend/AI code
- Follow established conventions (PEP 8 for Python, ESLint/Prettier for TS)
- Name things clearly; avoid abbreviations in identifiers
- Keep functions focused; one function, one responsibility
- Write meaningful commit messages

**Rationale**: Clean code reduces cognitive load, speeds up debugging,
and enables rapid iteration during a time-constrained FYP.

### VII. Progressive Enhancement

Core functionality MUST work without JavaScript or AI. The dashboard
should load useful data even if the AI service is temporarily unavailable.
Gracefully degrade features rather than failing entirely.

**Rationale**: LLM APIs have rate limits and downtime. The system must
remain useful even when AI components are unavailable.

## AI Feature Guidance

This section provides focused rules for the AI features being built
on Days 11-13: Task Extraction, Urgency + Deadline Detection, and
Recommended Action. These rules extend Principle III (AI is Assistive,
Not Magical) and the existing AI Behavior Rules in SPEC.md.

### Task Extraction

#### Purpose

Extract clear, actionable tasks from incoming messages so users can see
what they need to do without reading every message fully. Tasks are
stored in the `tasks` collection and displayed on the Tasks page.

#### Input → Output Contract

A message enters the system. The AI MUST return:

```json
{
  "tasks_extracted": [
    {
      "description": "Send FYP slides",
      "deadline": "Tonight",
      "priority_indicator": "urgent",
      "requires_action": true
    }
  ],
  "task_count": 1
}
```

#### What the AI MUST Do

1. **Only extract tasks explicitly mentioned in the message.** A task
   exists when the message contains a clear verb directed at the
   recipient (send, review, submit, prepare, confirm, call, etc.).
2. **Preserve the original deadline wording exactly as stated.** If the
   message says "tonight", the deadline field MUST be `"Tonight"` — not
   a converted date, not null, not an invented timestamp.
3. **Return an empty array when no actionable tasks exist.** Messages
   that are purely informational, social, or automated MUST produce
   zero tasks — no false positives.
4. **Attribute the task to the recipient, not the sender.** "I'll send
   you the files tomorrow" is NOT a task for the recipient.
5. **Combine related sub-tasks into one task** when they form a single
   coherent action (e.g., "review slides and send feedback" → one task).

#### What the AI MUST NEVER Do

- **NEVER invent a task that is not in the message.** If the message
  says "meeting tomorrow", that is context — not a task — unless it
  explicitly asks the recipient to do something.
- **NEVER invent deadlines.** If no deadline is mentioned, the
  `deadline` field MUST be `null`. Do not infer deadlines from context
  (e.g., "meeting tomorrow" does not mean the task is due tomorrow).
- **NEVER assume urgency without evidence.** The `priority_indicator`
  field MUST only contain words actually present in the message or
  strong semantic equivalents. Do not add "urgent" because the message
  is short or direct.
- **NEVER auto-create tasks in the database.** Tasks are advisory.
  The system stores them for user review; the user decides what to act on.

#### Quality Bar

- **Accuracy**: ≥ 85% of messages containing clear action requests MUST
  produce correct task extraction (tested against a labeled set of 50
  messages).
- **False positive rate**: ≤ 10% — messages without actionable content
  MUST NOT produce tasks.
- **Latency**: Task extraction MUST complete within the same LLM call
  as priority classification (no additional API round-trip).
- **Graceful fallback**: If extraction fails, the message is stored
  with `tasks_extracted: []` and `status: "pending"`. No error is shown
  to the user; the message still appears on the dashboard.

### Urgency & Deadline Detection

#### Purpose

Understand relative time expressions in messages and convert them into
useful deadline information when possible. This supports both task
extraction (deadline field) and priority classification (Urgent vs
Important vs Normal).

#### Supported Time Expressions

The AI MUST recognize and correctly classify these relative expressions:

| Expression | Classification | Example |
|---|---|---|
| right now, ASAP, immediately | Urgent (hours) | "Submit the form right now" |
| today, tonight | Urgent (today) | "Send me the slides tonight" |
| tomorrow | Important (1 day) | "Review this by tomorrow" |
| this week, by Friday | Important (days) | "Finish the report this week" |
| next week, next month | Normal (weeks) | "Prepare the slides next week" |
| before the meeting, before Monday | Depends on meeting date | "Send docs before the meeting" |
| no deadline mentioned | Normal (no urgency) | "Can you check this?" |

#### What the AI MUST Do

1. **Detect relative time expressions** and classify urgency based on
   the expression, not invented context.
2. **Preserve the original expression as the deadline value** when an
   exact date/time cannot be reliably determined from context. If the
   message says "tonight", the deadline is `"Tonight"` — not a computed
   datetime.
3. **Convert to an exact date ONLY when the expression is unambiguous
   and the current date context is available.** For example, "tomorrow"
   can be converted if today's date is known. If not, keep `"tomorrow"`.
4. **Use urgency signals to inform priority classification.** Messages
   with "ASAP" or "right now" MUST be classified as Urgent. Messages
   with "this week" SHOULD be classified as Important.
5. **Handle ambiguous references gracefully.** "Before the meeting" —
   if no meeting date is known, keep the original expression. Do not
   guess.

#### What the AI MUST NEVER Do

- **NEVER invent a specific date or time** that is not stated or
  unambiguously derivable from the message. "Tonight" MUST NOT become
  `"2026-08-19T23:59:00"`.
- **NEVER assume a timezone.** Keep deadline expressions in their
  original form unless the user's timezone is explicitly configured.
- **NEVER override user-stated deadlines.** If a user says "by Friday"
  and the AI thinks it should be "by Thursday" based on context, the
  AI MUST use "Friday".
- **NEVER infer urgency from message length, tone, or sender alone.**
  A short message is not automatically urgent. A message from a boss is
  not automatically urgent without a time-related expression.
- **NEVER fabricate deadlines for informational messages.** "Just
  FYI — the server will be down tomorrow" has no deadline for the
  recipient. `deadline` MUST be `null`.

#### Quality Bar

- **Accuracy**: ≥ 90% of relative time expressions MUST be correctly
  classified (tested against a labeled set of 30 messages with varied
  time expressions).
- **No hallucinated dates**: 0 tolerance — any invented date in a
  deadline field is a critical failure.
- **Latency**: Deadline detection is part of the single LLM analysis
  call. No additional latency budget.
- **Graceful fallback**: If deadline detection fails, `deadlines: []`
  is returned and priority defaults to `"normal"`. The user sees the
  message without deadline info; nothing breaks.

### Recommended Action

#### Purpose

Generate a short, actionable recommendation for the user when a message
arrives. This helps users quickly understand what to do next without
reading the full message. Recommendations are displayed on the dashboard
alongside priority, summary, and task extraction.

#### Input → Output Contract

A message enters the system. The AI MUST return:

```json
{
  "recommended_action": "Prepare and send the report before the deadline."
}
```

The `recommended_action` field is a single string containing one clear
next step for the user.

#### What a Good Recommended Action Looks Like

1. **One sentence, one action.** "Send the report by 5 PM" — not a
   paragraph of options.
2. **Verb-first.** Start with an action verb (Send, Review, Confirm,
   Prepare, Schedule, Call, etc.).
3. **Rooted in the message.** The recommendation MUST reflect what the
   message actually asks for, not an interpretation of what the user
   should do based on invented context.
4. **Time-aware when relevant.** If the message contains a deadline, the
   recommendation SHOULD reference it (e.g., "Submit the form before
   Friday").

#### What the AI MUST Do

1. **Extract the primary action from the message.** Identify the main
   verb directed at the recipient and phrase it as a clear next step.
2. **Keep it under 15 words.** Longer recommendations lose impact on a
   dashboard scan.
3. **Use the user's own words when possible.** If the message says
   "send the slides", the recommendation should be "Send the slides"
   — not "Distribute the presentation materials".
4. **Default to "Review this message" when no clear action exists.**
   Informational messages with no actionable content MUST still produce
   a recommendation, but it should be generic and honest.
5. **Return the recommendation in the same language as the message.**
   If the message is in Arabic, the recommendation MUST be in Arabic.

#### What the AI MUST NEVER Do

- **NEVER invent actions not in the message.** If the message says
  "meeting tomorrow", the recommendation MUST NOT be "Prepare meeting
  agenda" — that is an invented action. The correct output is
  "Review this message" or a direct reference to the stated content.
- **NEVER generate multiple recommendations.** The field is a single
  string, not an array. Pick the ONE most important action.
- **NEVER use hedging language.** "You might want to consider sending
  the report" is too weak. Use direct imperatives: "Send the report".
- **NEVER add opinions or judgments.** "You should prioritize this
  urgent task" adds subjective framing. Stick to the action itself.
- **NEVER auto-execute the recommendation.** The recommendation is
  advisory only. The user decides whether and when to act.

#### Quality Bar

- **Actionability**: ≥ 90% of messages with clear action requests MUST
  produce a recommendation that directly reflects the message's content
  (tested against a labeled set of 50 messages).
- **Honesty**: 0 tolerance — recommendations MUST NOT invent actions
  not present in the message.
- **Latency**: Recommendation generation is part of the single LLM
  analysis call (no additional API round-trip).
- **Graceful fallback**: If recommendation generation fails, the field
  returns an empty string `""`. The user sees the message without a
  recommendation; nothing breaks.

## Complete AI Pipeline

This section defines how the five individual agents — Priority, Summary,
Task Extraction, Deadline Detection, and Recommended Action — connect
into one end-to-end flow (Day 14). These rules extend Principle II
(Vertical Slices), Principle III (AI is Assistive, Not Magical), and
Principle VII (Progressive Enhancement).

### Purpose

When a message arrives, the complete pipeline MUST run every agent in
sequence and deliver one coherent result to MongoDB and the Dashboard:

```text
Message
  ↓
Priority Agent
  ↓
Summary
  ↓
Task Extraction
  ↓
Deadline Detection
  ↓
Recommended Action
  ↓
MongoDB
  ↓
Dashboard
```

**Success means**: A user opens the dashboard and immediately sees what
needs attention, why it matters, and what to do next — without opening
a single raw message.

### Core Principles for the Full Flow

1. **One message in, one complete analysis out.** Every incoming message
   MUST pass through all five agents exactly once per processing run.
   No message is left half-analyzed unless a stage fails, in which case
   that stage's documented fallback value is stored instead.
2. **Fixed stage order.** Priority runs first (it drives attention
   ranking); Recommended Action runs last (it consumes task and deadline
   context). Stages MUST NOT be reordered or silently skipped.
3. **Single LLM call.** Priority, tasks, deadlines, and recommendation
   MUST share one LLM analysis call, consistent with the feature guidance
   above. Adding pipeline stages MUST NOT multiply API round-trips.
4. **Persist once, read many.** The pipeline writes the complete analysis
   to MongoDB as ONE document update. The Dashboard MUST read stored
   results only — it MUST NOT invoke agents or recompute AI output.
5. **Per-stage graceful degradation.** Each stage keeps its own fallback
   (empty arrays, empty strings, default priority). A failed stage MUST
   NOT block later stages, the database save, or the dashboard render.
6. **Idempotent processing.** Re-running the pipeline on the same
   message MUST update the existing document — never create duplicates.

### What "Needs Attention" Means

A message is flagged 🔴 NEEDS ATTENTION only when agent outputs provide
evidence. The flag MUST be derived from stored signals — never invented.

A message qualifies when ANY of the following is true:

| Signal | Source Agents |
|---|---|
| Actionable task extracted AND a near-term deadline detected (e.g., "tonight", "tomorrow") | Task Extraction + Deadline Detection |
| Priority classified as Urgent AND an actionable task exists | Priority + Task Extraction |

Every flagged card MUST display a **"Why it matters"** line naming the
actual trigger in plain language (e.g., "A task with a near deadline was
detected."). Messages that meet no criterion appear normally WITHOUT the
flag — false positives erode user trust faster than missed flags.

### How the Final Result Looks on the Dashboard

Each analyzed message renders as a card with these fields, in this order:

```text
🔴 NEEDS ATTENTION
Send FYP slides
WhatsApp • Ali
Deadline: Tonight
Why it matters: A task with a near deadline was detected.
Recommended: Send the slides before tonight.
```

Field mapping rules:

- **Attention badge**: shown only when the Needs Attention criteria are met
- **Task line**: task description from Task Extraction (the user's own words)
- **Channel • Sender**: e.g., `WhatsApp • Ali` — from message metadata
- **Deadline**: original wording preserved (`Tonight`, never a computed datetime)
- **Why it matters**: trigger explanation tied to real agent signals
- **Recommended**: single verb-first action, ≤ 15 words

Additional rules:

- All card content comes from stored MongoDB data; the Dashboard formats,
  it does not compute.
- Missing optional fields (deadline, recommendation) are omitted cleanly —
  never rendered as blank space, `null`, or `"undefined"`.
- The card MUST render completely even when some fields are missing
  (Progressive Enhancement applies to the final render too).

### Quality Bar for the Complete Pipeline

- **End-to-end**: A message sent through any supported channel appears on
  the dashboard with all available fields — verified manually per channel.
- **Latency**: Total pipeline time ≤ 10 seconds per message including the
  LLM call. The UI shows a loading state; it never blocks or freezes.
- **Persistence**: 100% of processed messages are saved to MongoDB with
  whatever analysis succeeded (fallback values for failed stages).
- **Idempotency**: Reprocessing produces zero duplicate documents.
- **Flag honesty**: 100% of NEEDS ATTENTION flags MUST be explainable by
  their "Why it matters" line; 0 tolerance for invented reasons.
- **Fidelity**: Card fields map 1:1 to stored data — no recomputation,
  re-classification, or agent calls in the UI layer.

## Authentication & Multi-User System

This section defines the rules for turning Communication AI from a
single-user prototype into a real multi-user SaaS application (Week 3).
These rules extend Principle IV (User Control) and Principle V (Security
and Privacy). Day 15 delivered Signup; Days 16-17 deliver Login with JWT
sessions, full route protection, and the finished auth-page UI.

### Purpose of Authentication

Authentication converts the system into a multi-user application where
every message, task, and analysis belongs to exactly one account. Users
MUST be able to register and log in, and the system MUST guarantee that
each user sees only their own data.

**Success means**: Two users can use the system at the same time, and
neither can see, modify, or even detect the other's data.

### Core Security Principles

1. **Deny by default.** Every page and API endpoint is unauthenticated
   until explicitly allowlisted. Only `/login`, `/signup`, and health
   checks are public.
2. **Never trust the client.** User identity is derived ONLY from the
   verified session token on the server. A user ID supplied in a request
   body, query string, or header is never used for authorization.
3. **Server-side enforcement.** Protection MUST be enforced by FastAPI
   dependencies/middleware and Next.js middleware. Hiding links or
   buttons in the UI is cosmetic, never sufficient.
4. **Fail closed.** Missing, expired, or invalid credentials result in
   denial of access — never degraded or read-only access.
5. **Minimal exposure.** Auth responses and errors MUST NOT reveal
   password hashes, tokens, internal IDs of other users, or stack traces.

### User Isolation Rules

User isolation is the highest-priority requirement of Week 3. One user
MUST NEVER see another user's data. Every rule in this section is
mandatory and non-negotiable.

1. Every message, task, analysis, connection, and webhook document MUST
   carry a `user_id` field identifying its owner, set server-side at
   creation time. The `user_id` MUST be derived exclusively from the
   verified JWT session — never from request body, query string, or
   client-supplied header.
2. Every database query serving a request MUST filter by the
   authenticated user's `user_id`. Unfiltered queries are forbidden in
   all request paths, including background workers, webhooks, and
   scheduled tasks.
3. Requests for another user's resource MUST return 404 (not 403) so
   the resource's existence is never confirmed. The response body MUST
   NOT differ between "resource does not exist" and "resource belongs
   to another user."
4. Any new collection MUST define its ownership model before the first
   write to it. The ownership model MUST specify: the field name
   (`user_id`), how it is set (server-side from JWT), and which queries
   filter on it.
5. Isolation verification: register users A and B; B MUST see zero of
   A's messages and tasks through both the UI and direct API calls,
   including guessed object IDs. This test MUST pass before any
   data-access code ships to production.
6. Aggregation pipelines, joins, and bulk operations MUST apply the
   `user_id` filter before any other computation. Post-filter isolation
   is not sufficient — leaked data in intermediate results is a breach.
7. Error responses MUST NOT expose data from other users. A 404, 403,
   500, or validation error MUST NOT include another user's IDs, names,
   email addresses, or message content in the response body or logs
   visible to the client.
8. Frontend state MUST NOT store, cache, or render data belonging to
   another user. After logout, all client-side state (React state,
   URL params, service worker caches) MUST be cleared before the next
   user's session begins.
9. Database indexes MUST support efficient per-user queries. Full
   collection scans without a `user_id` filter are forbidden in
   production request paths.
10. Webhook ingestion endpoints MUST resolve the owning user from
    server-side credentials (API key, signed secret) — never from
    user-supplied query parameters or headers.
11. Any new API endpoint that returns a list of resources MUST enforce
    `user_id` filtering at the query layer, not by post-filtering
    results in application code.

### Password Handling Rules

1. Passwords MUST be hashed with bcrypt (or argon2id) before storage.
   Plaintext passwords MUST NEVER be stored, logged, or returned by any
   endpoint.
2. Minimum password length is 8 characters, enforced on both client
   and server.
3. Email addresses are unique (unique index on `users.email`); duplicate
   registrations MUST be rejected with a clear error message.
4. Failed login MUST return one generic error ("Invalid email or
   password") — never reveal whether the email exists.
5. Password fields MUST be excluded from all API responses, logs, and
   serialized documents.

### What Must Be Protected

- **Pages**: `/dashboard`, `/tasks`, `/attention`, `/inbox`,
  `/connections`, `/settings` — unauthenticated visits redirect to
  `/login`.
- **API endpoints**: `/messages`, `/tasks`, `/auth/me`, and every other
  data endpoint — unauthenticated calls return 401 Unauthorized.
- **Public surface**: only `/login`, `/signup`, and backend health
  checks.
- **Webhook/simulate endpoints**: each MUST have an explicit documented
  auth decision (authenticated, or scoped with a secret) — none may be
  silently left open.

### Day 15 Signup Contract

- **Page**: `/signup` with four fields: Name, Email, Password, Confirm
  Password.
- **Endpoint**: `POST /auth/register` accepting `{name, email, password}`
  → `201` with the created user (no hash) and an authenticated session
  cookie.
- **Validation**: server-side checks for required fields, email format,
  password length, and confirm-password match; client-side validation
  mirrors it for UX only.
- **Storage**: user document contains name, email, and the password
  hash — nothing else, no plaintext copy anywhere.

### Day 16 Login Contract

- **Page**: `/login` with Email and Password fields plus a visible link to
  `/signup`.
- **Endpoint**: `POST /auth/login` accepting `{email, password}` → `200` with
  the user object (no hash) and an authenticated session cookie; ANY failure
  (unknown email, wrong password, malformed body) → `401` with the single
  generic message "Invalid email or password".
- **Token**: A signed JWT containing the user's `user_id` (as `sub`) and an
  expiry, stored in an HttpOnly, Secure, SameSite cookie. Tokens MUST NEVER
  be stored in localStorage, sessionStorage, or returned in response bodies.
- **Verification**: The submitted password MUST be checked with the hashing
  library's comparison function against the stored bcrypt/argon2id hash.
  Hand-written comparisons are forbidden.
- **Post-login routing**: On success the user lands on their own
  `/dashboard`. Every subsequent request carries the cookie and resolves to
  exactly that user's data (see User Isolation Rules) — Hamza's dashboard,
  messages, tasks, and connections contain ONLY Hamza's data.

### Day 17 Route Protection Contract

- **Session endpoint**: `GET /auth/me` returns `{id, name, email}` resolved
  ONLY from the verified JWT cookie; missing, expired, or invalid tokens
  return `401`. The frontend uses this endpoint as its single source of
  truth for session state — it never decodes or trusts client-side token
  data.
- **Backend enforcement**: Every data endpoint (`/messages`, `/tasks`,
  `/connections`, `/dashboard`, `/auth/me`, and all future endpoints) MUST
  require a valid token through ONE shared FastAPI dependency/middleware.
  An endpoint without the dependency does not ship.
- **Frontend enforcement**: Next.js middleware redirects unauthenticated
  visits to any protected page (`/dashboard`, `/inbox`, `/tasks`,
  `/attention`, `/connections`, `/settings`) to `/login`; logged-in visits
  to `/login` or `/signup` redirect to `/dashboard`.
- **Public allowlist** (complete): `/login`, `/signup`, and backend health
  checks. Everything else denies by default.
- **No cosmetic-only protection**: Hiding links, buttons, or checking
  storage in React is cosmetic. The server MUST independently enforce every
  rule; the UI layer adds convenience, never authority.

### Day 18 User Isolation Contract

This section defines the strict data isolation rules for Day 18. It
extends Principle IV (User Control), Principle V (Security and Privacy),
and the User Isolation Rules above. Every message, task, analysis, and
related datum MUST belong to exactly one user. Isolation is not a feature
— it is a security invariant.

#### Purpose of User Isolation

User Isolation guarantees that every piece of data in the system is
owned by exactly one user and is invisible to all others. The system
MUST enforce this at every layer: database queries, API responses, UI
rendering, error messages, and logs. A breach of isolation is a critical
security failure — not a bug.

**Success means**: User A has Message A, User B has Message B. User A
MUST NEVER see Message B. User B MUST NEVER see Message A. This holds
for all data types: messages, tasks, analyses, connections, webhooks,
and any future collections.

#### Core Privacy & Security Principles

1. **Data belongs to the user, not the system.** Every document in
   MongoDB is owned by one user. The system is a custodian, not an
   owner. Users MUST be able to delete all their data and have it
   removed from every collection, index, and cache.
2. **Least privilege by default.** A user's session grants access to
   ONLY that user's data. No endpoint, query, or background process
   may access data across user boundaries without an explicit, audited
   mechanism (which does not exist in this system today).
3. **Deny by existence.** If a resource belongs to another user, the
   system MUST respond as if the resource does not exist (404). The
   system MUST NOT confirm, hint at, or leak the existence of data
   belonging to other users through status codes, error messages, or
   timing differences.
4. **Server-side ownership.** The `user_id` is extracted from the
   verified JWT session on every request. Client-supplied user IDs are
   never trusted. The server sets the `user_id` at write time; the
   client cannot override it.
5. **No cross-user aggregation.** Analytics, dashboards, and reports
   MUST only aggregate the current user's data. The system MUST NOT
   produce cross-user statistics, leaderboards, or comparisons — even
   if the data appears anonymized.
6. **Audit trail.** Every database write MUST include the owning
   `user_id`. Every database read MUST filter on `user_id` before any
   other operation. These two rules are the foundation of isolation
   and MUST NOT be bypassed.

#### Strict Rules for Data Ownership

Every data entity in the system MUST comply with these ownership rules:

| Entity | Ownership Field | Set By | Filtered By |
|---|---|---|---|
| User account | `_id` | System (registration) | N/A (identity) |
| Message | `user_id` | Server (webhook/simulate) | Every query |
| Task | `user_id` | Server (task extraction) | Every query |
| Analysis | `user_id` | Server (pipeline) | Every query |
| Connection | `user_id` | Server (user action) | Every query |

Rules:

1. The `user_id` field MUST be present on every document in every
   collection. No exceptions.
2. The `user_id` MUST be set server-side from the verified JWT at the
   moment of document creation. It MUST NOT come from the request body,
   query parameters, or headers.
3. Every database query in a request path MUST include a `user_id`
   filter as its FIRST condition. Queries without `user_id` are
   forbidden.
4. Bulk operations (insert many, update many, delete many) MUST apply
   `user_id` scope to prevent cross-user mutations.
5. Database migrations that touch user-owned collections MUST preserve
   the `user_id` field on every document. Migrations MUST NOT
   temporarily remove or nullify `user_id`.

#### What Must NEVER Happen

These are absolute prohibitions. Violation of any one is a critical
security failure that blocks release:

- **NEVER return another user's data.** An API response MUST NOT
  include any document, field, ID, email, name, or content belonging
  to a different user — even partially, even in an error message, even
  in a log visible to the client.
- **NEVER query without user_id filtering.** A database read or write
  that does not filter by the authenticated user's `user_id` is
  forbidden. This applies to every code path: request handlers,
  background jobs, webhook processors, and scheduled tasks.
- **NEVER trust client-supplied user IDs.** The `user_id` MUST come
  from the verified JWT session only. A request body containing
  `"user_id": "..."` or `"owner": "..."` MUST be ignored or rejected.
- **NEVER leak existence.** A 403 response that says "resource exists
  but belongs to another user" is a breach. The correct response is
  404 with no distinction between "not found" and "not yours."
- **NEVER cache cross-user data.** In-memory caches, Redis caches,
  CDN caches, and browser caches MUST NOT contain data from multiple
  users in the same entry. Per-user caching is permitted only when the
  cache key includes the `user_id`.
- **NEVER log user data across boundaries.** Log entries MUST NOT
  include another user's email, name, message content, or IDs. Error
  logs that capture full request context MUST sanitize cross-user
  references before writing.
- **NEVER bypass isolation for "convenience."** Admin views, debugging
  tools, analytics dashboards, and internal APIs are NOT exempt from
  isolation. Every access path enforces the same rules.
- **NEVER use partial isolation.** Isolation MUST apply to every data
  type equally. A system that isolates messages but leaks tasks is not
  isolated. Every collection is in scope.

#### Quality Bar for User Isolation

- **Two-user isolation test**: Register users A and B. Create messages,
  tasks, and connections for each. Verify: A sees only A's data; B sees
  only B's data. Verified through both the UI and direct API calls,
  including guessed object IDs.
- **API response audit**: Every endpoint that returns user data MUST be
  tested with two sessions. Response bodies MUST NOT contain any field
 , ID, or string from the other user.
- **404 semantics**: Requesting another user's resource by ID MUST
  return 404. The response body MUST be identical to requesting a
  non-existent resource.
- **Query coverage**: Every database query in the codebase MUST include
  a `user_id` filter. Automated testing or code review MUST verify
  this. Any query without `user_id` blocks merge.
- **No cross-user logs**: Error logs and application logs MUST NOT
  contain another user's data. Verified by inspecting log output
  during the two-user isolation test.
- **Logout state clear**: After logout, navigating to any protected
  page MUST show the login screen — not stale data from the previous
  user. Verified by logging out and logging in as a different user.
- **Ownership model documentation**: Every collection MUST have its
  ownership model documented (field name, source, query requirement)
  before it ships. Un documented collections block merge.

### Day 19 Connection Architecture

This section defines the rules for connecting external communication
accounts (WhatsApp, Gmail, LinkedIn, etc.) to the system. It extends
Principle IV (User Control), Principle V (Security and Privacy), and
the User Isolation Rules. Connections are the bridge between external
platforms and the AI pipeline.

#### Purpose of Connections

The Connections feature allows users to link external communication
accounts so the system can receive and process messages from multiple
channels. Users MUST be able to view connection status, connect new
providers, and disconnect existing ones. The system MUST guarantee that
each user's connections and associated credentials are completely isolated
from all other users.

**Success means**: A user connects their WhatsApp account. The system
receives messages from that account, processes them through the AI
pipeline, and displays results on the dashboard. No other user can see,
use, or detect this connection.

#### Security Principles for Token Storage

1. **Encrypted at rest.** All access tokens and refresh tokens MUST be
   encrypted before storage using AES-256 or equivalent. Plaintext
   tokens MUST NEVER be stored in the database.
2. **Never exposed to frontend.** Tokens (access, refresh, or any
   credential) MUST NEVER be returned in API responses, stored in
   client-side state, or visible in browser developer tools.
3. **Environment-based encryption keys.** Encryption keys MUST be stored
   in environment variables, never in code or database. Key rotation
   MUST be supported.
4. **Backend-only token operations.** Token refresh, validation, and API
   calls using stored tokens MUST happen exclusively on the backend.
   The frontend never handles tokens directly.
5. **Audit trail for token access.** Every token read or write operation
   MUST be logged with the user_id, timestamp, and operation type for
   security monitoring.

#### User Isolation for Connections

Every connection belongs to exactly one user. The same isolation rules
that apply to messages and tasks extend to connections:

1. Every connection document MUST carry a `user_id` field set server-side
   from the verified JWT.
2. Every database query for connections MUST filter by the authenticated
   user's `user_id` as the first condition.
3. Requests for another user's connection MUST return 404 with no
   distinction between "not found" and "not yours."
4. Connection deletion MUST only remove the authenticated user's
   connection — never affect other users' connections.
5. The system MUST NOT allow users to see, modify, or detect connections
   belonging to other users.

#### Frontend vs Backend Display Rules

**What the frontend MAY show:**

- Provider name (WhatsApp, Gmail, LinkedIn)
- Connection status (Connected, Disconnected, Error)
- Connect/Disconnect buttons
- Provider logo/icon
- "Coming Soon" label for unavailable providers

**What MUST stay in backend only:**

- Access tokens
- Refresh tokens
- OAuth state/authorization codes
- Token expiry timestamps
- Provider-specific credentials
- Any raw API responses containing credentials

The frontend communicates with the backend through API endpoints that
return only the safe fields listed above. The `connections` collection
in MongoDB stores all credential fields; the API response DTO MUST
exclude them.

#### Connection Status Contract

The `connections` collection stores these fields:

| Field | Type | Source | Visible to Frontend |
|---|---|---|---|
| `user_id` | string | Server (JWT) | No (implicit) |
| `provider` | string | Server (validated) | Yes |
| `status` | string | Server (computed) | Yes |
| `accessToken` | string | Server (encrypted) | No |
| `refreshToken` | string | Server (encrypted) | No |
| `createdAt` | datetime | Server (auto) | No |

Status values: `connected`, `disconnected`, `error`, `coming_soon`.

#### Quality Bar for Connection Architecture

- **Token encryption**: 100% of tokens encrypted at rest; zero plaintext
  tokens in database.
- **Frontend isolation**: Zero tokens, credentials, or raw OAuth data
  visible in API responses, browser storage, or developer tools.
- **User isolation**: Two-user isolation test passes for connections —
  User A sees only A's connections; User B sees only B's connections.
- **404 semantics**: Requesting another user's connection by ID returns
  404 with identical response to non-existent resource.
- **Connection lifecycle**: Connect → status "Connected" → Disconnect →
  status "Disconnected" works end-to-end for each provider.
- **Error handling**: Failed connections show user-friendly error
  messages; raw exceptions never shown.
- **Token refresh**: Backend successfully refreshes expired tokens
  without user intervention; frontend remains unaware of token lifecycle.

### Auth Pages UI/UX Principles

Both `/login` and `/signup` share one visual system built on Tailwind CSS +
shadcn/ui. They are the product's front door and MUST look intentional,
modern, and professional.

1. **Dark theme by default.** Deep neutral background, high-contrast text,
   subtle card elevation; both pages use the identical palette.
2. **One centered card layout.** Logo/title, short heading, form fields,
   primary action, and a secondary link ("Create an account" / "Already
   have an account?") in a vertically centered card of ~400px max width
   with generous spacing.
3. **Professional inputs.** Visible labels above fields, placeholder hints
   inside them, password visibility toggle, focus rings, and disabled
   states. Client-side validation mirrors server rules (email format,
   8+ characters) for fast feedback, but the server remains authoritative.
4. **One obvious primary button per page.** Full-width, high-contrast
   ("Log in" / "Sign up"), showing a loading spinner while the request is
   in flight; buttons are disabled during submission so requests cannot be
   duplicated by double-clicks.
5. **Honest errors, inline where possible.** Field-level messages for
   validation issues; one banner-level message for credential failures
   using the exact generic wording required by Password Handling Rules.
   Raw exceptions, stack traces, and technical codes are never shown.
6. **Consistency over decoration.** Both pages use identical fonts, radii,
   spacing scale, and component variants. Decorative extras (illustrations,
   animations) come only after the core flows pass the Quality Bar.

### Quality Bar for Authentication

- Registration works end-to-end: form → `POST /auth/register` → user
  persisted with hashed password → session established.
- Duplicate email signup is rejected with a clear, friendly error.
- Short/weak passwords are rejected with a specific message.
- Visiting any protected page while logged out redirects to `/login`.
- Calling any protected API without a token returns 401.
- The two-user isolation test passes (see User Isolation Rules).
- Zero occurrences of plaintext passwords in code, logs, database, or
  network responses.
- Login and register flows show loading states and human-readable
  errors; raw exceptions are never shown to users.
- Valid credentials log the user in end-to-end: form → `POST /auth/login`
  → JWT cookie set → redirect to their own `/dashboard` showing only
  their data.
- Invalid credentials show the generic error and never reveal whether
  the email exists.
- `GET /auth/me` with a valid cookie returns the session user; without a
  cookie it returns 401.
- Logged-in visits to `/login` or `/signup` redirect to `/dashboard`.
- Login and signup pages render in dark theme with working loading,
  focus, disabled, and password-visibility states, verified on desktop
  and mobile widths.

## Technical Principles

### Frontend

- **Framework**: Next.js with TypeScript
- **Styling**: Tailwind CSS + shadcn/ui component library
- **Architecture**: App Router with server components where possible
- **State**: Minimize client state; prefer server components and URL state
- **Rendering**: SSR for dashboard; CSR only when interactivity requires it

### Backend

- **Framework**: FastAPI (Python)
- **Database**: MongoDB with Motor async driver
- **API Design**: RESTful endpoints with clear JSON schemas
- **Authentication**: JWT-based with secure cookie storage
- **Validation**: Pydantic models for all request/response payloads

### AI Layer

- **LLM Integration**: Use a single LLM API provider initially; abstract
  the interface to allow future provider swaps
- **Prompt Management**: Store prompts as versioned templates, not hardcoded
  strings
- **Fallback**: Always have a non-AI fallback path for critical features
- **Cost Awareness**: Monitor token usage; implement rate limiting per user

### Infrastructure

- **Monorepo**: Single repository with clear separation
  (`app/` for frontend, `backend/` for API)
- **Environment**: `.env.local` for secrets, never committed
- **Package Management**: npm for frontend, pip/poetry for backend

## Quality Bar

### Definition of Done

A feature is DONE when:
1. It works end-to-end (vertical slice complete)
2. It handles errors gracefully with user-facing messages
3. It has been tested manually on the target browser
4. It does not break existing functionality
5. Code has been reviewed (even if self-reviewed for FYP)

### Testing Expectations

- **Unit Tests**: Required for business logic (priority scoring, task extraction)
- **Integration Tests**: Required for API endpoints
- **E2E Tests**: Recommended for critical user flows (not mandatory for FYP)
- **Manual Testing**: Required for all UI changes before commit

### Performance Baseline

- Dashboard loads in under 3 seconds on localhost
- API responses return in under 500ms (excluding LLM calls)
- LLM-powered features show a loading state; never block the UI

### Task Extraction & Deadline Detection Targets

- Task extraction accuracy ≥ 85% on labeled test set
- False positive rate ≤ 10% (no tasks from non-actionable messages)
- Deadline hallucination rate = 0% (no invented dates)
- Relative time expression accuracy ≥ 90%
- Single LLM call for priority + tasks + deadlines (no extra latency)

### Recommended Action Targets

- Recommendation actionability ≥ 90% on labeled test set
- Recommendation hallucination rate = 0% (no invented actions)
- Single LLM call for priority + tasks + deadlines + recommendations
- Fallback returns empty string on failure (no errors shown)

### Complete Pipeline Targets

- End-to-end flow verified: message → all five agents → MongoDB → dashboard card
- Total pipeline latency ≤ 10 seconds per message (LLM call dominates; UI shows loading state)
- Zero duplicate documents when a message is reprocessed
- Every NEEDS ATTENTION flag carries a truthful "Why it matters" explanation
- Dashboard renders exclusively from stored data (no agent invocation from UI)

## Decision Guidelines

When facing uncertainty, use these tiebreakers in order:

1. **Ship it**: Choose the option that delivers value fastest
2. **Keep it simple**: Choose the option with fewer moving parts
3. **User trust**: Choose the option that preserves user control and transparency
4. **Reversibility**: Choose the option that is easiest to change later
5. **Learn it**: Choose the option that teaches you the most for the FYP

### Technology Decisions

- New library: Only if no existing dependency solves the problem
- New pattern: Only if existing patterns are clearly inadequate
- New service: Only if the functionality cannot live in existing services

### AI Decisions

- When AI output is uncertain: Show confidence level, default to "review needed"
- When AI is slow: Cache aggressively, show stale data with timestamp
- When AI is wrong: Log the error, improve the prompt, notify the user

## Governance

This constitution is the authoritative reference for all development decisions
in the Communication AI project. All code reviews, planning sessions, and
implementation choices MUST align with these principles.

### Amendment Process

1. Propose change with rationale
2. Document impact on existing code/features
3. Update constitution with new version
4. Propagate changes to dependent templates and docs

### Versioning Policy

- **MAJOR**: Principle removal, redefinition, or governance change
- **MINOR**: New principle added or section materially expanded
- **PATCH**: Clarifications, wording fixes, typo corrections

### Compliance Review

Before merging any feature branch, verify:
- [ ] Feature follows Simplicity First (no over-engineering)
- [ ] Feature is a complete vertical slice
- [ ] AI outputs are explainable and dismissible
- [ ] User retains control over all automated actions
- [ ] No secrets or sensitive data in code or logs
- [ ] Code is clean and follows project conventions
- [ ] Core functionality works without AI availability
- [ ] Task extraction produces no false positives (no tasks from non-actionable messages)
- [ ] No invented deadlines — all deadline values come from the message or are null
- [ ] Relative time expressions preserved as-is when exact conversion is unreliable
- [ ] Recommended actions reflect the message content (no invented actions)
- [ ] Recommended actions are single, concise, verb-first strings
- [ ] Full pipeline runs on every incoming message (five agents, fixed order)
- [ ] Complete analysis persisted to MongoDB in one document; dashboard reads stored data only
- [ ] NEEDS ATTENTION flags derive from agent signals and always include a "Why it matters" line
- [ ] Reprocessing a message never creates duplicates
- [ ] Every page and endpoint requires authentication except the public allowlist
- [ ] All data queries filter by the authenticated user's `user_id` (user isolation)
- [ ] Passwords are hashed with bcrypt/argon2id; never stored, logged, or returned in plaintext
- [ ] Unauthenticated page access redirects to `/login`; unauthenticated API access returns 401
- [ ] New collections define their ownership model before first write
- [ ] `POST /auth/login` verifies the bcrypt/argon2id hash and issues a signed HttpOnly JWT cookie — tokens never appear in localStorage or response bodies
- [ ] `GET /auth/me` resolves identity only from the verified session token and returns 401 without one
- [ ] Every data endpoint enforces authentication through the shared server-side dependency/middleware (no unprotected endpoints)
- [ ] Logged-in visits to `/login` or `/signup` redirect to `/dashboard`; logged-out visits to protected pages redirect to `/login`
- [ ] Auth pages share one dark-theme design with loading, focus, disabled, and inline error states
- [ ] Every document in every collection carries a `user_id` set server-side from the JWT
- [ ] Every database read/write includes a `user_id` filter as its first condition
- [ ] Requests for another user's resource return 404 with a body identical to "not found"
- [ ] API responses never contain any field, ID, name, or content from another user
- [ ] Logout clears all client state; the next user's session shows no stale data from the previous user
- [ ] New collections have a documented ownership model (field name, source, query requirement) before merge
- [ ] Connection tokens (access, refresh) are encrypted at rest using AES-256 or equivalent
- [ ] No tokens, credentials, or OAuth data appear in API responses, browser storage, or developer tools
- [ ] Connection queries filter by authenticated user's `user_id` as first condition
- [ ] Requesting another user's connection by ID returns 404 identical to non-existent resource
- [ ] Connection status contract is documented (user_id, provider, status, accessToken, refreshToken, createdAt)
- [ ] Frontend only shows provider, status, and connect/disconnect buttons — no credential fields

**Version**: 1.7.0 | **Ratified**: 2026-08-19 | **Last Amended**: 2026-08-25
