# 05 — Backend & APIs

> The FastAPI backend explained: how it is structured, what every endpoint does, and the full API reference. Beginner-friendly first, then technical detail.

---

## 1. What the backend is

The backend is a **Python 3.13 FastAPI** application. It is the only part of the system that talks to the database, to the AI, and to external services. The frontend is a thin client.

Its responsibilities:

1. **Authentication** — register, login, sessions, password reset.
2. **Message management** — receive, list, filter, delete, re-analyse.
3. **AI analysis** — one entry point (`process_message`) that classifies and enriches messages.
4. **Integrations** — Gmail OAuth + polling, WhatsApp webhook, email.
5. **Assistant** — one entry point (`process_command`) for Kestrel/JARVIS.
6. **Realtime** — WebSocket fan-out per user.
7. **Analytics** — read-only aggregation.
8. **Background work** — Gmail poller and pending-analysis retry sweep.

```
backend/
├── main.py                 app, lifespan, routers, CORS
├── database.py             Mongo client + collections + indexes
├── dependencies.py         get_current_user
├── models/                 Pydantic schemas (user, message, task, connection, meta_webhook)
├── routes/                 all HTTP + WS endpoints
├── services/               business logic (see below)
│   └── ai/                 the AI pipeline + the assistant
├── utils/encryption.py     AES token encryption
├── scripts/                dev/ops helpers
└── tests/                  pytest suite
```

---

## 2. How a request is handled

1. **CORS + GZip** are applied globally in `main.py`.
2. The route's **dependency** `get_current_user` reads the `cai_token` cookie, decodes the JWT, validates the `ObjectId`, and loads the user (else 401).
3. The route delegates to a **service** function.
4. The service does a **user-scoped** Mongo query (or calls the AI / an external API).
5. The route returns a **Pydantic model** (FastAPI serialises it to JSON).

Two rules the code enforces everywhere:
- **The owner id always comes from the session**, never from the request body.
- **Routes never call `analyze_message` directly** — they call `process_message`.

---

## 3. Full API reference

Base URL: the backend origin (in the app, reached via the `/api` rewrite). All endpoints require the session cookie unless marked **public**.

### 3.1 Auth — `routes/auth.py`

| Method | Path | Auth | Purpose | Notes |
|--------|------|------|---------|-------|
| POST | `/auth/register` | public | Create account | 409 if email exists; hashes password; sets session cookie |
| POST | `/auth/login` | public | Log in | 401 on bad credentials; sets session cookie |
| POST | `/auth/logout` | required | Log out | Clears cookie |
| GET | `/auth/me` | required | Current user | Used by Navbar/Settings |
| POST | `/auth/forgot-password` | public | Request reset email | Always generic response; 60 s cooldown |
| POST | `/auth/reset-password` | public | Reset with token | 30-min, single-use, hashed token |

### 3.2 Messages — `routes/messages.py`

| Method | Path | Purpose | Notes |
|--------|------|---------|-------|
| GET | `/messages` | List messages | Filters: tab, priority, source, sender, search `q`, date range; user-scoped |
| GET | `/messages/counts` | Counts per tab | Drives tab pills + SignalLine |
| GET | `/messages/senders` | Distinct senders | Drives the sender filter |
| POST | `/messages` | Create a message | Runs `process_message` **synchronously** |
| DELETE | `/messages` | Clear inbox | Deletes all of the user's messages |
| DELETE | `/messages/{id}` | Delete one | User-scoped (404 if not owner) |
| PUT | `/messages/{id}/priority` | Override priority | Stores override + reviewed/verified flags |
| POST | `/messages/{id}/reanalyze` | Re-run AI | Re-enters `process_message` |

### 3.3 Webhooks — `routes/webhooks.py`

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/webhooks/whatsapp` | public | Meta verification challenge (`hub.verify_token`) |
| POST | `/webhooks/whatsapp` | signature | Receive WhatsApp messages; verifies `X-Hub-Signature-256` HMAC (constant-time) |
| POST | `/webhooks/simulate` | required | Inject a demo message; analysis runs in the background |

### 3.4 Gmail — `routes/gmail.py`

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/connections/gmail/auth-url` | required | Returns the Google consent URL |
| GET | `/connections/gmail/callback` | **public** | OAuth redirect target; identity proven by signed `state` |
| GET | `/auth/google/callback` | **public** | Alias of the above |
| POST | `/connections/gmail/refresh` | required | Force a full INBOX resync |

### 3.5 Connections — `routes/connections.py`

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/connections` | List the user's connections |
| POST | `/connections` | Create a connection (Gmail via this route is rejected) |
| DELETE | `/connections/{id}` | Disconnect (revokes Google token best-effort, then deletes) |

### 3.6 Tasks — `routes/tasks.py`

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/tasks` | List active tasks (excludes completed + currently snoozed; priority-sorted; limit 100) |
| PUT | `/tasks/{id}/status` | Complete a task |
| PUT | `/tasks/{id}/snooze` | Snooze (1 hour / tomorrow / next week) |
| GET | `/tasks/{id}/message` | Fetch the source message of a task |

### 3.7 Analytics — `routes/analytics.py`

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/analytics?period=day\|week\|month` | Aggregated stats; invalid period → 400 |

### 3.8 Assistant — `routes/jarvis.py`

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/jarvis/chat` | required | The assistant. Empty/missing message → 400. Returns `{reply, action, used_ai}` |

Request body (`JarvisChatRequest`): `{ message: str, confirmation_token?: str, confirmed?: bool }`.

Response (`JarvisChatResponse`): `{ reply: str, action: JarvisAction | null, used_ai: bool }`. `JarvisAction` uses a custom serialiser that omits unset fields.

### 3.9 WebSocket — `routes/ws.py`

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| WS | `/ws` | cookie | Realtime channel; inbound text ignored (keep-alive) |
| GET | `/ws-token` | required | Mint a short-lived WS token (120 s) for the dev `?token=` path |

### 3.10 Health

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Backend health (used by `HealthBadge`) |

---

## 4. The service layer

| Service | Responsibility |
|---------|----------------|
| `services/security.py` | bcrypt hashing, JWT create/decode, WS tokens; rejects `purpose` tokens |
| `services/connection.py` | Connection CRUD + token encryption |
| `services/gmail.py` | Google OAuth, token refresh/revoke, email normalisation, inbox poller |
| `services/password_reset.py` | Reset tokens + Brevo email |
| `services/analytics.py` | `build_analytics_response` (read-only aggregation) |
| `services/realtime.py` | `ConnectionManager` (per-user WebSocket fan-out) |
| `services/retry_pending.py` | Retry sweep for `pending` analyses |
| `services/threads.py` | Deterministic thread linking |
| `services/webhook_ingest.py` | The shared ingest path for all sources |
| `services/ai/orchestrate.py` | `process_message` — the ONE AI entry point |
| `services/ai/routing.py` | Rule-based agent routing |
| `services/ai/analyzer.py` | Prompt build + provider call + parse |
| `services/ai/attention.py` | Deterministic "needs attention" rules |
| `services/ai/token_budget.py` | Token estimation + truncation |
| `services/ai/context.py` | Thread context build/validate/apply |
| `services/ai/providers/*` | `GroqProvider` (active), `OpenAIProvider` (unused) |
| `services/ai/jarvis_agent.py` | `process_command` — the ONE assistant entry point |
| `services/ai/jarvis_intents.py` | Assistant NLU (navigation + info intents) |
| `services/ai/jarvis_actions.py` | Assistant actions + confirmation tokens |
| `services/ai/jarvis_messages.py` | Assistant message-content intelligence |

---

## 5. Key backend flows

### 5.1 Creating a message (`POST /messages`)
```
route → validate body → ingest_message(...)
      → dedupe check (user_id + external_message_id)
      → threads.resolve_and_stamp
      → insert with ai_analysis.status="pending"
      → process_message (synchronously)
      → update with ai_analysis + routing
      → realtime.emit("message.created")
```

### 5.2 WhatsApp webhook (`POST /webhooks/whatsapp`)
```
verify HMAC signature (constant-time) → parse Meta payload
→ for each text message: ingest_message(..., background_tasks=...)
→ analysis runs in the background (response returns fast)
```

### 5.3 Gmail poll
```
poller loop (every 30s, if GOOGLE_CLIENT_ID set)
→ for each connected user: fetch inbox after watermark
→ normalize_email (MIME parse, HTML fallback, skip attachments)
→ ingest_message(..., subject=...)
→ update last_fetched_at watermark
```

### 5.4 Assistant (`POST /jarvis/chat`)
```
empty guard → Phase 4 messages → Phase 2 actions → Phase 3 intents
→ Phase 1 routing → Phase 5 conversation
→ record turn in per-user context → return {reply, action, used_ai}
```

---

## 6. Configuration (environment variables)

See `backend/.env.example` for the full list. The important ones:

| Group | Variables |
|-------|-----------|
| Database | `MONGO_URI`, `DB_NAME` |
| Auth | `JWT_SECRET`, `TOKEN_EXPIRY_DAYS`, `COOKIE_SECURE`, `COOKIE_SAMESITE` |
| Encryption | `ENCRYPTION_KEY` (AES for OAuth tokens) |
| AI (Groq) | `GROQ_API_KEY`, `GROQ_MODEL`, `GROQ_FALLBACK_MODEL`, `GROQ_MAX_OUTPUT_TOKENS`, budget + resilience knobs |
| Gmail | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`, `GMAIL_POLL_INTERVAL_SECONDS`, `GMAIL_INBOX_QUERY`, `GMAIL_MAX_RESULTS`, `GMAIL_MAX_PAGES` |
| WhatsApp | `WHATSAPP_APP_SECRET`, `WHATSAPP_VERIFY_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID` |
| Email | `BREVO_API_KEY`, `EMAIL_FROM`, `FRONTEND_URL`, `RESET_TOKEN_TTL_MINUTES`, `RESET_REQUEST_COOLDOWN_SECONDS` |
| Realtime | `WS_ALLOW_QUERY_TOKEN` (dev only) |
| Retry | `RETRY_INTERVAL_SECONDS`, `RETRY_SLEEP_SECONDS`, `RETRY_MAX_CONSECUTIVE_FAILURES` |

---

## 7. Error handling conventions

- **401** — missing/invalid session (from `get_current_user`).
- **400** — bad input (e.g. invalid analytics period, empty assistant message).
- **403** — failed webhook signature.
- **404** — not found *or* not owned (used deliberately so users can't probe others' ids).
- **409** — duplicate email on register.
- AI failures never surface as HTTP errors on ingest; they are stored as `ai_analysis.status="pending"` and retried.

---

## 8. Things to know before editing the backend

1. **Never call `analyze_message` from a route or service** — use `process_message`.
2. **Never trust a client-supplied `user_id`** — take it from `get_current_user`.
3. **Always put `user_id` first in Mongo `$match`** in aggregations.
4. **Never await motor under `asyncio.run` in tests** — use the `TestClient` loop or a fake collection.
5. **Date handling is UTC everywhere** (analytics, "today", threads).
6. **Dedupe** relies on the composite index `{user_id, external_message_id}`.
7. **Background loops** only start on the real DB (they're skipped on the test DB).

See `07_DATABASE.md`, `09_SECURITY_AND_PRIVACY.md`, and `11_TESTING_AND_DEPLOYMENT.md` for the details behind these rules.
