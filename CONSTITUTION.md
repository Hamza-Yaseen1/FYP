# Communication AI Constitution

## Core Mission

Build an Agentic AI system that helps users manage communication overload.
The system receives messages from multiple channels (WhatsApp, Gmail, etc.),
prioritizes them intelligently, extracts tasks and deadlines, and presents
users with a clean dashboard showing only what needs their attention.

**Success means**: Users spend less time triaging messages and more time
acting on what matters.

---

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

---

## AI Feature Guidance

This section provides focused rules for the two AI features being built
on Days 11-12: Task Extraction and Urgency + Deadline Detection.
These rules extend Principle III (AI is Assistive, Not Magical) and
the existing AI Behavior Rules in SPEC.md.

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

---

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

---

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

---

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

---

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

### Compliance Checklist

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

**Version**: 1.1.0 | **Ratified**: 2026-08-19 | **Last Amended**: 2026-08-20
