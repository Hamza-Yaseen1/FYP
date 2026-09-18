# Project Highlights

**Project**: Communication Overload Management ("Signal Desk")
**Student**: Hamza Yaseen
**Status**: Development complete through Day 25 (Agent Memory)
**Date of this report**: September 2026

---

## 1. Project Introduction

This is my Final Year Project: a web application that helps people manage
communication overload. People today receive messages from many channels —
WhatsApp, Gmail, social media — and important requests easily get lost. This
system pulls those messages into one clean dashboard, uses Artificial
Intelligence to triage them automatically (deciding what is urgent or
important), extracts the tasks and deadlines hidden inside them, and shows the
user a prioritized view of what actually needs their attention.

The system was built as a full-stack application with a modern frontend, a
Python backend API, a MongoDB database, and an integrated AI analysis pipeline
powered by the Groq LLM platform.

---

## 2. Problem Being Solved

**The real-world problem**: Professionals and students receive dozens of
messages every day across multiple apps. Manually opening every message to
decide "is this urgent?", "is there a task here?", and "when is it due?" is
slow and error-prone. Important messages get buried, tasks are forgotten, and
deadlines are missed.

**What this project does about it**:
1. **Centralizes** messages from multiple channels into one inbox.
2. **Automatically prioritizes** each message as Urgent, Important, Normal, or Low.
3. **Extracts action items** (tasks) and deadlines directly from message text.
4. **Flags** messages that "Need Your Attention" so nothing important is missed.
5. **Connects to real WhatsApp** so genuine incoming messages can be triaged automatically.

The core idea is simple: *spend less time reading and sorting messages, and more
time acting on what matters.*

---

## 3. My Main Contributions

These are the major pieces of work actually present in the repository:

- Designed the full system architecture (frontend, backend API, database, AI layer, external integration).
- Developed the modern Next.js frontend with a prioritized inbox, dashboard, task manager, and attention view.
- Built the complete FastAPI backend with RESTful endpoints, JWT authentication, and user data isolation.
- Integrated MongoDB as the data store with message, task, user, and connection collections and indexes.
- Implemented the AI analysis pipeline using the Groq LLM, with priority classification, task extraction, deadline detection, summarization, and recommended actions.
- Built a rule-based AI **routing orchestrator** that reduces cost and replies faster by skipping AI calls for trivial messages.
- Implemented automatic message-thread linking and lightweight "agent memory" (bounded context between related messages).
- Integrated the **WhatsApp Business / Meta Cloud API webhook** with signature verification for real inbound messages.
- Implemented secure authentication and strict **per-user data isolation**.
- Wrote and ran an automated test suite (136 backend tests) plus frontend component tests.
- Produced structured technical documentation (specs, plans, constitutions) for every feature.

---

## 4. Key Technical Achievements

### 4.1 AI Orchestrator with Zero-Cost Short-Circuiting
**What was built**: `backend/services/ai/orchestrate.py` is the single entry point for AI. Before calling the LLM, a rule-based router (`routing.py`) decides whether a message needs AI at all. Trivial messages ("ok", "thanks", "got it") and media/no-content messages are handled with deterministic defaults — **zero AI calls, zero cost, near-zero latency**. Only meaningful messages trigger the LLM.

**How it works**: `decide_routing()` uses keyword and script detection (including Arabic text handling) to select the smallest sufficient subset of the five "agents" (Priority, Summary, Task Extraction, Deadline Detection, Recommended Action). Every path attaches an explainable `routing` record so the behavior is transparent.

**Why it is important**: This is a cost-and-latency optimization that also makes the AI decisions explainable. It directly implements the project's "AI is Assistive, Not Magical" principle and keeps the dashboard fast.

### 4.2 Single-Call AI Analysis Pipeline
**What was built**: All intelligence — priority, tasks, deadlines, summary, and recommended action — is produced by **one** LLM call per message (`providers/groq.py`), using a structured JSON prompt instead of several separate calls.

**Why it is important**: It respects the constitution's "single LLM call" rule, minimizing latency and token cost while keeping outputs reliable enough to parse.

### 4.3 Deterministic Thread Linking & Agent Memory
**What was built**: `backend/services/threads.py` groups related messages into conversation threads using a **pure deterministic rule** (same user + source + sender, arriving within 60 minutes). Then `context.py` gives the AI up to 5 recent same-thread messages as context in the **same single AI call**, so a follow-up message ("Need it before our meeting.") can visibly add a deadline to an earlier message's task.

**How it works**: The link is resolved at ingest with one indexed query. Any AI-suggested revision is **validated against the actual thread** before being written — the value must literally appear in a source message. This gives "zero tolerance for unlabelled influence."

**Why it is important**: This is genuine lightweight memory without expensive vector databases or embeddings — a conservative, explainable, and secure design that fits an FYP scope.

### 4.4 WhatsApp Cloud API Webhook Integration
**What was built**: A real webhook endpoint (`routes/webhooks.py`) for the Meta/WhatsApp Cloud API, with:
- GET verification flow (`hub.challenge` handshake),
- **HMAC-SHA256 signature verification** of every delivery using the App Secret (constant-time comparison),
- Pydantic-validated payload parsing,
- UUID/eid-based **deduplication** so duplicate deliveries never re-analyze.

**Why it is important**: This moves the project from "simulated" to real-world integration and demonstrates webhook security, a genuinely challenging engineering problem.

### 4.5 Strict Per-User Data Isolation
**What was built**: Every database query is scoped by the authenticated `user_id` (see `dependencies.py` and every route). A user can only ever read/modify their own messages, tasks, and connections. Combined with JWT + httpOnly-cookie authentication, user A cannot see user B's data.

**Why it is important**: Privacy and security are core requirements for a communication tool; this was a deliberate, verified design decision (tested in `test_user_isolation.py`).

---

## 5. System Workflow

1. **A message enters the system** — via the web UI's "Simulate Message", the REST `POST /messages` endpoint, or a real WhatsApp webhook delivery.
2. **The backend validates the request** — authentication is checked; webhook deliveries are signature-verified and deduplicated.
3. **The message is stored in MongoDB** — with its channel, sender, content, and a server-generated identity (`messageId`, and `threadId`/`conversationId` when linked to a thread).
4. **The AI orchestrator routes the message** — a rule-based decision determines whether AI analysis is needed (trivial messages skip straight to defaults).
5. **AI processing analyzes the message** — if needed, a single LLM call returns priority, confidence, summary, extracted tasks, deadlines, and a recommended action. Context from earlier thread messages rides in the same call.
6. **Attention is computed and stored** — the `needs_attention` flag is derived and the full analysis (including an explainable routing record, and validated context updates) is saved back to the message.
7. **The result is shown to the user** — the dashboard, inbox, attention view, and task manager render AI insights with priority badges, confidence levels, summaries, and recommended actions.

---

## 6. Challenges I Faced

### 6.1 AI Analysis Failing Silently
**Problem**: The AI analysis returned a useless stub (`priority: "normal"`, `confidence: 0`, `status: "pending"`) instead of real results. This is documented in `AI-FIX-SUMMARY.md`.

**Investigation**: I reviewed the provider implementation and logs and found the errors were too vague to debug.

**Root Cause**: The analysis prompt only asked for priority, not all the fields the system expected (tasks, summary, actions, deadlines), and there was no validation of the API key or comprehensive logging.

**Solution**: Replaced the incomplete prompt with a comprehensive single-call analysis prompt, added API-key validation on initialization, added detailed step-by-step logging, and graceful field defaults when the model omits data.

**Lesson Learned**: Good diagnostics matter. A prompt that asks for all required fields up-front (with supplied defaults) is far more reliable than patching missing fields after the fact.

### 6.2 LLM Rate Limits / Daily Token Caps
**Problem**: During testing, Groq hit rate limits / daily token caps, returning HTTP 429, which blocked analysis.

**Investigation**: The exception handler logged the provider response, identifying "429" / "rate_limit" as the cause.

**Solution**: The analyzer now detects rate-limit errors, logs them clearly, and stores the message with safe fallback values (default Normal priority, `status: "pending"`) so the message is never lost and the dashboard keeps working. The AI can be re-run when the quota resets.

**Lesson Learned**: AI services can be unavailable or limited. A system that depends on AI must always degrade gracefully (Progressive Enhancement).

### 6.3 MongoDB Connection / Environment Configuration
**Problem**: Connecting the backend to MongoDB required correct configuration of the connection URI, database name, and environment secrets.

**Investigation**: `backend/database.py` loads settings from environment variables (with sensible defaults).

**Solution**: A documented `.env` / `.env.example` handles secrets (`MONGO_URI`, `JWT_SECRET`, `GROQ_API_KEY`, etc.), and the app validates required secrets at startup (e.g. `security.py` raises if `JWT_SECRET` is missing).

**Lesson Learned**: Keep secrets in environment variables and fail fast (with a clear message) when a required secret is missing.

### 6.4 WhatsApp Webhook "Verification Works But No Messages Arrive"
**Problem**: The webhook endpoint was verified successfully with Meta, but no messages were being received.

**Investigation**: The troubleshooting guide (`WEBHOOK_SETUP_GUIDE.md`) walks through checking the backend process, ngrok tunnel, subscription fields, and the direction of traffic.

**Root Cause**: Meta only sends webhooks for messages **sent to** your business number (one-directional by design), and webhook `messages` events must be explicitly subscribed in the Meta dashboard; the free ngrok URL also changes on restart.

**Solution**: Documented the correct configuration (subscribe to `messages`, use a stable ngrok URL, understand directionality) and added server-side signature verification and deduplication for production safety.

**Lesson Learned**: Real external integrations involve configuration outside the codebase. Methodical troubleshooting and good documentation are essential.

### 6.5 Async Database Access and Testing Pitfalls
**Problem**: Writing reliable async tests for the Motor/MongoDB driver was error-prone.

**Investigation**: Over the test suite I found that awaiting motor operations inside `asyncio.run(...)` leads to problems.

**Solution**: Tests use the FastAPI `TestClient` loop or a fake collection, and never `await` motor under a separate `asyncio.run`. This is documented as a project convention in `AGENTS.md`.

**Lesson Learned**: Async test patterns require care; using the framework's own event loop is the reliable approach.

---

## 7. Research and Learning

Throughout development I researched and learned:

- **Next.js 16** App Router, server components, client components, and route-level middleware for route protection.
- **FastAPI + Python** async routing, Pydantic validation, and dependency injection (`Depends`).
- **MongoDB + Motor** — collections, indexes, aggregation pipelines, atomic updates, and unique/partial indexes.
- **LLM integrations** — the Groq API, structured JSON prompting, prompt engineering, and robust JSON response cleaning/parsing.
- **Provider abstraction** — designing a `BaseLLMProvider` interface so OpenAI/Groq/Gemini can be swapped (Groq is active; OpenAI remains as a legacy provider).
- **Authentication & security** — JWT tokens, bcrypt password hashing, httpOnly cookies, HMAC webhook signature verification.
- **Webhook patterns** — Meta Cloud API verification handshake, signature verification, and idempotent/deduplicated delivery handling.
- **Design-driven development** — I followed a documentation-first workflow (spec → plan → tasks → implementation, plus a project "Constitution" of principles), which kept the project consistent and reviewable.

**Approaches considered and final choices**:
- *AI provider*: chose Groq for its free tier and speed; kept a provider abstraction for flexibility.
- *Analysis granularity*: chose a single combined LLM call over many small calls (lower latency/cost).
- *Memory/threads*: chose deterministic rule-based linking over a vector store / RAG (simpler, explainable, zero new runtime dependencies).
- *Authentication*: chose JWT stored in an httpOnly cookie over localStorage (more secure against XSS).

---

## 8. Current Status

### Working
- Secure registration, login, logout, and route protection.
- Per-user data isolation for messages, tasks, and connections.
- Message simulation and real WhatsApp webhook ingestion (signature-verified, deduplicated).
- Full AI pipeline: routing orchestrator, priority, tasks, deadlines, summary, recommended actions, attention flagging.
- Thread linking and lightweight agent memory (bounded context + validated context updates).
- Rich UI: Inbox (with priority tabs, filters, search), Dashboard, Attention view, Tasks manager (with snooze and status), Connections, and Settings (appearance/theme).
- Automated test suite (136 backend tests + frontend component tests).

### Partially Completed / Under Development
- Connection management is structural: WhatsApp can be linked, but Gmail/LinkedIn are marked "coming soon" (not fully integrated).
- The OpenAI provider exists but is a legacy artifact; the live provider is Groq.
- The Dashboard header currently shows a hardcoded user name greeting ("Good morning, Hamza"); it is not yet fully dynamic per authenticated user.

### Planned / Not Yet Implemented (documented in SPEC.md as out of scope)
- Real Gmail / LinkedIn integrations.
- Advanced analytics and reporting.
- Real-time notifications (currently auto-polling).
- Mobile application.
- Team / multi-user collaboration features.
- Natural-language query interface and offline mode.
- User data export and account deletion flows (mentioned as requirements, not yet built as UI).

> Note: The timeline for the weekly reports is largely reconstructed from the
> repository's git history, specs, and documentation rather than from running
> logs, and is marked as such where relevant.

---

# Supervisor Talking Points

Here are short, confident points you can speak naturally in a supervisor meeting,
based only on what is actually in the project:

1. "I started by designing the overall architecture — separating the frontend, backend, and database responsibilities into a clean full-stack structure."

2. "The project's core value is AI-powered triage: every incoming message is automatically prioritized and checked for tasks, so users stop losing important messages."

3. "I built a real backend in Python with FastAPI, using MongoDB for storage and JWT-based authentication with secure httpOnly cookies for login."

4. "I implemented strict per-user data isolation, so every single database query is scoped to the logged-in user — no one can see anyone else's data."

5. "The AI is powered by the Groq LLM, and I designed it as a single analysis call per message to keep it fast and cheap."

6. "One of my best contributions is a rule-based AI router that skips the LLM entirely for trivial messages like 'ok' or 'thanks' — that cuts cost and response time to almost zero for a large share of real traffic."

7. "I integrated the real WhatsApp Cloud API through a webhook, including signature verification and deduplication, so genuine messages can flow in securely."

8. "I added lightweight 'agent memory' — related messages get linked into threads deterministically, and the AI can use earlier messages as context to improve later analyses."

9. "I followed a documentation-driven workflow: every feature has a spec, a plan, task checklists, and even a project 'Constitution' of principles that kept development consistent."

10. "I wrote an automated test suite with over 130 backend tests covering authentication, isolation, webhooks, AI routing, and thread linking."

11. "A key lesson I learned was handling AI failures gracefully — when the LLM is rate-limited or down, messages still get stored and the dashboard keeps working."

12. "I researched prompt engineering and structured JSON outputs so that the AI reliably returns priority, tasks, deadlines, summaries, and actions."

13. "The hardest engineering challenge was external webhook integration, and I solved it by researching Meta's verification handshake, HMAC signatures, and idempotent message handling."

14. "The system is at a strong working stage through Day 25, with clear next steps like real Gmail integration and dynamic user profiles."
