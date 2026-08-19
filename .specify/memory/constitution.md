<!--
Sync Impact Report
==================
Version change: N/A → 1.0.0 (initial creation)
Modified principles: N/A (new document)
Added sections:
  - Core Mission
  - Development Principles (7 principles)
  - Technical Principles
  - Quality Bar
  - Decision Guidelines
  - Governance
Removed sections: N/A
Templates requiring updates:
  - .specify/templates/plan-template.md ✅ verified (Constitution Check section present)
  - .specify/templates/spec-template.md ✅ verified (requirements format compatible)
  - .specify/templates/tasks-template.md ✅ verified (task structure compatible)
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

**Version**: 1.0.0 | **Ratified**: 2026-08-19 | **Last Amended**: 2026-08-19
