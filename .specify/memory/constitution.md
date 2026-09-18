<!--
Sync Impact Report
==================
Version change: 1.17.0 → 1.18.0 (MINOR: Day 29 Security + Testing — new
section added covering the purpose of the hardening phase, core security
principles, reliability/AI-failure rules, duplicate prevention rules,
MUST-NOT prohibitions, and quality bar for this phase.)
Modified principles: N/A (Day 29 continues to extend principles V
(Security and Privacy), VII (Progressive Enhancement), and the Day 18
User Isolation / Day 23 webhook / Day 24 Orchestrator rules without
redefining any core principle)
Added sections:
  - Day 29 Security & Reliability Hardening — full section with purpose,
    core security principles, reliability (AI failure handling), duplicate
    prevention, MUST-NOT rules, and quality bar
Modified sections:
  - Governance compliance checklist — four Day 29 items added
Removed sections: N/A
Templates requiring updates:
  - .specify/templates/plan-template.md ✅ no changes needed
    (Constitution Check gates derive from constitution file)
  - .specify/templates/spec-template.md ✅ no changes needed
    (spec template structure unchanged)
  - .specify/templates/tasks-template.md ✅ no changes needed
    (task structure compatible; security/reliability testing naturally
    map to existing test-first task phases)
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

**Day 24 amendment**: Which agents run for a given message is decided by
the AI Orchestrator (see "Day 24 AI Orchestrator" below), not by a fixed
default. This pipeline executes whichever agents the Orchestrator selects,
in the order the Orchestrator fixes.

### Purpose

When a message arrives, the AI Orchestrator routes it to the agents it
needs; the pipeline runs the selected agents in sequence and delivers one
coherent result to MongoDB and the Dashboard:

```text
Message
  ↓
AI Orchestrator ── decides which agents are needed
  ↓
Priority Agent (always)
  ↓
[Summary / Task Extraction / Deadline Detection as routed]
  ↓
Recommended Action (when routed)
  ↓
MongoDB
  ↓
Dashboard
```

**Success means**: A user opens the dashboard and immediately sees what
needs attention, why it matters, and what to do next — without opening
a single raw message.

### Core Principles for the Full Flow

1. **One message in, one directed analysis out.** Every incoming message
   MUST pass through the AI Orchestrator exactly once per processing run;
   the Orchestrator selects the agents required for that message (Day 24).
   Selected agents then run exactly once. No message is left half-analyzed
   unless a stage is intentionally skipped by the Orchestrator or fails, in
   which case that stage's documented fallback value is stored instead.
2. **Fixed stage order.** Among the agents selected by the Orchestrator,
   Priority runs first (it drives attention ranking); Recommended Action
   runs last (it consumes task and deadline context). Stages MUST NOT be
   reordered or silently skipped.
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

### Day 20 Better Inbox

This section defines the rules for improving the Inbox page with clear
filters, search, and sorting. It extends Principle II (Vertical Slices),
Principle IV (User Control), and the User Isolation Rules from Day 18.
The Better Inbox transforms a basic message list into a powerful,
filterable interface that helps users quickly find and prioritize messages.

#### Purpose of Better Inbox

The Better Inbox transforms the basic message list into a powerful,
filterable interface that helps users quickly find and prioritize messages.
Users MUST be able to filter by priority levels (All, Urgent, Important,
Normal, Unread) and by source (WhatsApp, Gmail, etc.), search across
messages, and sort by date and sender.

**Success means**: A user opens the Inbox and can immediately find the
messages they need to act on, regardless of how many messages exist.
Filtering and searching are fast, accurate, and intuitive.

#### Core Filtering Principles

1. **Priority-based tabs are primary.** The inbox MUST display tabs for
   All, Urgent, Important, Normal, and Unread messages. These are the
   primary navigation mechanism.
2. **Source filtering is secondary.** Users MUST be able to filter by
   communication source (WhatsApp, Gmail, LinkedIn, etc.) in addition
   to priority tabs.
3. **Search is universal.** The search bar MUST search across all message
   fields: content, sender, subject, and any extracted metadata.
4. **Filters compose.** Priority tabs and source filters MUST work
   together. Selecting "Urgent" tab + "WhatsApp" source shows only
   urgent WhatsApp messages.
5. **Clear visual feedback.** Active filters MUST be clearly indicated.
   Users MUST know exactly what view they're looking at.
6. **One-click reset.** Users MUST be able to clear all filters and
   return to the default view with a single action.

#### User Capabilities

Users MUST be able to:
- **Switch between priority tabs** (All, Urgent, Important, Normal,
  Unread) with one click
- **Filter by source** (WhatsApp, Gmail, LinkedIn, etc.) using a
  dropdown or multi-select
- **Search messages** using the "Search communications..." search bar
- **Sort by date** (newest first, oldest first)
- **Sort by sender** (alphabetical)
- **Combine filters** (e.g., "Urgent" + "WhatsApp" + "from Ali")
- **See filter counts** (number of messages in each tab/filter)
- **Clear all filters** with one action
- **View message details** by clicking on a message card

#### Message Display Rules

Every message in the inbox MUST:
1. **Belong to the current user.** Only messages with the authenticated
   user's `user_id` are shown. This extends the User Isolation Rules
   from Day 18.
2. **Show essential fields:** sender, source, subject/preview, timestamp,
   priority badge, unread indicator
3. **Respect priority classification.** The priority badge (Urgent,
   Important, Normal) MUST match the AI pipeline's classification
4. **Preserve original data.** Sender names, timestamps, and content
   come from the stored message — never fabricated
5. **Handle missing data gracefully.** If a field is missing (e.g., no
   subject), omit it cleanly — never show "null", "undefined", or
   blank space

#### Quality Bar for Better Inbox

- **Filter accuracy**: 100% — selecting "Urgent" shows ONLY messages
  classified as Urgent
- **Search accuracy**: Search results MUST match the query in sender,
  subject, or content fields
- **Performance**: Filtering and search MUST complete in under 200ms
  for up to 1000 messages
- **User isolation**: Two-user isolation test passes — User A sees only
  A's messages in inbox; User B sees only B's messages
- **Empty states**: When no messages match filters, show a clear
  "No messages found" state
- **Loading states**: Show skeleton loaders during initial load; filters
  apply instantly without loading states
- **Responsive design**: Inbox MUST work on desktop and mobile widths
- **Accessibility**: Filter tabs and search bar MUST be keyboard navigable

### Day 21 Task Management

This section defines the rules for building a clean "My Tasks" page that
shows extracted tasks clearly. It extends Principle I (Simplicity First),
Principle II (Vertical Slices), and the Task Extraction guidance from the
AI Feature Guidance section. The Task Management page transforms task
extraction results into a focused, actionable task list.

#### Purpose of Task Management

The Task Management page provides a clean, focused view of all extracted
tasks. Users MUST be able to see their tasks organized by urgency with
clear action options. The page transforms AI-extracted tasks into a
simple, actionable list that helps users act on what matters.

**Success means**: A user opens the Tasks page and immediately sees their
tasks organized by priority, with clear options to complete, snooze, or
view the source message for each task.

#### Core Task Management Principles

1. **Tasks are extracted, not invented.** Every task displayed MUST come
   from the Task Extraction agent's output stored in MongoDB. The system
   MUST NOT create, modify, or prioritize tasks beyond what the AI
   extracted from the original message.
2. **Clarity over complexity.** The task list MUST show only essential
   information: task description, deadline, and priority indicator. No
   hidden states, no complex workflows, no unnecessary metadata.
3. **Actionable by default.** Every task MUST have clear action options
   available. Users can complete, snooze, or view the source message for
   any task without navigating away from the page.
4. **Urgency drives organization.** Tasks MUST be organized by urgency
   with visual indicators: 🔴 for urgent, 🟡 for important, 🟢 for normal.
   Users MUST see urgent tasks first.
5. **Simplicity in interaction.** Task actions (Complete, Snooze, View)
   MUST be one-click operations. No confirmation dialogs, no complex
   forms, no multi-step processes.

#### Task Display Rules

Every task in the "My Tasks" page MUST:

1. **Belong to the current user.** Only tasks with the authenticated
   user's `user_id` are shown. This extends the User Isolation Rules
   from Day 18.
2. **Show essential fields:** task description, deadline (if any), and
   priority indicator (🔴, 🟡, 🟢)
3. **Respect priority classification.** The priority indicator MUST match
   the AI pipeline's classification from Task Extraction.
4. **Preserve original wording.** Task descriptions and deadlines come
   from the AI extraction — never fabricated or modified.
5. **Handle missing data gracefully.** If a deadline is missing, omit it
   cleanly — never show "null", "undefined", or blank space.

#### Task Action Rules

**Complete Action:**
- MUST mark the task as completed in the database
- MUST remove the task from the active task list
- MUST show a brief visual confirmation (e.g., task disappears with subtle animation)
- MUST NOT delete the task permanently — it can be accessed in task history if needed

**Snooze Action:**
- MUST allow users to snooze tasks for a defined period (e.g., 1 hour, tomorrow, next week)
- MUST update the task's deadline to the snoozed time
- MUST keep the task in the active list until the new deadline passes
- MUST show the updated deadline after snoozing

**View Message Action:**
- MUST navigate to or display the original message that triggered the task extraction
- MUST show the message in context (sender, source, timestamp, content)
- MUST allow users to return to the task list easily
- MUST NOT lose the user's position in the task list

#### Quality Bar for Task Management

- **Accuracy**: 100% — every task displayed MUST correspond to a real
  extracted task in MongoDB; no fabricated tasks
- **User isolation**: Two-user isolation test passes — User A sees only
  A's tasks; User B sees only B's tasks
- **Performance**: Task list loads in under 1 second for up to 100 tasks
- **Action reliability**: 100% — Complete, Snooze, and View actions MUST
  work as specified; no silent failures
- **Empty states**: When no tasks exist, show a clear "No tasks found"
  state with helpful guidance
- **Loading states**: Show skeleton loaders during initial load; actions
  apply instantly without loading states
- **Responsive design**: Task list MUST work on desktop and mobile widths
- **Accessibility**: Task actions MUST be keyboard navigable

### Day 22 WhatsApp Business Integration Research + Setup

This section defines the rules for researching and setting up the official
WhatsApp Business Platform (Cloud API) integration. It extends Principle IV
(User Control), Principle V (Security and Privacy), and the Connection
Architecture from Day 19. Day 22 is a research and setup day — not full
implementation.

#### Purpose of Real WhatsApp Integration

Replace the fake/mock WhatsApp webhook with a real integration using the
official WhatsApp Business Platform Cloud API. The system MUST receive
incoming messages from a verified WhatsApp Business number, process them
through the AI pipeline, and display results on the dashboard.

**Success means**: A test message sent to the WhatsApp Business number is
received by the webhook, stored in MongoDB, and appears on the dashboard
with full AI analysis — proving the integration works end-to-end.

#### Official & Allowed Approach Only

The system MUST use ONLY the official WhatsApp Business Platform Cloud API
provided by Meta. Specifically:

1. **Cloud API only.** All WhatsApp communication MUST go through the
   official Meta Cloud API (`graph.facebook.com`). Self-hosted BSP
   solutions, third-party wrappers, or reverse-engineered endpoints are
   forbidden.
2. **Meta Developer account required.** A Meta Developer account MUST be
   created and used to register the WhatsApp Business app.
3. **Official SDK or REST API.** Use the official Meta SDK or direct REST
   API calls. No community libraries that abstract the API without
   maintaining compatibility.
4. **Webhook verification.** The webhook endpoint MUST respond to Meta's
   verification challenge (`GET` request with `hub.mode`, `hub.verify_token`,
   `hub.challenge`) before receiving any messages.

#### Security & Privacy Principles for WhatsApp Integration

1. **Credentials in environment only.** The WhatsApp Business Account ID,
   Phone Number ID, Access Token, and Webhook Verify Token MUST be stored
   in environment variables (`.env.local`), never in code, database, or
   version control.
2. **HTTPS required.** The webhook endpoint MUST be served over HTTPS.
   Meta will not send webhooks to HTTP endpoints.
3. **Webhook signature verification.** Every incoming webhook request MUST
   be validated using Meta's `X-Hub-Signature-256` header before
   processing. Requests with invalid signatures MUST be rejected.
4. **No personal WhatsApp data.** The system MUST NOT attempt to read,
   access, or process personal WhatsApp notifications, messages from
   personal accounts, or data outside the WhatsApp Business Platform
   scope.
5. **User isolation for WhatsApp connections.** Each user's WhatsApp
   Business connection MUST be isolated per the User Isolation Rules from
   Day 18. The `user_id` is resolved server-side from the verified JWT —
   never from webhook query parameters.
6. **Minimal data retention.** Store only the message content, sender
   metadata, and timestamps needed for the AI pipeline. Do not store
   raw webhook payloads longer than necessary for processing.

#### What to Set Up Today (Research + Setup Scope)

Day 22 covers research and initial configuration only. The following
MUST be completed:

| Task | Description |
|---|---|
| Meta Developer Account | Create and verify a Meta Developer account |
| WhatsApp Business App | Register a new app in the Meta Developer portal |
| WhatsApp Business Number | Associate a test phone number with the Business account |
| Cloud API Access | Obtain the Phone Number ID, WhatsApp Business Account ID, and a temporary access token |
| Webhook Configuration | Register a webhook URL in the Meta portal pointing to the backend endpoint |
| Webhook Verification | Implement and test the `GET` verification challenge endpoint |
| Environment Variables | Store all credentials (access token, phone number ID, WABA ID, verify token) in `.env.local` |
| Test Message Reception | Send a test message to the Business number and confirm the webhook receives it |
| MongoDB Storage | Store the received test message in the `messages` collection with `user_id` |
| End-to-End Proof | Verify the test message appears on the dashboard with AI analysis |

#### What MUST NOT Happen

- **NEVER read personal WhatsApp notifications.** The system MUST NOT
  access, scrape, or process WhatsApp messages from personal accounts.
  Only messages sent to the registered WhatsApp Business number through
  the official Cloud API are in scope.
- **NEVER use unofficial APIs or libraries.** Third-party WhatsApp
  wrappers (e.g., `whatsapp-web.js`, `baileys`, community reverse-engineered
  libraries) are forbidden. Only the official Meta Cloud API is allowed.
- **NEVER store API keys or tokens in code.** All credentials MUST be in
  environment variables. Hardcoded secrets are a blocking security violation.
- **NEVER skip webhook signature verification.** Every incoming request
  MUST be validated. Accepting unsigned webhooks is a security breach.
- **NEVER auto-send messages during research.** Day 22 is about receiving
  and processing incoming messages. Auto-reply, broadcast, or template
  message sending is out of scope for this phase.
- **NEVER expose webhook secrets or access tokens to the frontend.**
  WhatsApp Business credentials are backend-only, consistent with the
  Connection Architecture from Day 19.

#### Quality Bar for Day 22

- **Webhook verification**: The `GET` verification endpoint responds
  correctly to Meta's challenge and the portal shows "Verified" status.
- **Message reception**: A test message sent to the Business number is
  received by the `POST` webhook endpoint within 30 seconds.
- **Signature validation**: Webhook requests with invalid or missing
  signatures are rejected (403 or 400).
- **Storage**: Received test messages are stored in MongoDB with `user_id`,
  `sender`, `content`, `timestamp`, and `source: "whatsapp"`.
- **Dashboard display**: The test message appears on the dashboard with
  AI analysis (priority, summary, tasks, recommendation) — end-to-end
  flow confirmed.
- **Credential security**: Zero hardcoded secrets; all credentials in
  `.env.local`; `.env.local` is gitignored.
- **User isolation**: The test message is associated with the authenticated
  user's `user_id` from the JWT — not from webhook parameters.

### Day 23 Real WhatsApp Webhook

This section defines the rules for converting the verified webhook from
Day 22 into a real ingestion endpoint for the WhatsApp Business Cloud API.
It extends Principle II (Vertical Slices), Principle V (Security and
Privacy), the Day 18 User Isolation Rules, and the Day 22 WhatsApp Business
Integration. Day 23 is an implementation day: the webhook stops being a
research stub and becomes the entry point for real messages.

#### Purpose of the Real WhatsApp Webhook

Receive real incoming messages from the WhatsApp Business Cloud API,
validate them, and normalize them into the standard Communication AI message
format before storing to MongoDB and running the AI pipeline.

**Success means**: A real message sent to the WhatsApp Business number is
received by the webhook, validated, normalized, stored in MongoDB, and
appears on the dashboard with full AI analysis — following exactly the same
path as the simulate endpoint today. Neither the AI pipeline nor the
dashboard can tell whether a message came from WhatsApp, the simulate
endpoint, or a future channel.

#### Normalized Message Format (Source-Agnosticity)

The AI pipeline, dashboard, and database MUST NEVER consume channel-specific
payloads. WhatsApp payloads, simulate payloads, and future channels are
translated at the ingestion boundary into one canonical message document:

```json
{
  "userId": "64f...",
  "source": "whatsapp",
  "sender": "Ali",
  "content": "Send me the slides tonight.",
  "receivedAt": "2026-08-28T09:41:00Z",
  "externalMessageId": "wamid.ABC123..."
}
```

Rules:

1. **`source` is an enum, never free text.** Allowed values: `whatsapp`,
   `simulate`, and channels added later by explicit amendment. Downstream
   code branches on this field; no other source indicator is read.
2. **`sender` is human-readable.** Use the profile name from the payload
   when present; fall back to the `wa_id` phone number when it is not.
   Never store raw Meta contact objects.
3. **`content` is the message text.** For non-text messages (images, audio,
   documents), store an empty string and let the pipeline mark the message
   as media-only. Never drop the message.
4. **`receivedAt` is server time.** The UTC ISO-8601 timestamp captured when
   the webhook received the event — not the sender-reported timestamp.
5. **`externalMessageId` is the provider message ID** (e.g., Meta `wamid`).
   It MUST be persisted and MUST key idempotence.
6. **`userId` is set server-side.** The owning user is resolved from verified
   webhook credentials / the connection mapping — never from query
   parameters, request body, or headers (User Isolation Rules, Day 18).

**Rationale**: Normalization is the boundary between the external world and
the AI core. If every channel parses its own payload, the pipeline grows one
special case per provider and quality dies by entropy. One canonical format
keeps the AI, MongoDB, and the dashboard provider-agnostic.

#### Security & Validation Rules

1. **Signature first.** Every `POST /webhooks/whatsapp` request MUST be
   validated against Meta's `X-Hub-Signature-256` header (HMAC-SHA256 over
   the raw body with `WHATSAPP_APP_SECRET`) BEFORE any parsing. Invalid or
   missing signatures return 403 and are never processed.
2. **Structure validation.** The parsed payload MUST be validated with a
   Pydantic model matching Meta's schema before any field is read.
   Malformed payloads are rejected (400) and never stored.
3. **Respond fast, process later.** The webhook handler MUST return 200 as
   soon as the message is validated and accepted. The AI pipeline runs
   asynchronously off the request path. A non-2xx reply triggers Meta
   retries and duplicate deliveries.
4. **Idempotent delivery.** Processing MUST be keyed on `externalMessageId`.
   A duplicate delivery (Meta retry, replay) MUST be acknowledged with 200
   and skipped without creating a duplicate document.
5. **Credentials server-side only.** `WHATSAPP_APP_SECRET`, access tokens,
   and verify tokens stay in environment variables and are never returned
   to the frontend (Connection Architecture, Day 19).
6. **Minimal retention.** Store the normalized message, not the raw Meta
   payload. Raw webhook payloads are never persisted long-term or surfaced
   to the dashboard.

#### What Happens When a Real Message Arrives

```text
WhatsApp  →  Webhook POST (Meta Cloud API)
              ↓
        1. Verify X-Hub-Signature-256
              ↓
        2. Validate payload structure (Pydantic)
              ↓
        3. Normalize to canonical message format
              ↓
        4. Dedupe on externalMessageId  ── dup → respond 200, stop
              ↓
        5. Persist to MongoDB with user_id (server-side)
              ↓
        6. Trigger AI pipeline asynchronously
              ↓
        7. Dashboard renders from stored analysis only
```

Each step is a distinct responsibility. The webhook handler covers steps 1–5
and responds 200; the pipeline runs step 6 out-of-band; the dashboard never
touches the webhook (Complete AI Pipeline rules).

#### What MUST NOT Happen

- **NEVER process an unverified webhook.** Requests with invalid or missing
  signatures are rejected before any parsing or storage.
- **NEVER block the Meta response on the AI pipeline.** The webhook MUST
  respond 200 fast; running the five-agent pipeline synchronously risks
  timeouts, retries, and duplicate processing.
- **NEVER store raw Meta payloads.** Only the normalized message is
  persisted. Raw payloads are not kept beyond the request scope.
- **NEVER trust client-supplied identity.** `userId` is resolved server-side
  from verified credentials, never from query parameters or body fields.
- **NEVER bypass normalization.** No service, agent, or dashboard component
  reads WhatsApp-specific fields (`text.body`, `wa_id`) directly.
- **NEVER auto-reply or auto-send.** Day 23 remains receive-only; outbound
  messaging stays out of scope (as in Day 22).

#### Quality Bar for Day 23

- **Signature validation**: Webhook requests with invalid or missing
  `X-Hub-Signature-256` are rejected (403); zero unverified payloads are
  processed.
- **Normalization fidelity**: A real received message converts losslessly to
  the canonical format (`source`, `sender`, `content`, `receivedAt`,
  `externalMessageId`) — verified with a live test message.
- **End-to-end parity**: A real WhatsApp message and a simulate message
  produce identical dashboard cards; the pipeline and dashboard cannot
  distinguish the source.
- **Idempotency**: Redelivering the same webhook payload produces zero
  duplicate documents (keyed on `externalMessageId`).
- **Responsiveness**: The webhook responds 200 within 1 second of arrival;
  total pipeline latency stays within the existing ≤ 10 second budget.
- **Source-agnostic core**: Zero references to WhatsApp-specific fields in
  the AI pipeline, storage layer, or dashboard (grep-verifiable).
- **Isolation**: The ingested message carries a server-resolved `user_id`
  and is visible only to that user.
- **No regression**: Simulated messages continue to work through the same
  normalized ingest path.

### Day 24 AI Orchestrator

This section defines the rules for the AI Orchestrator, a single decision
layer that chooses which agents — Priority, Summary, Task Extraction,
Deadline Detection, Recommended Action — need to run for each new message.
It extends Principle I (Simplicity First), Principle III (AI is Assistive,
Not Magical), Principle VII (Progressive Enhancement), and the Complete AI
Pipeline rules. One clear orchestration layer MUST replace any scattered,
ad-hoc AI calls.

#### Purpose of the AI Orchestrator

The Orchestrator is the single entry point between message ingestion and
the AI agents. Its job is to answer one question for every message: "What
do we need to know about this message — and which agents tell us?" Instead
of always running every analysis on every message, the system routes each
message to exactly the agents that add value for it.

```text
New Message
  ↓
Orchestrator
  ↓
What do we need to know?
  ↓
Priority Agent / Task Agent / Summary Agent / etc.
```

**Success means**: Every incoming message is analyzed exactly as much as it
needs — no more, no less. Trivial messages are cheap and fast; rich messages
get full treatment; nothing irrelevant is ever computed.

#### Core Orchestration Principles

1. **One orchestration layer.** All routing decisions (what to analyze, and
   in what order) live in the Orchestrator. Services, endpoints, webhooks,
   and the dashboard MUST NOT call agents directly or decide on their own
   whether an agent runs. Messy scattered AI calls are forbidden.
2. **Minimal analysis per message.** The Orchestrator MUST select the
   smallest set of agents that can fully serve the message. Full analysis
   is the default ONLY when the Orchestrator cannot decide confidently — it
   is never the first choice.
3. **Priority is never optional.** Priority classification runs for every
   message; every inbox and dashboard view depends on it. If no other agent
   is selected, priority still runs.
4. **Trivial messages are cheap.** Messages with no actionable content
   (greetings, "ok", social chatter) MUST be routed to minimal analysis
   (priority + summary only) — no task extraction, no deadline detection,
   no elaborate recommendation.
5. **Decisions are explainable.** Every routing decision MUST be recorded in
   the stored analysis (a `routing` note naming which agents ran and why), so
   users and developers can see why a message got light or full treatment.
   This extends Principle III (AI is Assistive, Not Magical).
6. **Rule-based first, LLM only when needed.** The Orchestrator SHOULD route
   with cheap, deterministic signals (channel, sender, content length,
   presence of action/time-trigger keywords) before spending any LLM budget.
   It is a router for AI, not a new AI agent that needs its own model call.
7. **One path only.** This is NOT a multi-agent framework: no orchestration
   SDK, no agent-to-agent messaging, no conversation graphs, no runtime. ONE
   orchestrator function, ONE decision path. If the design needs more than
   that, the feature is too complex (Principle I).

#### What the Orchestrator MUST Decide

1. **Whether to analyze at all.** Messages with no analyzable content
   (media-only with empty text, empty content, or out-of-scope channels)
   MAY be stored and shown without AI analysis, with `status` set
   accordingly. A skipped message MUST still appear on the dashboard and
   MUST never block ingestion.
2. **Which agents to run.** From the five available agents, the Orchestrator
   MUST select the required subset for this message:
   - **Priority Agent**: always — never skipped.
   - **Summary Agent**: every message except trivial one-liners where the
     summary would just duplicate the content.
   - **Task Extraction**: only when the message plausibly requests an action
     (contains a task-trigger verb or keyword: send, review, submit,
     confirm, prepare, call, ...).
   - **Deadline Detection**: only when a time expression is present
     ("tonight", "tomorrow", "by Friday", ...).
   - **Recommended Action**: only when the message warrants a next step;
     otherwise the honest fallback ("Review this message").
3. **The order of execution.** Priority first, Recommended Action last.
   The Orchestrator fixes the order; individual agents MUST NOT reorder
   themselves or the stages around them.
4. **The fallback for every selected agent.** A selected-but-failed agent
   stores its documented fallback value; an intentionally skipped agent
   stores the skip reason in the `routing` note. The two MUST be
   distinguishable in the stored record so debugging stays honest.
5. **Whether the LLM call is needed at all.** If routing determines no
   analysis is worth an API call (trivial/empty content), the message MUST
   be stored with deterministic low-cost defaults instead of spending
   tokens. When the LLM IS needed, it remains exactly one round-trip.

#### What the Orchestrator MUST NOT Do

- **NEVER let AI be called from outside the Orchestrator.** No service,
  endpoint, webhook, or dashboard component invokes an agent on its own;
  all AI access goes through the Orchestrator. This is the "one clear
  orchestration layer" rule.
- **NEVER fabricate an agent's output.** Skipping Task Extraction means
  `tasks_extracted: []` — not a guessed task. A skipped agent must never
  produce invented tasks, deadlines, or action plans.
- **NEVER spend extra LLM round-trips on orchestration.** Adding a routing
  decision MUST NOT multiply API calls. Routing comes from deterministic
  rules or rides inside the existing single analysis call (Complete AI
  Pipeline rules).
- **NEVER build a multi-agent framework.** No second orchestrator, no
  agent-to-agent messaging, no external orchestration SDK, no runtime. One
  function, one path.
- **NEVER let an agent choose its own execution.** An agent MUST NOT decide
  to run itself, skip itself, or reorder itself. Routing authority belongs
  to the Orchestrator alone.
- **NEVER degrade what must always hold.** Priority is never skipped. User
  isolation, source normalization (Day 23), and persistence apply to every
  message the Orchestrator routes — exactly as before.
- **NEVER hide the decision.** Light treatment of a message MUST be
  visible in its stored `routing` note — it must never look like a bug.

#### Quality Bar for the AI Orchestrator

- **Routing coverage**: 100% of incoming messages flow through the
  Orchestrator; zero direct agent calls exist outside it (grep-verifiable).
- **Decision accuracy**: ≥ 90% of a labeled set of 50 messages are routed to
  the correct agent subset (trivial messages get no task extraction; action
  messages get task extraction).
- **Priority completeness**: 100% of analyzed messages carry a priority
  value.
- **Cost discipline**: The Orchestrator adds ZERO extra LLM round-trips;
  total pipeline latency stays within the existing ≤ 10 second budget.
- **No fabrication**: Skipped agents store documented fallbacks plus a
  `routing` note with the skip reason; 0 tolerance for invented tasks,
  deadlines, or recommended actions.
- **Explainability**: Every stored analysis includes a `routing` note naming
  the agents that ran and the trigger for the decision.
- **No regression**: The end-to-end flow (WhatsApp webhook → Orchestrator →
  selected agents → MongoDB → dashboard) still produces correct cards, and
  simulate messages behave identically.

### Day 25 Agent Memory / Context

This section defines the rules for giving the AI lightweight context between
related messages. It extends Principle I (Simplicity First), Principle III
(AI is Assistive, Not Magical), Principle IV (User Control), Principle V
(Security and Privacy), Principle VII (Progressive Enhancement), and the
Day 24 Orchestrator rules. Today every message is analyzed in isolation;
Day 25 lets the system associate messages when it clearly makes sense.

#### Purpose of Agent Memory / Context

The AI MUST be able to treat closely-related messages as one exchange so
that context from one message can inform the analysis of another:

```text
Message 1: "Can you send the report?"        ← task, no deadline
Message 2: "Need it before our meeting."     ← deadline context

Known together: the report task carries a deadline; the inbox shows one
linked thread instead of two unrelated cards.
```

**Success means**: When two or more messages clearly belong to the same
exchange, the system links them (stored IDs) and, when a later message
supplies missing context (deadline, urgency), that context is reflected in
the earlier message's analysis — visibly and explainably. Messages that do
not clearly relate are treated exactly as they are today.

#### Core Principles for Linking Messages

1. **Link only when it clearly makes sense.** Two messages MUST be linked
   only by a deterministic rule: same user, same channel (`source`), same
   normalized `sender`, and arrival within a bounded time window of the
   previous message in the thread (default ≤ 60 minutes). The link MUST be
   evidence-based, never a matter of interpretation.
2. **Context is additive, never invented.** A later message's context MAY
   refine the analysis of an earlier linked message, but every inferred
   enrichment MUST be recorded with an explanation naming the linked
   message(s). Nothing is written into a message that the linked messages do
   not actually support.
3. **Idle by default.** When no link applies, analysis proceeds exactly as
   today — zero behavior change, zero extra cost. Context is a bonus, never
   a prerequisite for analysis.
4. **Assistive, not magical.** Every context-enriched field MUST carry a
   plain-language reason (e.g., "Deadline added from a later message by Ali").
   The insight MUST be dismissible and verifiable against the linked
   messages — never a silent rewrite of prior analysis.
5. **Isolation is absolute.** A thread or conversation MUST NEVER span
   users. Linking happens strictly within one user's messages and remains
   owned by that user (Day 18 User Isolation Rules apply unchanged).
6. **No memory framework.** This is lightweight in-message context, NOT a
   persistent conversation memory. No vector store, no embeddings, no RAG,
   no agent-with-memory runtime. One deterministic link step, then the
   existing single-call pipeline (Principle I).

#### What MUST Be Stored

Every message document in MongoDB MUST carry three identity fields, all set
server-side at ingest — never supplied by the client:

| Field | Type | Set By | Nullable | Meaning |
|---|---|---|---|---|
| `messageId` | string | System (message `_id`) | Never | Identity of the message |
| `threadId` | string | Server (deterministic link rule) | Yes (null when alone) | Groups messages in one exchange |
| `conversationId` | string | Server (defaults to `threadId` when set) | Yes | Broad persistent grouping, reserved for user-defined conversations |

Rules:

1. **`messageId`** equals the message's own identifier and MUST always be
   present.
2. **`threadId`** follows the deterministic rule in Core Principle #1. When
   a new message matches an existing thread (same user, source, sender,
   in-window arrival), it inherits that thread's `threadId`; otherwise it is
   `null`. A `threadId` MUST NOT be created for a single message on
   speculation.
3. **`conversationId`** MUST NOT be invented. For Day 25 it equals
   `threadId` when set and is `null` otherwise. A user-defined conversation
   concept may come later only by explicit amendment of this section.
4. **Isolation preserved.** Linked messages remain individually owned,
   individually queryable, and individually deletable by their user. The
   link is metadata, never a shared container.
5. **Indexing.** Per-user indexes on `{user_id, conversationId, receivedAt}`
   and `{user_id, threadId, receivedAt}` MUST support link resolution and
   thread display without full scans.
6. **No retrofitting.** Historical messages MAY be backfilled with
   `threadId`/`conversationId` only by the same deterministic rule and only
   within one user's data; backfills MUST NOT guess groupings.

#### What Context Enters the AI Call (Bounded)

1. **Deterministic link, then single call.** Linking is resolved by the
   rule in storage; the context is presented to the model INSIDE the
   existing single analysis call (Complete AI Pipeline) — never as an extra
   round-trip or a second agent.
2. **Cap the context window.** At most the most recent 5 messages of the
   linked thread are passed in, all belonging to the same user. Older or
   unrelated history MUST NOT be included.
3. **Prioritized user facts.** An explicit fact stated by the user (a stated
   deadline, a stated preference) always wins over inferred context. The
   system MUST NOT use context to override a user-stated value (mirror of the
   Day 11 deadline rules).
4. **The Orchestrator still decides.** Context availability is one more input
   to the Orchestrator's routing decision. If routing decides context is not
   worth spending on, the message is analyzed standalone with normal
   fallbacks — never blocked.

#### What the System MUST NOT Do

- **NEVER invent a link.** Messages from different senders, different
  channels, or far apart in time MUST NOT be grouped on keywords, tone, or
  speculation. A false link is a false claim about the conversation.
- **NEVER build a memory framework.** No vector store, no embeddings, no
  RAG, no fine-tuned memory model, no conversation-history database beyond
  the stored identity fields. Context must fit in a deterministic link plus
  the existing single LLM call.
- **NEVER span users.** A thread or conversation MUST NOT combine messages
  from different users. Cross-user grouping is a Day 18 isolation breach.
- **NEVER silently rewrite prior analysis.** If later context changes an
  earlier message's deadline or urgency, the update MUST be stored as a new,
  explainable analysis revision with a reason naming the linked message. The
  original wording is never overwritten invisibly.
- **NEVER let context override an explicit user-stated fact.** An inferred
  deadline never beats a stated one.
- **NEVER block ingestion on linking.** If link resolution fails or times
  out, the message is stored and analyzed standalone exactly as today
  (Progressive Enhancement; Day 24 Orchestrator fallback rules).
- **NEVER inflate cost.** Context handling adds zero LLM round-trips and zero
  measurable latency to standalone messages.

#### Quality Bar for Day 25

- **Link precision**: ≤ 5% false links — messages from different senders,
  different channels, or unrelated conversations are never grouped (tested
  against a labeled set of 30 message pairs).
- **Link recall**: ≥ 80% of labeled, clearly-related same-sender windows
  arrive correctly in one `threadId` (same labeled set).
- **Context effect**: When a later message adds a deadline to an earlier
  linked message, the earlier message's deadline/priority update is visible,
  correct, and carries a reason naming the linked message. 0 tolerance for
  unlabelled context influence.
- **No regression**: Standalone (unlinked) messages are analyzed exactly as
  before with zero added latency — verified by re-running the existing
  single-message test set unchanged.
- **Isolation**: Linking a conversation across two users is impossible —
  verified with the two-user isolation test.
- **Cost discipline**: Context handling adds zero extra LLM round-trips;
  total pipeline latency stays within the existing ≤ 10 second budget.
- **Explainability**: Every context-enriched field is dismissible and
  traceable to the linked message(s) that produced it.

### Day 26 Gmail Integration

This section defines the rules for connecting Gmail accounts to the system
using Google's official OAuth 2.0 flow. It extends Principle IV (User
Control), Principle V (Security and Privacy), Principle VII (Progressive
Enhancement), the Day 19 Connection Architecture, and the Normalized Message
Format from Day 23. Day 26 adds a second real communication channel after
WhatsApp, proving the system is channel-agnostic.

#### Purpose of Gmail Integration

Allow users to connect their Gmail account so the system can receive and
process incoming emails through the same AI pipeline used for WhatsApp
messages. The system MUST use only Google's official OAuth 2.0 flow — no
passwords, no IMAP, no unofficial libraries.

**Success means**: A user clicks "Connect Gmail", is redirected to Google's
consent screen, grants permission, and the system begins receiving their
new emails. Those emails appear on the dashboard as normalized message
cards, indistinguishable in treatment from WhatsApp messages — same
priority, same task extraction, same AI analysis. No other user can see,
use, or detect this Gmail connection.

#### OAuth-Only Security Principle

The system MUST use ONLY Google's official OAuth 2.0 authorization flow.
Specifically:

1. **No passwords.** The system MUST NEVER ask for, accept, store, log,
   or transmit a user's Gmail password. This is an absolute prohibition.
2. **Google OAuth 2.0 only.** All Gmail access goes through Google's
   official OAuth 2.0 endpoints (`accounts.google.com` for authorization,
   `oauth2.googleapis.com` for token exchange). Third-party auth
   libraries, community wrappers, or reverse-engineered endpoints are
   forbidden.
3. **Official Google API client.** Use the official Google API Python client
   (`google-api-python-client`) or direct REST API calls to the Gmail API
   (`gmail.googleapis.com`). No community libraries that abstract the
   Gmail API without maintaining official compatibility.
4. **Minimal scopes.** The OAuth consent screen MUST request only the
   minimum Gmail scopes needed: `https://www.googleapis.com/auth/gmail.readonly`
   for reading emails. Write scopes (`gmail.send`, `gmail.modify`) are
   forbidden at this stage — Day 26 is receive-only.
5. **Consent is explicit.** Users MUST see Google's consent screen listing
   exactly what permissions are requested before granting access. The
   system MUST NOT bypass or automate the consent step.

**Rationale**: Passwords are the weakest link in authentication. OAuth
delegates credential management to Google, the account owner's trusted
provider. The system never touches the password and cannot be compromised
through it.

#### Token Handling Rules

Gmail OAuth tokens (access tokens and refresh tokens) are among the most
sensitive credentials in the system. These rules extend the Day 19
Connection Architecture security principles:

1. **Encrypted at rest.** Access tokens and refresh tokens MUST be
   encrypted with AES-256 (or equivalent) before storage in MongoDB.
   Plaintext tokens MUST NEVER be stored, logged, or returned.
2. **Never exposed to frontend.** Tokens MUST NEVER appear in API
   responses, client-side state, localStorage, sessionStorage, or browser
   developer tools. The frontend sees only connection status (Connected /
   Disconnected / Error).
3. **Backend-only token operations.** Token refresh, validation, and all
   Gmail API calls using stored tokens MUST happen exclusively on the
   backend. The frontend never handles tokens directly.
4. **Environment-based encryption keys.** The AES-256 encryption key for
   tokens MUST be stored in an environment variable (`TOKEN_ENCRYPTION_KEY`
   or equivalent), never in code or database.
5. **Refresh token lifecycle.** The backend MUST automatically refresh
   expired access tokens using the stored refresh token. Users MUST NOT be
   prompted to re-authenticate when a token expires — the refresh is
   invisible to them. If a refresh token is revoked by Google or the user,
   the connection status MUST transition to `error` with a clear message
   prompting re-connection.
6. **Audit trail.** Every token read, write, or refresh operation MUST be
   logged with `user_id`, timestamp, and operation type for security
   monitoring.
7. **Revocation on disconnect.** When a user disconnects their Gmail
   account, the system MUST revoke the Google token (Google's revocation
   endpoint) and then delete all stored tokens from the database. Partial
   cleanup (deleting from DB but not revoking) is a security leak.

**Rationale**: OAuth tokens grant access to a user's entire Gmail inbox.
Compromised tokens are equivalent to compromised accounts. Encryption at
rest and backend-only handling ensure tokens are never in a position to be
leaked.

#### Normalized Email Format

Gmail emails MUST be converted into the same canonical message document
used by WhatsApp and the simulate endpoint. The AI pipeline, dashboard,
and database MUST NEVER consume Gmail-specific payloads. The email is
translated at the ingestion boundary:

```json
{
  "userId": "64f...",
  "source": "gmail",
  "sender": "Ali <ali@example.com>",
  "content": "Please review the attached slides before tomorrow.",
  "receivedAt": "2026-09-10T14:30:00Z",
  "externalMessageId": "gmail_msg_abc123",
  "subject": "FYP Slides Review"
}
```

Rules:

1. **`source` is `"gmail"`** — an enum value, never free text. The
   `source` field distinguishes channels; downstream code branches on this
   field.
2. **`sender` is human-readable.** Use the sender's display name from the
   Gmail `From` header when present; fall back to the email address. Format:
   `"Name <email@example.com>"` or just `"email@example.com"` when no name.
3. **`content` is the email body text.** For multipart emails, use the
   `text/plain` part. If only HTML exists, strip tags and store the plain
   text equivalent. Empty body → empty string (never null).
4. **`receivedAt` is server time.** The UTC ISO-8601 timestamp when the
   webhook or polling cycle fetched the email — not the sender-reported
   `Date` header.
5. **`externalMessageId` is Gmail's message ID** (`id` field from the
   Gmail API). It MUST be persisted and MUST key idempotence — duplicate
   fetches produce zero duplicate documents.
6. **`subject` is an extra field for Gmail only.** Emails have subjects;
   WhatsApp messages do not. This field is nullable and MUST NOT be
   required for non-email channels. The dashboard MAY display it when
   present.
7. **`userId` is set server-side.** The owning user is resolved from the
   verified JWT session — never from query parameters or request body
   (Day 18 User Isolation Rules, Day 19 Connection Architecture).
8. **Attachments are NOT ingested in Day 26.** The system reads email body
   text only. Attachment content, filenames, and metadata are not stored or
   processed. This may be extended by explicit amendment.

**Rationale**: Normalization keeps the AI core channel-agnostic. Gmail
emails and WhatsApp messages flow through identical pipelines, receive
identical analysis, and produce identical dashboard cards. The system
cannot be confused by different payload shapes.

#### Connection Ownership

Every Gmail connection MUST belong to exactly one user. The same isolation
rules that apply to WhatsApp connections extend to Gmail:

1. Every Gmail connection document MUST carry a `user_id` field set
   server-side from the verified JWT.
2. Every database query for Gmail connections MUST filter by the
   authenticated user's `user_id` as the first condition.
3. Requests for another user's Gmail connection MUST return 404 with no
   distinction between "not found" and "not yours."
4. Gmail connection deletion MUST only remove the authenticated user's
   connection — never affect other users' connections.
5. The system MUST NOT allow users to see, modify, or detect Gmail
   connections belonging to other users.
6. Gmail tokens MUST be isolated per user — one user's refresh token MUST
   NEVER be used to access another user's Gmail.

#### Email Ingestion Flow

```text
User clicks "Connect Gmail"
  ↓
Backend generates OAuth state + redirects to Google consent screen
  ↓
User grants permission on Google
  ↓
Google redirects back with authorization code
  ↓
Backend exchanges code for access + refresh tokens (server-side only)
  ↓
Tokens encrypted and stored in MongoDB with user_id
  ↓
Connection status → "connected"
  ↓
Backend begins polling / watching for new emails (or webhook)
  ↓
New email received
  ↓
1. Verify it belongs to the connected user
2. Normalize to canonical message format
3. Dedupe on externalMessageId
4. Persist to MongoDB with user_id
5. Trigger AI pipeline asynchronously
6. Dashboard renders from stored analysis only
```

Each step is a distinct responsibility. Token exchange (steps 1-5) happens
once at connection time. Email ingestion (steps 6+) runs continuously while
the connection is active. The AI pipeline and dashboard never touch the
Gmail API directly.

#### What the System MUST NOT Do

- **NEVER ask for or accept Gmail passwords.** OAuth is the only
  authentication mechanism. Any code path that accepts a password is a
  critical security violation.
- **NEVER store tokens in plaintext.** All OAuth tokens MUST be encrypted
  at rest before database storage. Plaintext tokens in code, database,
  logs, or responses are blocking violations.
- **NEVER expose tokens to the frontend.** Tokens MUST NOT appear in API
  responses, browser storage, URL parameters, or developer tools. The
  frontend sees only connection status.
- **NEVER auto-send or auto-reply to emails.** Day 26 is receive-only.
  Outbound email, auto-replies, and draft creation are out of scope.
- **NEVER bypass user consent.** The Google consent screen MUST be shown
  to the user. Tokens obtained without explicit consent are invalid.
- **NEVER use write-scope OAuth permissions.** `gmail.send` and
  `gmail.modify` scopes are forbidden. Only `gmail.readonly` is permitted.
- **NEVER trust client-supplied user IDs.** `userId` for Gmail-derived
  messages is resolved server-side from the verified JWT, never from
  request parameters.
- **NEVER process emails without normalization.** Gmail-specific fields
  (`snippet`, `payload.headers`, `labelIds`) MUST NOT be read by the AI
  pipeline, storage layer, or dashboard. Only the normalized format is used.
- **NEVER skip idempotence.** Duplicate email fetches (from polling
  overlaps, retries, or reconnections) MUST produce zero duplicate
  documents, keyed on `externalMessageId`.
- **NEVER let Gmail tokens persist after disconnect.** When a user
  disconnects, tokens are revoked with Google and deleted from the
  database. Partial cleanup is a security leak.
- **NEVER aggregate Gmail data across users.** Each user's emails are
  isolated. Cross-user email analytics, comparisons, or combined views are
  forbidden (Day 18 User Isolation Rules).
- **NEVER auto-delete old emails.** The system does not manage Gmail
  mailbox state. It reads and stores normalized copies; the original
  emails remain untouched in the user's Gmail account.

#### Quality Bar for Day 26

- **OAuth flow**: The full Connect Gmail → Google consent → token
  exchange → status "connected" flow works end-to-end without errors.
- **Token security**: 100% of OAuth tokens encrypted at rest; zero
  plaintext tokens in database, code, logs, or API responses.
- **Frontend isolation**: Zero tokens, credentials, or raw OAuth data
  visible in API responses, browser storage, or developer tools.
- **User isolation**: Two-user isolation test passes for Gmail — User A
  sees only A's Gmail connection and emails; User B sees only B's.
- **404 semantics**: Requesting another user's Gmail connection by ID
  returns 404 identical to non-existent resource.
- **Normalization fidelity**: A real received Gmail email converts
  losslessly to the canonical format (`source: "gmail"`, `sender`,
  `content`, `receivedAt`, `externalMessageId`, `subject`) — verified
  with a live test email.
- **End-to-end parity**: A Gmail email and a WhatsApp message produce
  identical dashboard cards; the pipeline and dashboard cannot distinguish
  the source (beyond the `source` field).
- **Idempotency**: Re-fetching the same email produces zero duplicate
  documents (keyed on `externalMessageId`).
- **Inbox integration**: Gmail emails appear in the Inbox alongside
  WhatsApp messages, filterable by source ("Gmail" tab), priority, and
  search.
- **Connection lifecycle**: Connect → status "Connected" → Disconnect →
  status "Disconnected" works end-to-end for Gmail.
- **Token refresh**: Backend successfully refreshes expired access tokens
  without user intervention; frontend remains unaware of token lifecycle.
- **Revocation on disconnect**: Disconnecting Gmail revokes the token
  with Google and deletes all stored tokens — verified by re-connecting
  and confirming the old token is invalid.
- **No regression**: WhatsApp and simulate messages continue to work
  identically. The new Gmail channel adds to the system without breaking
  existing channels.

### Day 27 Cross-Platform Dashboard

This section defines the rules for building a unified Cross-Platform
Dashboard that groups all messages by priority, regardless of their source
(WhatsApp, Gmail, etc.). It extends Principle I (Simplicity First),
Principle IV (User Control), Principle VII (Progressive Enhancement), and
the Normalized Message Format from Day 23. Day 27 delivers the central
user-facing view that makes multi-channel communication manageable.

#### Purpose of the Cross-Platform Dashboard

The Cross-Platform Dashboard provides one unified view of all communications
across all connected channels, organized by priority. Users MUST see all
their messages in a single place, grouped by priority level (Urgent,
Important, Normal, Low), with clear source labels showing where each message
came from.

**Success means**: A user opens the Dashboard and immediately sees all
their communications organized by priority — WhatsApp messages, Gmail
emails, and messages from any future channel — in one clean, scannable
view. They can instantly identify what needs attention first, regardless
of the source.

#### Core Organization Principles

1. **Priority-first organization.** The Dashboard MUST group messages by
   priority level (🔴 URGENT, 🟡 IMPORTANT, 🟢 NORMAL, ⚪ LOW) as the
   primary organizational structure. Priority groups are the first thing
   users see — not source, not sender, not time. Messages whose analysis
   is pending, skipped, or absent MUST NOT pollute these groups; they
   render in a clearly separated "Pending analysis" tail instead.
2. **One place for all platforms.** Messages from ALL connected channels
   (WhatsApp, Gmail, and any future channels) MUST appear together in the
   same Dashboard view. No separate pages per channel. The Dashboard is
   source-agnostic — it shows messages, not platforms.
3. **Clear source labels.** Every message card MUST display a clear source
   label (e.g., "WhatsApp", "Gmail") so users immediately know where the
   message came from. The label is informational, not a filter — it does
   not change the card's position in the priority grouping.
4. **Only current user's messages.** The Dashboard MUST show only messages
   belonging to the authenticated user. Every database query for the
   Dashboard filters by `user_id` as the first condition. This extends the
   User Isolation Rules from Day 18.
5. **Simple and clean design.** The Dashboard MUST prioritize scannability
   and clarity. No unnecessary metadata, no complex layouts — just
   messages organized by what matters most. Progressive Enhancement applies:
   the Dashboard MUST load useful data even if the AI service is
   temporarily unavailable (Principle VII).

#### What Each Card Should Show

Every message card in the Cross-Platform Dashboard MUST display these
fields, in this order:

```text
🔴 URGENT
FYP presentation deadline
WhatsApp • Ali
Deadline: Tonight
```

Field mapping rules:

- **Priority indicator**: 🔴 for Urgent, 🟡 for Important, 🟢 for Normal,
  ⚪ (muted styling) for Low. Derived from the stored `ai_analysis.priority`
  — never computed in the UI.
- **Message content or task description**: The key content from the message.
  If tasks were extracted, show the task description (user's own words).
  Otherwise show the AI summary, or a content preview when neither exists.
- **Source label**: Channel name (WhatsApp, Gmail) — always visible,
  always paired with the sender name using the format `Source • Sender`.
- **Sender name**: Who sent the message, from stored metadata.
- **Timestamp**: When the message was received (`receivedAt`), displayed
  as a relative time or formatted date.

Optional fields (shown when present, omitted cleanly when absent — never
rendered as blank space, `null`, or `"undefined"`):

- **Deadline**: If extracted by the AI pipeline. Preserved in original
  wording (`Tonight`, not a computed datetime).
- **Subject**: For Gmail emails. Displayed when present, absent for
  WhatsApp messages.
- **Recommended action**: If available from the AI pipeline. Single
  verb-first sentence, ≤ 15 words.

Additional card rules:

- All card content comes from stored MongoDB data; the Dashboard formats,
  it does not compute.
- The card MUST render completely even when some optional fields are missing
  (Progressive Enhancement applies to the final render too).
- Missing optional fields are omitted cleanly — never rendered as blank
  space, `null`, or `"undefined"`.

#### Rules for Grouping and Ordering

1. **Groups are priority-based.** Messages are grouped into four priority
   sections in fixed order: 🔴 URGENT, 🟡 IMPORTANT, 🟢 NORMAL, ⚪ LOW.
   Messages MUST appear in the correct group based on their AI-assigned
   priority from stored `ai_analysis.priority`. Messages with `priority:
   "pending"` or with missing/absent analysis MUST be rendered in a final,
   clearly separated "Pending analysis" tail — NEVER merged into a
   classified group, because that would inflate the group and misrepresent
   the stored priority.
2. **Within groups, order by recency.** Messages within each priority group
   (and within the Pending tail) are ordered by `receivedAt` timestamp,
   newest first. This ensures the most recent communications are always
   most visible within each priority level.
3. **Empty groups are hidden.** If no messages exist for a priority level,
   that group section is not rendered — never display an empty "No urgent
   messages" group. The Dashboard shows only groups that contain messages.
4. **All sources mix freely.** A WhatsApp message and a Gmail email in the
   same priority group appear side by side with equal visual weight — no
   source-based segregation within groups. The source label identifies
   origin; it does not determine placement.
5. **User isolation is absolute.** Every query for the Dashboard filters by
   the authenticated user's `user_id` as the first condition. Unfiltered
   queries are forbidden. Cross-user message visibility is a critical
   security failure (Day 18 User Isolation Rules).

#### What the System MUST NOT Do

- **NEVER show messages from other users.** The Dashboard is user-scoped.
  Every query MUST filter by the authenticated user's `user_id`. A message
  from another user MUST NEVER appear in the Dashboard — not partially,
  not filtered, not in aggregate.
- **NEVER segregate by source.** Messages from different channels MUST
  appear together in the same priority group. Separate "WhatsApp tab" and
  "Gmail tab" views violate the "one place for all platforms" principle.
  Source filtering is a secondary filter on top of the unified view, not
  a replacement for it.
- **NEVER compute priority in the UI.** The Dashboard reads stored
  `ai_analysis.priority` from MongoDB. It MUST NOT reclassify, re-score,
  or override the AI pipeline's priority in the frontend.
- **NEVER render empty group sections.** Priority groups and the Pending
  tail with zero messages MUST NOT be displayed. Empty groups waste screen
  space and confuse users.
- **NEVER merge pending/unanalyzed messages into classified groups.** A
  message whose analysis is pending, skipped, or absent MUST NOT appear as
  URGENT, IMPORTANT, NORMAL, or LOW. It belongs only in the "Pending
  analysis" tail, where it renders with a pending indicator.
- **NEVER show raw timestamps without formatting.** ISO-8601 strings
  MUST be formatted into human-readable relative time ("2 hours ago") or
  a formatted date. Raw `2026-09-10T14:30:00Z` strings are never shown.
- **NEVER block the Dashboard on AI availability.** Messages with pending
  or failed AI analysis MUST still appear on the Dashboard with available
  fields. The Dashboard reads stored data only — it MUST NOT invoke AI
  agents or recompute analysis (Complete AI Pipeline rules).
- **NEVER invent message content.** Card content comes from stored MongoDB
  data only. The Dashboard MUST NOT generate, complete, or guess message
  text, sender names, or any other field.
- **NEVER bypass idempotence or normalization.** The Dashboard is a
  read-only consumer. It does not write to the messages collection, does
  not trigger re-analysis, and does not modify stored data.

#### Quality Bar for Day 27

- **Unified view**: All messages from all connected channels appear in one
  Dashboard view — no separate pages per channel. Verified by sending a
  WhatsApp message and a Gmail email and confirming both appear in the
  same Dashboard.
- **Priority accuracy**: Messages are grouped by their AI-assigned priority
  level; the group matches the stored `ai_analysis.priority` value. 100%
  match between stored priority and displayed group. Pending/skipped
  messages appear only in the Pending tail, never in a classified group.
- **Source visibility**: 100% of message cards display a clear source label
  (WhatsApp, Gmail) paired with the sender name.
- **User isolation**: Two-user isolation test passes — User A sees only
  A's messages; User B sees only B's messages. Verified through both the
  UI and direct API calls, including guessed object IDs.
- **Recency ordering**: Messages within each priority group are ordered by
  `receivedAt`, newest first. Verified by inserting messages with known
  timestamps and confirming display order.
- **Empty state**: When no messages exist, show a clear "No messages yet"
  state — not broken layouts or empty group sections.
- **Missing field handling**: Cards render completely when optional fields
  (deadline, subject, recommendation) are absent. No blank spaces, null
  values, or "undefined" text.
- **Responsive design**: Dashboard works on desktop and mobile widths.
  Priority groups stack vertically; cards remain readable at all widths.
- **Performance**: Dashboard loads in under 2 seconds for up to 100
  messages. No blocking on AI service availability.
- **No regression**: WhatsApp, Gmail, and simulate messages continue to
  work identically through the same normalized ingest path. The Dashboard
  adds a new view without breaking existing flows.

### Day 28 Analytics

This section defines the rules for building a professional Analytics /
Communication Overview section. It extends Principle I (Simplicity First),
Principle IV (User Control), Principle V (Security and Privacy), and
Principle VII (Progressive Enhancement). Day 28 transforms raw message data
into meaningful insights that help users understand their communication
patterns and make better decisions about where to focus their attention.

#### Purpose of Analytics

The Analytics page provides a focused, read-only view of the user's
communication data — message volumes, priority distributions, source
breakdowns, and task completion trends. It answers three questions every
user has: How much am I communicating? What needs my attention? Am I
keeping up?

**Success means**: A user opens the Analytics page and immediately sees
accurate, real-time numbers that reflect their actual communication
patterns. The page loads fast, looks professional, and gives actionable
insight without requiring any configuration or AI interaction.

#### Core Analytics Principles

1. **Data must be real, not sampled.** Every number on the Analytics page
   MUST be computed from the authenticated user's actual stored messages
   and tasks in MongoDB. The system MUST NOT use estimated, cached
   (stale beyond the current session), or projected numbers. When the
   user has 247 messages, the page shows 247 — not "approximately 250".
2. **User isolation is absolute.** Analytics queries MUST filter by the
   authenticated user's `user_id` as the first condition. Cross-user
   aggregation, comparison, or combined statistics are forbidden (Day 18
   User Isolation Rules). The system MUST NOT produce cross-user
   benchmarks, leaderboards, or anonymized aggregate views.
3. **Simplicity over sophistication.** Analytics MUST present clear,
   direct numbers and straightforward charts. No complex statistical
   models, no predictive analytics, no AI-generated insights beyond what
   the existing pipeline already stores. The goal is clarity, not
   analytical depth.
4. **Clean, professional design.** The Analytics page MUST look polished
   and intentional — consistent with the dark theme, card-based layout,
   and visual language established across Dashboard, Inbox, Tasks, and
   Connections. Numbers MUST be prominently displayed; charts MUST be
   clean and readable.
5. **Progressive Enhancement.** The Analytics page MUST load useful data
   even if the AI service is temporarily unavailable. Charts and counters
   that depend on stored analysis data render normally; features that
   would require additional computation degrade gracefully (Principle VII).

#### What Metrics Should Be Shown

The Analytics page MUST display the following sections:

**Communication Overview — Summary Cards**

| Metric | Definition |
|---|---|
| Total Communications | Count of all messages belonging to the authenticated user (all sources, all time or filtered period) |
| Urgent | Count of messages with `ai_analysis.priority = "urgent"` |
| Important | Count of messages with `ai_analysis.priority = "important"` |
| Normal | Count of messages with `ai_analysis.priority = "normal"` |
| Low Priority | Count of messages with `ai_analysis.priority = "low"` |

Rules for summary cards:
- Counts MUST be exact integers computed from MongoDB aggregation on the
  user's `messages` collection, filtered by `user_id`.
- The cards MUST show the current period context (e.g., "This Week",
  "All Time") and the user MUST be able to toggle between time periods.
- Pending/skipped/absent analysis messages MUST be counted separately
  and shown as "Pending" — never merged into a priority group.

**Charts**

| Chart | Type | Data |
|---|---|---|
| Communications by Source | Bar or pie chart | Message count grouped by `source` field (whatsapp, gmail, etc.) |
| Priority Distribution | Bar or pie chart | Message count grouped by `ai_analysis.priority` (urgent, important, normal, low, pending) |
| Task Completion | Counter or progress indicator | Count of tasks marked completed vs total tasks extracted for the user |
| Response / Attention Trends | Line or bar chart | Message volume over time (daily or weekly buckets), optionally segmented by priority |

Rules for charts:
- Charts MUST use a lightweight charting library (e.g., recharts, Chart.js)
  that renders client-side — no server-side image generation.
- Chart data MUST be fetched from a dedicated analytics API endpoint that
  performs MongoDB aggregation server-side. The frontend MUST NOT compute
  analytics from raw message lists.
- Charts MUST handle empty states (zero messages) gracefully — show "No
  data yet" rather than broken or empty chart containers.
- Charts MUST be responsive and readable on both desktop and mobile widths.

#### Analytics API Contract

The backend MUST expose a single analytics endpoint:

```text
GET /analytics?period=week|month|all
```

Response:

```json
{
  "period": "week",
  "total": 247,
  "byPriority": {
    "urgent": 12,
    "important": 38,
    "normal": 151,
    "low": 46
  },
  "bySource": {
    "whatsapp": 180,
    "gmail": 67
  },
  "tasks": {
    "total": 42,
    "completed": 28
  },
  "trends": [
    { "date": "2026-09-05", "count": 34 },
    { "date": "2026-09-06", "count": 41 }
  ]
}
```

Rules:
- The endpoint MUST require authentication (JWT cookie) — unauthenticated
  calls return 401.
- The `user_id` filter MUST be applied server-side as the first condition
  in every aggregation pipeline.
- The `period` parameter filters by `receivedAt`: `week` = last 7 days,
  `month` = last 30 days, `all` = no time filter. Default is `week`.
- The response MUST include only the authenticated user's data. Zero
  cross-user aggregation.
- The endpoint MUST respond within 500ms for up to 10,000 messages
  (MongoDB aggregation with proper indexes).

#### What the System MUST NOT Do

- **NEVER show cross-user analytics.** Every query filters by
  `user_id`. Cross-user statistics, combined views, or anonymized
  aggregates are forbidden — even if the data appears de-identified.
- **NEVER compute analytics in the frontend from raw message lists.**
  The frontend MUST fetch pre-aggregated data from the analytics API
  endpoint. Fetching all messages and computing counts client-side is
  forbidden — it leaks data and performs poorly at scale.
- **NEVER use estimated or cached (stale) numbers.** Analytics counts
  MUST reflect the current state of the database. Stale cached counts
  that do not update when messages arrive are a data accuracy violation.
- **NEVER display analytics for other users.** A bug, misconfigured
  query, or missing `user_id` filter that causes one user to see another
  user's analytics is a critical security failure.
- **NEVER store analytics results permanently.** Analytics are computed
  on demand from stored message data. The system MUST NOT create a
  separate analytics collection that could drift out of sync with the
  source data.
- **NEVER require AI to render analytics.** Charts and counters MUST
  work from stored `ai_analysis.priority` values and message metadata.
  If the AI service is down, previously analyzed messages still appear
  in analytics; only newly arriving messages may show as "pending".
- **NEVER add AI-generated narrative insights.** Analytics MUST show
  numbers and charts — not AI-written summaries like "Your communication
  volume increased this week." The user interprets the data; the system
  presents it.

#### Quality Bar for Day 28

- **Data accuracy**: 100% — every count on the Analytics page MUST match
  the result of a direct MongoDB count query on the user's messages with
  the same filters. No rounding, no estimation, no stale cache.
- **User isolation**: Two-user isolation test passes for analytics —
  User A sees only A's communication statistics; User B sees only B's.
  Verified by registering two users, creating messages for each, and
  confirming their analytics pages show different numbers.
- **Performance**: Analytics API responds within 500ms for up to 10,000
  messages. Charts render within 1 second of data arrival.
- **Empty state**: When a user has zero messages, the Analytics page
  shows "No data yet" with a helpful prompt — not broken charts or zero
  counts in misleading layouts.
- **Time period toggle**: Switching between "This Week", "This Month",
  and "All Time" updates all summary cards and charts instantly without
  a full page reload.
- **Responsive design**: Analytics page works on desktop and mobile
  widths. Summary cards stack vertically on small screens; charts resize
  proportionally.
- **Chart readability**: Charts use clear labels, readable fonts, and
  sufficient color contrast against the dark theme. No unlabeled axes,
  no ambiguous color coding.
- **Source breakdown accuracy**: The "Communications by Source" chart
  MUST show accurate counts per source (whatsapp, gmail, etc.) that sum
  to the total communications count.
- **No regression**: Dashboard, Inbox, Tasks, and Connections continue
  to work identically. The Analytics page is a new read-only view that
  adds to the system without modifying existing flows.

### Day 29 Security & Reliability Hardening

This section defines the rules for the security-hardening and
reliability-verification phase. It extends Principle V (Security and
Privacy), Principle VII (Progressive Enhancement), the Day 18 User
Isolation Rules, the Day 23 webhook security rules, and the Day 24
Orchestrator fallback rules. Day 29 adds no new features — it proves the
non-negotiables hold under attack and under failure.

#### Purpose of Security + Testing

All core features are built. Day 29 verifies critical behaviors that the
system has relied on silently until now: isolation cannot be broken, bad
webhook input is rejected at the door, a failing AI never loses data, and
duplicate deliveries never multiply documents. Security and reliability
are verified behavior, not declared intent.

**Success means**: Four critical tests pass:

1. **Authentication & User Isolation** — User A MUST NOT access User B's
   messages (or tasks, analyses, connections, analytics) through the UI
   or direct API, including guessed object IDs.
2. **Webhook Security** — Invalid signature or malformed webhook requests
   are rejected before parsing or storage.
3. **AI Reliability** — When the AI is unavailable, the message is still
   stored and retried later; zero data loss.
4. **Duplicate Prevention** — The same message received twice produces one
   document, keyed on `externalMessageId`.

#### Core Security Principles

1. **Isolation is an invariant, not a feature.** User A MUST NEVER read,
   write, detect, or infer User B's data — at the database layer (first
   filter `user_id`), the API layer (404 for not-yours, indistinguishable
   from not-found), the UI layer, logs, and caches. A single broken
   boundary is a release-blocking failure (Day 18 rules apply unchanged).
2. **Deny by default at the boundary.** Every endpoint — especially
   webhooks and OAuth callbacks — MUST require explicit, verifiable
   credentials before any parsing. Requests without valid authentication
   or signatures are rejected (401/403) and never partially processed.
3. **Clear rejection over silent acceptance.** Invalid, ambiguous, or
   malformed requests MUST fail loudly with an explicit status code and a
   safe, generic error. The system MUST NOT accept a bad request "just in
   case" and process it partially.
4. **Fail closed.** On any verification failure (missing signature, expired
   token, malformed payload) the outcome is rejection or a retry-safe
   acknowledgement — never degraded, read-only, or half-written state.
5. **Secrets stay server-side.** Signing secrets, API keys, and verify
   tokens live in environment variables only; they are never returned to
   clients or written to logs, responses, or the database in plaintext
   (Days 19, 22, 23, 26 rules extend).

#### Reliability Principles (AI Failure Handling)

1. **Store first, analyze later.** Ingestion MUST persist the message to
   MongoDB with its server-set `user_id` and identity fields BEFORE any AI
   work. An AI outage MUST NOT lose a message.
2. **AI failure softens, never erases.** When analysis fails or the
   provider is unavailable, the message MUST be stored with
   `ai_analysis` in a pending state (or its documented fallback), MUST
   remain visible on the dashboard, and MUST be retried later. Zero data
   loss is the bar.
3. **Never block ingestion on AI.** The webhook/ingest path MUST respond
   200 once the message is validated and stored; analysis runs
   asynchronously (Day 23/24 rules). A slow or downed AI service never
   delays or drops ingestion.
4. **Retries are idempotent.** Background retry of a pending analysis MUST
   update the same stored document — never insert a second copy (see
   Duplicate Prevention below).
5. **Degradation is observable.** Pending/retry state MUST be visible to
   the user (e.g., a "pending analysis" tail on the dashboard) and in the
   stored document, so a silent failure never masquerades as success.

#### Duplicate Prevention Rules

1. **`externalMessageId` is the idempotence key.** Every provider message
   (WhatsApp `wamid`, Gmail message id, simulate payload id) MUST have its
   unique identifier persisted at ingest, set server-side.
2. **Dedupe before insert.** The ingest path MUST check for an existing
   document with the same `externalMessageId` (user-scoped) before writing.
   On match, the delivery is acknowledged (200 for webhooks) and skipped —
   no duplicate document, no re-analysis.
3. **Dedupe covers every reprocessing path.** Meta redeliveries, Gmail
   polling overlaps, AI-failure retries, and user-triggered re-analysis
   MUST all converge on the same stored document — never a new one.
4. **The database is the final authority.** A unique index on the
   user-scoped dedupe key (e.g., `{user_id, externalMessageId}`) MUST back
   the application check so a race can never insert a duplicate.
5. **Key-less messages get a deterministic key.** Messages without a
   provider ID (simulate, legacy data) MUST derive a deterministic identity
   server-side (e.g., hash of `user_id` + `source` + `sender` + `content` +
   `receivedAt`) or be explicitly exempted — never silently duplicated.

#### What MUST NOT Happen

- **NEVER leak across users.** Any code path that lets User A read, guess,
  or enumerate User B's data — including via guessed object IDs, error
  messages, logs, or timing differences — is a release-blocking breach.
- **NEVER process an unverified webhook.** Requests with invalid or missing
  signatures, or malformed payloads, are rejected before parsing or
  storage; partial processing is forbidden.
- **NEVER lose a message to AI failure.** An AI timeout, 429, provider
  outage, or malformed model output MUST NOT drop a message; pending state
  plus retry is the only acceptable outcome.
- **NEVER insert a duplicate.** A repeated delivery, AI-failure retry, or
  polling overlap MUST produce zero new documents.
- **NEVER block ingestion on AI.** The request path never waits on or fails
  because of the AI service.
- **NEVER degrade silently.** Rejections, pending analysis, and retries
  MUST be explicit in responses and stored state — quiet acceptance and
  quiet drops are failures.

#### Quality Bar for Day 29

- **Isolation test**: The two-user A/B test passes for messages, tasks,
  connections, and analytics — via UI and direct API, including guessed
  object IDs. A sees zero of B's data; 404 responses are indistinguishable
  from "not found" (Day 18 bar).
- **Webhook rejection**: Requests with invalid signature, missing
  signature, or malformed body are rejected (403/400) before any
  processing — verified with a suite of negative payloads.
- **AI-outage recovery**: With the AI provider mocked to fail (timeout /
  429 / hard error), a message is still stored with pending state, remains
  visible on the dashboard, and is completed (document updated, no
  duplicate) when the provider is restored.
- **Duplicate idempotence**: Delivering the same `externalMessageId` twice
  (webhook redelivery, poll overlap, retry) yields exactly one document —
  verified at the application layer and backed by the unique index.
- **No regression**: The full backend suite (`backend/tests/`) and the
  frontend vitest suite stay green; Dashboard, Inbox, Tasks, Connections,
  and Analytics continue to work identically.

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

- End-to-end flow verified: message → Orchestrator → selected agents → MongoDB → dashboard card
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
- [ ] Every incoming message is routed by the AI Orchestrator; selected agents run in fixed order (Priority first, Recommended Action last)
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
- [ ] Inbox displays only messages belonging to the authenticated user (user isolation)
- [ ] Priority tabs (All, Urgent, Important, Normal, Unread) filter correctly
- [ ] Source filtering works in combination with priority tabs
- [ ] Search bar searches across sender, subject, and content fields
- [ ] Active filters are clearly indicated with visual feedback
- [ ] One-click reset clears all filters and returns to default view
- [ ] Filter counts show accurate numbers for each tab/filter
- [ ] Empty states display "No messages found" when no messages match filters
- [ ] Loading states show skeleton loaders during initial load
- [ ] Inbox works responsively on desktop and mobile widths
- [ ] Filter tabs and search bar are keyboard navigable
- [ ] Tasks page displays only tasks belonging to the authenticated user (user isolation)
- [ ] Task priority indicators (🔴, 🟡, 🟢) match AI pipeline classification
- [ ] Task descriptions and deadlines preserve original AI extraction wording
- [ ] Complete action marks task as completed and removes from active list
- [ ] Snooze action updates task deadline and keeps task in active list
- [ ] View message action navigates to original source message
- [ ] Task actions are one-click operations without confirmation dialogs
- [ ] Empty tasks state shows "No tasks found" with helpful guidance
- [ ] Task list loads in under 1 second for up to 100 tasks
- [ ] Task list works responsively on desktop and mobile widths
- [ ] Task actions are keyboard navigable
- [ ] Webhook POST requests are validated with Meta's `X-Hub-Signature-256`; invalid or missing signatures are rejected before parsing
- [ ] Incoming webhook messages are normalized to the canonical format (`userId`, `source`, `sender`, `content`, `receivedAt`, `externalMessageId`) before storage or processing
- [ ] `externalMessageId` keys idempotence — duplicate webhook deliveries produce zero duplicate documents
- [ ] Webhook responds 200 quickly; the AI pipeline runs asynchronously and never blocks the Meta response
- [ ] Raw Meta webhook payloads are never stored long-term or exposed to the frontend
- [ ] `user_id` for webhook-derived messages is resolved server-side from verified credentials, never from query parameters or body
- [ ] No WhatsApp-specific fields (`text.body`, `wa_id`) are referenced by the AI pipeline, storage layer, or dashboard
- [ ] Simulated messages continue to flow through the same normalized ingest path without regression
- [ ] Every incoming message flows through the single AI Orchestrator; zero direct agent calls exist outside it
- [ ] The Orchestrator routes each message to the minimal agent subset it needs; Priority is never skipped
- [ ] Orchestration adds zero extra LLM round-trips; total pipeline latency stays within the ≤ 10 second budget
- [ ] Skipped agents store documented fallback values and an explainable `routing` note; no fabricated outputs
- [ ] The Orchestration layer is a single function/path — no multi-agent framework, no scattered AI calls
- [ ] Every message stores `messageId`, `threadId`, and `conversationId` (nullable where not applicable), all set server-side — never client-supplied
- [ ] Messages are linked only by the deterministic rule (same user + source + sender + bounded time window); zero LLM-invented links
- [ ] Context enters analysis inside the existing single LLM call — no extra round-trips, no second agent
- [ ] Context-enriched fields carry an explanation naming the linked message(s) and are dismissible by the user
- [ ] Threads/conversations never span users; linked messages stay individually owned, queryable, and deletable (isolation)
- [ ] No vector store, embeddings, RAG, or long-term memory layer is used for context (Simplicity First)
- [ ] Link-resolution failure degrades gracefully — the message is analyzed standalone and ingestion never blocks
- [ ] Gmail connection uses ONLY Google OAuth 2.0; no passwords are asked for, accepted, stored, or logged
- [ ] Gmail OAuth requests only `gmail.readonly` scope; write scopes (`gmail.send`, `gmail.modify`) are not requested
- [ ] Gmail OAuth tokens (access + refresh) are encrypted at rest with AES-256 before database storage
- [ ] No Gmail tokens, credentials, or raw OAuth data appear in API responses, browser storage, or developer tools
- [ ] Gmail token refresh happens backend-only; users are not prompted to re-authenticate on token expiry
- [ ] Gmail emails are normalized to canonical format (`source: "gmail"`, `sender`, `content`, `receivedAt`, `externalMessageId`, `subject`) before storage
- [ ] Gmail `externalMessageId` keys idempotence — duplicate email fetches produce zero duplicate documents
- [ ] Gmail connection carries `user_id` set server-side from JWT; every Gmail query filters by `user_id`
- [ ] Requesting another user's Gmail connection by ID returns 404 identical to non-existent resource
- [ ] Gmail disconnect revokes the token with Google and deletes all stored tokens from the database
- [ ] Gmail emails appear in the Inbox alongside WhatsApp messages, filterable by source and priority
- [ ] Cross-Platform Dashboard groups messages by priority (🔴 URGENT, 🟡 IMPORTANT, 🟢 NORMAL, ⚪ LOW) as the primary organizational structure; pending/unanalyzed messages render only in a separated "Pending analysis" tail
- [ ] Messages from all connected channels (WhatsApp, Gmail) appear together in the same Dashboard view — no separate pages per channel
- [ ] Every message card displays a clear source label (WhatsApp, Gmail) paired with the sender name
- [ ] Dashboard shows only messages belonging to the authenticated user (user isolation); every query filters by `user_id` as first condition
- [ ] Messages within each priority group are ordered by `receivedAt` timestamp, newest first
- [ ] Empty priority groups are hidden — never displayed as empty sections
- [ ] Dashboard renders from stored MongoDB data only; it does NOT invoke AI agents or recompute analysis
- [ ] Analytics queries filter by authenticated user's `user_id` as first condition (user isolation)
- [ ] Analytics counts are exact — computed from MongoDB aggregation on user's messages, not estimated or cached
- [ ] Cross-user analytics aggregation is forbidden — every metric is scoped to the authenticated user only
- [ ] Analytics endpoint requires authentication; unauthenticated calls return 401
- [ ] Two-user isolation A/B test passes for messages, tasks, connections, and analytics (guessed IDs included) — User A never sees User B's data
- [ ] Invalid or missing webhook signatures and malformed payloads are rejected before any parsing or storage
- [ ] AI outage/failure stores the message with pending state, keeps it visible, and retries later — zero message loss
- [ ] Duplicate `externalMessageId` deliveries produce zero duplicate documents (user-scoped check backed by a unique index)

**Version**: 1.18.0 | **Ratified**: 2026-08-19 | **Last Amended**: 2026-09-11
