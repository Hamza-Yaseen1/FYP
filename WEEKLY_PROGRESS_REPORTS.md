# Weekly Progress Reports — Communication AI Platform

**Student**: Hamza Yaseen
**Project**: Communication AI Platform ("Signal Desk")

> **Important note on the timeline**: These 8 weekly reports are **reconstructed
> from the repository's git history, feature specs, plans, and documentation**
> rather than from day-by-day running logs. They reflect the *logical* order in
> which the features were specified and built, matched to the actual git commit
> dates and the `specs/` branch sequence. Week boundaries group related
> milestones into a sensible progression. Where a specific date or source is
> not directly verifiable, it is clearly labelled as reconstructed or inferred.

---

# Week 1 — Project Planning & Architecture

## Objectives

- Define the core product clearly before writing any code.
- Establish the project's main concept: an AI-powered communication manager.
- Decide the central priority model and the "Needs Your Attention" idea.
- Create the foundational project rules (the "Constitution") and baseline specification.

## Work Completed

- Wrote the core product definition (`docs/day1-core-product.md`) describing priority levels (Urgent / Important / Normal / Low), their meanings, colours, and example messages.
- Defined the central concept: a message "Needs Your Attention" when it is Urgent, or Important with a clear task/deadline.
- Created the baseline feature specification (`SPEC.md`) capturing user stories, functional requirements, success criteria, priority definitions, and AI behaviour rules.
- Published the **Communication AI Constitution** (`CONSTITUTION.md`) — a set of development principles (Simplicity First, Vertical Slices, AI is Assistive, User Control, Security & Privacy, Clean Code, Progressive Enhancement).
- Planned the technology stack: Next.js frontend, FastAPI backend, MongoDB, and an LLM-based AI layer.

## Technical Work

- Documented the architecture as a **monorepo** with `app/` (frontend) and `backend/` (API).
- Defined four priority levels with clear, evidence-based rules so AI classification could later be consistent.
- Set performance baselines (dashboard < 3 s, API < 500 ms excluding AI, AI never blocks the UI).
- Established the "single LLM call" and "AI is advisory and explainable" principles that shaped all later AI work.

## Challenges Faced

- Designing an AI classification scheme that is simple yet reliable, without over-engineering an FYP.

## Research and Investigation

- Compared possible LLM providers (documented in `specs/1-baseline-spec/research.md`): OpenAI (default), Groq, and Gemini as alternatives; Anthropic, local models (Ollama), and Hugging Face were considered and set aside.
- Explored how to structure prompts so AI output can be reliably parsed (structured JSON vs free text vs function calling).

## Solution

- Selected a provider abstraction (`BaseLLMProvider`) so providers can be swapped.
- Chose structured JSON prompt outputs validated with Pydantic.
- Adopted synchronous analysis (adequate for FYP scale) instead of a complex async queue.

## Key Learning

- Planning and clear principles before coding prevent rework and keep the project demo-able at every stage.

## Outcome

- A documented, reviewable foundation: product definition, spec, constitution, and an implementation plan for the AI layer.

## Next Steps

- Set up the initial Next.js and FastAPI project scaffold, then build the first vertical slice (simulated messages appearing on a dashboard).

---

# Week 2 — Initial Project Setup & Message Dashboard

## Objectives

- Set up the Next.js frontend and FastAPI backend project scaffolds.
- Create the MongoDB database connection.
- Build the first vertical slice end-to-end: a simulated message enters the system and appears on a dashboard.

## Work Completed

- Initialised the FastAPI backend with health check, CORS, and MongoDB (Motor) connection (`backend/main.py`, `backend/database.py`).
- Built the REST message endpoints (create, list, counts, senders, sources).
- Created the message simulation path so messages from different channels can be tested without real integrations.
- Built the Next.js dashboard page showing recent messages, a message simulation form, and health status.
- Created the frontend API client (`lib/api.ts`) with `credentials: include` for session handling.

## Technical Work

- Set up async MongoDB access with Motor and defined collections (`messages`, `users`, `tasks`, `connections`, `ai_analysis`).
- Added MongoDB indexes for email uniqueness, message sorting, and text search.
- Implemented a message data model and Pydantic request/response validation (`backend/models/message.py`).
- Implemented RESTful endpoints in `backend/routes/messages.py`.

## Challenges Faced

- Configuring and connecting the Python backend to MongoDB correctly (URI, database name, environment variables).

## Research and Investigation

- FastAPI + Motor async database documentation.
- MongoDB index creation.

## Solution

- Moved connection settings into environment variables with documented `.env`/`.env.example` files and a default local URI fallback.
- Created indexes at application startup in the FastAPI lifespan.

## Key Learning

- Separating configuration from code and validating required secrets early avoids confusing runtime failures.

## Outcome

- A working full-stack "hello world" of the product: messages can be created (simulated) and displayed on the dashboard.

## Next Steps

- Add the first AI feature: automatic priority classification of messages.

---

# Week 3 — AI Priority Classification

## Objectives

- Integrate the Groq LLM and enable automatic priority classification of incoming messages.
- Show priority on the dashboard with a clear visual badge and confidence level.

## Work Completed

- Implemented the AI provider abstraction (`backend/services/ai/providers/`) and a working Groq provider.
- Added the priority classification prompt (`prompts/priority.txt`) and the AI orchestrator (`services/ai/analyzer.py`).
- Extended the message response model with an `ai_analysis` document containing `priority`, `confidence`, and `explanation`.
- Updated the dashboard/inbox to display a priority badge with confidence.
- Created the **Priority Agent Constitution** (`docs/priority-agent-constitution.md`) documenting strict classification rules.

## Technical Work

- Added the Groq dependency and `GROQ_API_KEY` configuration.
- Implemented structured JSON prompting with normalisation of priority aliases (`normalize_priority`) and robust response cleaning (`clean_response`).
- Triggered analysis synchronously at message ingestion so the stored message carries its AI result.

## Challenges Faced

- AI analysis was returning a useless fallback instead of real results (see `AI-FIX-SUMMARY.md`).

## Research and Investigation

- Groq API usage.
- Prompt engineering for reliable structured JSON output.

## Solution

- Fixed the provider prompt to request all required fields, validated the API key, and added detailed logging and safe field defaults.

## Key Learning

- An analysis call is only as good as its prompt; asking for everything up-front with defaults beats patching missing fields later.

## Outcome

- Messages are automatically classified as Urgent / Important / Normal / Low with confidence and explanation, shown on the dashboard.

## Next Steps

- Extract actionable tasks and deadlines from messages, and add summaries.

---

# Week 4 — Task Extraction, Deadline Detection & Summaries

## Objectives

- Extract clear, actionable tasks from messages with their deadlines.
- Detect relative time expressions and convert them to useful deadline information (without inventing dates).
- Generate concise one-sentence summaries.

## Work Completed

- Added the Task model and task extraction logic (`backend/models/task.py`, prompts).
- Implemented **task extraction** and **urgency + deadline detection** rules (documented in `CONSTITUTION.md`).
- Added the summary generation prompt and summary display in the message cards.
- Developed the "Needs Attention" evaluation (`services/ai/attention.py`) with two rules (task + near deadline, or urgent + task).
- Added tests for task extraction and priority edge cases.

## Technical Work

- The AI returns extracted tasks with `description`, `deadline` (preserved exactly as stated, `null` if none), and `priority_indicator`.
- Strict "no invented tasks / no invented deadlines" behaviour to guarantee zero hallucinated dates.
- Derived `needs_attention` from stored analysis (pure functions, no LLM needed).

## Challenges Faced

- Ensuring the AI never invents tasks or deadlines (false positives and hallucinated dates are critical failures).

## Research and Investigation

- Prompt rules for conservative task/deadline extraction (documented in the constitution and the task-extraction spec).
- Time-expression semantics ("ASAP", "tonight", "by Friday", "next week").

## Solution

- Enforced explicit prompt rules: only extract explicitly requested actions, preserve deadline wording verbatim, and default to empty/null when uncertain. Verified with edge-case tests.

## Key Learning

- Trust in an AI assistant is built by being conservative and explainable — never guessing urgency or dates.

## Outcome

- Messages now produce reliable tasks, deadlines, and summaries, with an attention flag for the user's view.

## Next Steps

- Add recommended actions and complete the unified AI pipeline so all intelligence comes from a single call.

---

# Week 5 — Recommended Actions & the Complete AI Pipeline

## Objectives

- Suggest a recommended next action for each message.
- Combine priority, tasks, deadlines, summary, and recommended action into a **single** AI call.

## Work Completed

- Added the recommended-action prompt and display "Move on" actions in the UI.
- Refactored the analysis into one combined call returning all fields together.
- Added the attention dashboard ("Needs Your Attention") view.
- Wrote integration tests for the complete AI pipeline.

## Technical Work

- Adapted the provider prompt (`ANALYSIS_PROMPT`) to produce all fields in one JSON response: priority, confidence, explanation, summary, tasks, deadlines, and recommended action.
- Implemented response parsing into a Pydantic `AIAnalysisResult`.
- Kept the recommendation language matching the source message and never inventing actions.

## Challenges Faced

- Keeping one call reliable while returning many fields, and handling AI rate limits gracefully.

## Research and Investigation

- Structured JSON prompting and robust parsing.
- Error handling for LLM failures (rate limits, API downtime).

## Solution

- Designed a single comprehensive prompt with explicit field contracts.
- The analyzer detects rate-limit errors and falls back to safe defaults with `status: "pending"`, never losing the message.

## Key Learning

- Consolidating AI output into one call dramatically reduces latency and cost while staying reliable.

## Outcome

- A complete, unified AI pipeline delivering all five intelligence outputs from one LLM call, plus the attention view.

## Next Steps

- Add user accounts, login, and strict per-user data isolation so data is private.

---

# Week 6 — User Authentication & Data Isolation

## Objectives

- Add secure registration, login, and logout.
- Protect dashboard routes from unauthenticated access.
- Enforce strict per-user data isolation.

## Work Completed

- Added the `User` model and registration/login/logout endpoints (`backend/routes/auth.py`).
- Implemented JWT tokens stored in **httpOnly cookies** and bcrypt password hashing (`services/security.py`).
- Added the `get_current_user` dependency used to authenticate every protected route.
- Added Next.js route protection (`middleware.ts`) redirecting unauthenticated users to `/login`.
- Implemented per-user scoping on every message, task, and connection query.
- Added `test_auth.py` and `test_user_isolation.py`.

## Technical Work

- JWT with HS256 and 7-day expiry; httpOnly, SameSite cookie for session storage.
- Every route uses `current_user = Depends(get_current_user)` and filters queries by `user_id`.
- Logout clears the cookie even when the token is invalid.

## Challenges Faced

- Designing a secure yet simple session mechanism, and verifying isolation between users.

## Research and Investigation

- JWT and bcrypt best practices; secure cookie flags (httpOnly, SameSite).
- Preventing cross-user data leakage in MongoDB queries.

## Solution

- Used httpOnly cookies (protected from XSS), constant-time password verification, and user-scoped queries on all data access. Tests confirmed no user can access another's records.

## Key Learning

- Data isolation must be enforced at the database-query level, not just hidden in the UI.

## Outcome

- Full authentication with route protection and verified per-user data isolation.

## Next Steps

- Improve the inbox UX (filters, tabs), add task management (status, snooze), and model external connections.

---

# Week 7 — Better Inbox, Task Management & Connections Architecture

## Objectives

- Build a richer inbox with priority tabs, filters, and search.
- Add full task management (complete, snooze, view source).
- Model external connection accounts (WhatsApp, Gmail, LinkedIn) with an architecture for linking channels.

## Work Completed

- Reworked the inbox with priority tabs (All / Urgent / Important / Normal / Unread) with live counts, plus source, priority, sender, and date-range filters and search.
- Added the `tasks` collection and task endpoints (list, status update, delete, snooze, source message).
- Added priority-tab counts and multi-filter backend aggregation (`/messages/counts`, `/messages/senders`).
- Added the `connections` architecture: provider enum, connection model, and connection endpoints.
- Added AES encryption for stored connection tokens (`utils/encryption.py`).

## Technical Work

- Aggregation pipelines for filter counts and priority-based task sorting.
- Snooze functionality computed from `snoozed_until` timestamps.
- Unique per-user-per-provider index on connections.
- Task-to-message linking via `source_message_id`.

## Challenges Faced

- Writing efficient aggregation queries for filter counts and ensuring correct per-user behaviour.

## Research and Investigation

- MongoDB aggregation framework.
- Design of a multi-channel connection architecture.

## Solution

- Used indexed queries and aggregation pipelines scoped by `user_id`; kept tasks and connections cleanly separated models.

## Key Learning

- A well-designed data model (separate collections, clear references) makes features like snooze and filtering straightforward to add.

## Outcome

- A polished, filterable inbox and a full task-management workflow, plus a connection model ready for real channels.

## Next Steps

- Integrate a real external channel (WhatsApp) via the Meta Cloud API webhook.

---

# Week 8 — WhatsApp Integration, AI Orchestration & Agent Memory

## Objectives

- Integrate the real **WhatsApp Cloud API** webhook with security.
- Add a rule-based **AI orchestrator** to cut cost and latency.
- Implement lightweight **agent memory** (thread linking + bounded context).

## Work Completed

- Implemented the WhatsApp webhook endpoint (`backend/routes/webhooks.py`) with Meta verification handshake, **HMAC-SHA256 signature verification**, Pydantic payload validation, and **deduplication**.
- Built a unified ingestion pipeline (`services/webhook_ingest.py`) used by both REST and webhook paths, with background-task AI analysis for webhooks.
- Added the **AI orchestrator** (`services/ai/orchestrate.py` + `routing.py`): rule-based routing that skips the LLM for trivial/no-content messages (zero cost) and attaches an explainable `routing` record on every path.
- Added deterministic **thread linking** (`services/threads.py`) and **agent memory** (`services/ai/context.py`): up to 5 same-thread recent messages are injected into the existing single AI call, and any AI-suggested context update is validated against the thread before being applied.
- Added the WhatsApp setup guide and expansion of the test suite (136 backend tests).

## Technical Work

- Webhook security: constant-time HMAC comparison, signature over raw body, owner resolution server-side.
- Deduplication using a unique `external_message_id` index with idempotent handling.
- Routing decision table (trivial, deadline, action, full, non-Latin-script) to select the smallest AI agent subset.
- Deterministic link rule: same user + source + sender within a 60-minute window; `threadId` born from the anchor message id.
- Context validation: every revision must reference a real thread message and contain a verbatim value from its source — "zero tolerance for unlabelled influence."

## Challenges Faced

- "Webhook verification works but no messages arrive" — a real external-configuration problem (documented in `WEBHOOK_SETUP_GUIDE.md`).
- Keeping AI memory cheap and safe (no vector store / RAG).

## Research and Investigation

- Meta Cloud API webhook verification handshake and signature scheme.
- Whether to use deterministic linking vs embeddings/vector databases (chose deterministic — simpler, explainable, zero new dependencies).

## Solution

- Documented correct Meta configuration (subscribe to `messages`, stable ngrok URL, one-directional traffic) and added server-side signature verification and dedup for production safety.
- Implemented conservative rule-based linking with validated, reason-named context updates.

## Key Learning

- Real integrations involve external configuration and security carefulness; and "memory" does not require heavy AI machinery — a conservative rule plus validated context can be enough and is far more trustworthy.

## Outcome

- Real WhatsApp messages can flow in securely, AI analysis is cheaper and faster, and related messages are analyzed with bounded, explainable context.

## Next Steps / Current Status

- The project is at a strong working stage through Day 25.
- **Partially complete**: Gmail/LinkedIn connections are only "coming soon"; the OpenAI provider is a legacy artifact (Groq is live); the Dashboard greeting is still hardcoded.
- **Planned/out of scope** (from `SPEC.md`): real Gmail/LinkedIn integration, advanced analytics, real-time notifications, mobile app, data export/account-deletion UI.
