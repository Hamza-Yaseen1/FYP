# 12 — Learn My Project

> A guided walkthrough for **you** (the author) to truly understand your own project, in the order you should learn it. Read this top-to-bottom once; you will be able to explain every part in a viva.

---

## How to use this document

Work through the sections in order. Each section has three parts:
- **Idea** — the concept in plain words.
- **Where** — the files to open.
- **Say it** — a one-sentence answer you can give in a viva.

---

## Part 1 — The 60-second pitch

**Idea:** Sift collects messages from Gmail and WhatsApp, uses AI to sort them by importance and pull out tasks and deadlines, and shows everything in one dashboard with an assistant you can talk to.

**Say it:** *"Sift is a communication triage app. It ingests messages from multiple sources, runs each one through a single AI analysis call that is chosen by rule-based routing, surfaces the ones that need attention, turns them into tasks, and lets users ask an assistant about their inbox."*

---

## Part 2 — The moving parts

**Idea:** There are three tiers — a Next.js frontend, a FastAPI backend, and MongoDB — plus external services (Groq, Google, Meta, Brevo).

**Where:** `app/`, `components/`, `lib/` (frontend); `backend/main.py`, `backend/routes/`, `backend/services/` (backend); `backend/database.py` (data).

**Say it:** *"The browser never calls the backend directly; Next.js rewrites `/api/*` to FastAPI so the httpOnly session cookie stays on one origin. FastAPI owns all logic and is the only thing that talks to the database and the AI."*

---

## Part 3 — Authentication (learn this first)

**Idea:** Users log in with email/password. The backend issues a JWT in an httpOnly cookie. Every protected endpoint decodes that cookie to find the user.

**Where:** `backend/services/security.py`, `backend/routes/auth.py`, `backend/dependencies.py`, `proxy.ts`.

**Key details to know:**
- Passwords: bcrypt.
- Session: HS256 JWT, 7 days, `cai_token` cookie.
- Reset tokens and WS tokens carry a `purpose` claim, so `decode_token` **rejects** them as sessions.
- `proxy.ts` only checks the cookie's *presence*; the backend does real validation.

**Say it:** *"Auth is a bcrypt password check that issues a short JWT session cookie; the same JWT machinery issues purpose-scoped tokens for password reset and WebSockets, and the decoder refuses any token that has a purpose claim."*

---

## Part 4 — How a message gets in

**Idea:** Three sources (Gmail, WhatsApp, manual/simulate) all converge on **one** ingest function.

**Where:** `backend/services/webhook_ingest.py`, `backend/services/threads.py`, `backend/services/gmail.py`, `backend/routes/webhooks.py`.

**Key details:**
- `ingest_message` dedupes on `(user_id, external_message_id)`, links threads deterministically, inserts with `status="pending"`, then analyses.
- Threads: same user + source + sender within 60 minutes.
- Gmail: OAuth read-only + a 30-second poller using an `after:` watermark.

**Say it:** *"Every source goes through one ingest function so dedupe, thread-linking, and analysis are identical; threads are linked deterministically by sender and a 60-minute window, not by AI."*

---

## Part 5 — The AI pipeline (the heart of the project)

**Idea:** A rule engine decides which outputs are needed; **one** LLM call produces them; a routing record explains the decision; failures are marked pending and retried.

**Where:** `backend/services/ai/orchestrate.py` (entry), `routing.py` (rules), `analyzer.py` (call), `attention.py` (deterministic attention), `providers/groq.py` (provider), `prompts/*.txt`.

**Key details:**
- Trivial/no-content messages → **zero** LLM calls.
- Five "agents" (priority, summary, task_extraction, deadline_detection, recommended_action) are **outputs of one call**, not separate agents.
- `routing.llm_call_used` is attached on every path.
- "Needs attention" is **deterministic** (R1: task + near-term deadline; R2: urgent + task).

**Say it:** *"It is not multi-agent: a pure rule engine routes each message to a single structured LLM call, attaches an explainable routing record, and degrades to a retryable pending state if the AI is unavailable."*

---

## Part 6 — The assistant (Kestrel / JARVIS)

**Idea:** A layered, deterministic-first command router with five phases; the LLM is used only where language understanding is needed.

**Where:** `backend/services/ai/jarvis_agent.py`, `jarvis_messages.py`, `jarvis_actions.py`, `jarvis_intents.py`; frontend `components/jarvis/*`.

**Key details:**
- Order: Phase 4 messages → Phase 2 actions → Phase 3 intents → Phase 1 routing → Phase 5 conversation.
- Ownership rules keep earlier phases byte-identical.
- Destructive actions need a signed 2-minute confirmation token.
- Voice is browser-only (Web Speech API); TTS is chunked to avoid Chrome truncation; barge-in is supported.

**Say it:** *"The assistant is deterministic first: navigation, info, message intelligence, and actions are all rule-based; the LLM only handles general conversation and optional intent labelling, and destructive actions require a signed confirmation."*

---

## Part 7 — Security and multi-user isolation

**Idea:** The owner id always comes from the session, and every query is scoped by it.

**Where:** `backend/dependencies.py`, every route, `backend/services/security.py`, `backend/services/gmail.py`, `backend/utils/encryption.py`.

**Key details:**
- Cross-user access → **404** (no id probing).
- OAuth tokens AES-encrypted; reset tokens SHA-256 hashed.
- WhatsApp webhook HMAC-verified (constant-time).
- No secrets in the frontend.

**Say it:** *"User isolation is enforced by taking the owner id from the session and scoping every query by it; cross-user requests return 404, and all sensitive tokens are encrypted or hashed."*

---

## Part 8 — Realtime

**Idea:** New/updated messages push to the right user's browser.

**Where:** `backend/services/realtime.py`, `backend/routes/ws.py`, `lib/realtime.ts`, `components/RealtimeProvider.tsx`.

**Key details:** per-user fan-out only; backoff reconnect; 15 s polling fallback; `MessageList` polls 2.5 s only while a message is un-analysed.

**Say it:** *"Realtime is a per-user WebSocket fan-out with a polling fallback, so a user only ever receives their own events."*

---

## Part 9 — The database

**Idea:** Four collections (`users`, `messages`, `tasks`, `connections`), with analysis stored inside each message.

**Where:** `backend/database.py`, `backend/models/*`, `07_DATABASE.md`.

**Key details to memorise:**
- Dedupe index `{user_id, external_message_id}`.
- Messages indexed on `{user_id, created_at}` + a text index.
- Tasks sorted by priority then recency; excludes completed and currently-snoozed.
- Analytics `$match` on `user_id` first, always.

**Say it:** *"Messages carry their analysis inline, dedupe uses a composite user-scoped index, and every analytics pipeline starts by matching the user."*

---

## Part 10 — Frontend structure

**Idea:** Next.js App Router with public, auth, and dashboard route groups, all talking through one cached fetch wrapper.

**Where:** `app/`, `components/`, `lib/api.ts`, `lib/api/*`.

**Key details:** GET cache 10 s + in-flight dedup; 401 → `/login`; assistant mounted once in `DashboardLayout`; theme applied pre-paint.

**Say it:** *"The frontend is a thin client: one fetch wrapper with a 10-second GET cache and de-duplication, and the assistant lives in the dashboard layout so it persists across screens."*

---

## Part 11 — Testing

**Idea:** pytest for the backend (real DB, fakes for AI/external), vitest for the frontend.

**Where:** `backend/tests/`, `app/**/__tests__/`, `components/**/__tests__/`.

**Key rules:** never await motor under `asyncio.run`; mock httpx; fresh email per test; `afterEach(cleanup)` on frontend.

**Say it:** *"Backend tests run against a wiped test database with AI and external calls faked; frontend tests run in jsdom with explicit cleanup because vitest globals are off."*

---

## Part 12 — Self-test (answer these without notes)

1. What are the three tiers and how does the browser reach the backend?
2. Why can't a password-reset token be used as a session?
3. What are the five "agents", and why is it *not* multi-agent?
4. What two rules define "needs attention"?
5. How is a thread formed?
6. What happens when the AI fails?
7. Why does the assistant need a confirmation token?
8. How is multi-user isolation enforced?
9. What is the dedupe index?
10. Why is TTS chunked?

If you can answer all ten clearly, you understand your project.

---

## Part 13 — The one-paragraph summary to memorise

*"Sift is a Next.js + FastAPI + MongoDB communication triage app. It ingests Gmail and WhatsApp messages through one shared pipeline, links threads deterministically, and analyses each message with a single rule-routed LLM call that produces priority, summary, action, tasks, and deadlines — with an explainable routing record and graceful pending-and-retry failure handling. A deterministic assistant (Kestrel/JARVIS) answers questions, navigates, and performs confirmed actions by voice or text. Everything is strictly user-scoped, tokens are encrypted or hashed, and the system keeps working when the AI is down."*
