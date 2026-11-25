# 10 — External Services

> Every third-party service Sift depends on: what it does, why it is used, how it is configured, and what happens if it fails.

---

## 1. Summary table

| Service | Role | Required? | If it fails |
|---------|------|-----------|-------------|
| **MongoDB Atlas** | Primary database | ✅ Yes | App cannot function |
| **Groq** | LLM inference (analysis + assistant chat) | 🟡 Effectively yes for AI features | Analyses stay `pending` and retry; assistant falls back to deterministic replies |
| **Google (Gmail API + OAuth)** | Read-only email ingestion | 🔵 Optional per user | Gmail feature disabled; other features unaffected |
| **Meta (WhatsApp Business Platform)** | Inbound WhatsApp messages | 🔵 Optional | WhatsApp ingestion stops; other features unaffected |
| **Brevo** | Transactional email (password reset) | 🟡 Needed for password reset | Reset emails fail; login still works |
| **Vercel** | Hosting (frontend + backend) | ✅ Yes | App offline |

---

## 2. MongoDB Atlas

- **What:** Managed MongoDB. Sift uses the async driver Motor.
- **Config:** `MONGO_URI` (a `mongodb+srv://` connection string), `DB_NAME`.
- **Used for:** all persistence — `users`, `messages`, `tasks`, `connections`.
- **Connection hardening:** DNS resolvers pinned to 8.8.8.8 / 1.1.1.1 / 8.8.4.4, `tz_aware=True`, 5 s timeouts.
- **Tests** use a separate DB (`communication_ai_test`) and wipe collections around every test.
- **If it fails:** the whole app fails. There is no caching layer in front of the DB.
- **Unresolved:** backup retention and geographic region are not documented in code.

---

## 3. Groq (LLM)

- **What:** Fast LLM inference API. Sift's active AI provider.
- **Config:** `GROQ_API_KEY`, `GROQ_MODEL` (default `qwen/qwen3.8-27b`), `GROQ_FALLBACK_MODEL` (`openai/gpt-oss-20b`), `GROQ_MAX_OUTPUT_TOKENS`, plus budget/resilience knobs.
- **Used for:**
  - **Message analysis** (one structured JSON call per message) — priority, summary, action, tasks, deadlines.
  - **Assistant** — optional intent labelling, message summarisation, and general chat (only when a key is set).
- **Costs/limits:** free-tier rate limits are the reason for `reasoning_effort="none"`, a JSON response format, a low token cap, retries, and a **circuit breaker** for daily-quota 429s.
- **If it fails:**
  - Message analyses become `status="pending"` and are retried every 60 s.
  - The assistant replies with deterministic fallbacks (or `CONVERSATION_UNAVAILABLE_REPLY` for general chat).
  - The rest of the app keeps working.
- **Privacy:** message content and metadata **are sent** to Groq. This is disclosed in the Privacy Policy.
- **Note:** the `openai` Python package and `providers/openai.py` exist but are **unused** — the factory always returns Groq.

---

## 4. Google (Gmail API + OAuth 2.0)

- **What:** Official OAuth 2.0 + Gmail read API.
- **Scope:** `https://www.googleapis.com/auth/gmail.readonly` only (restricted scope).
- **Config:** `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`, poller settings.
- **Used for:** letting a user connect their inbox and pull new mail into Sift.
- **No SDK:** all calls are direct REST via httpx.
- **If it fails:** Gmail ingestion stops; the connection may flip to `error` with a Reconnect CTA; other features are unaffected.
- **Production requirement:** Google app verification (+ likely CASA for the restricted scope) — **not completed**.
- See `08_GMAIL_OAUTH.md` for the full flow.

---

## 5. Meta / WhatsApp Business Platform

- **What:** WhatsApp Cloud API webhook.
- **Config:** `WHATSAPP_APP_SECRET` (HMAC verification), `WHATSAPP_VERIFY_TOKEN` (challenge), `WHATSAPP_PHONE_NUMBER_ID`.
- **Used for:** receiving inbound WhatsApp text messages.
- **Security:** every request is verified via `X-Hub-Signature-256` (constant-time); a verification challenge completes the initial handshake.
- **If it fails:** WhatsApp messages are not received; other sources keep working.
- **Limitations:** only text is ingested; media is skipped.

---

## 6. Brevo (transactional email)

- **What:** Email delivery REST API.
- **Config:** `BREVO_API_KEY`, `EMAIL_FROM`, `FRONTEND_URL`, `RESET_TOKEN_TTL_MINUTES`, `RESET_REQUEST_COOLDOWN_SECONDS`.
- **Used for:** the **only** outbound email — password reset links. No marketing, no notifications.
- **Endpoint:** `https://api.brevo.com/v3/smtp/email`, 10-second timeout.
- **If it fails:** password reset silently doesn't send (the API still returns a generic success). Login is unaffected.
- **Unverified:** live delivery was not confirmed in this repo — the API key type and sender verification are open items (`15_FINDINGS_AND_GAPS.md`).

---

## 7. Vercel (hosting)

- **What:** Hosts both the Next.js frontend and the FastAPI backend.
- **Used for:** deployment, HTTPS, environment variables.
- **Config:** frontend `BACKEND_URL` must point to the backend; backend env vars set in the Vercel dashboard.
- **Caveat:** the backend's in-process background loops (Gmail poller, retry sweep) assume a **long-lived** process. On serverless/edge-style runtimes that can scale down, these loops may not run continuously.

---

## 8. What is NOT used (despite the README implying otherwise)

| Not used | Note |
|----------|------|
| OpenAI API (live) | `providers/openai.py` exists but is dead code. |
| Google Sign-In | Not implemented; Google OAuth is only for Gmail. |
| Any analytics/ad tracker | None. |
| Any push-notification service | Notifications are not implemented. |
| Any message queue/worker | Background work is in-process asyncio. |
| Any payment provider | No monetisation in the code. |

---

## 9. Adding a new external service (pattern to follow)

1. Put the credentials in `backend/.env` and `.env.example` (never in the frontend).
2. Isolate all calls in a `services/*.py` module (like `gmail.py`, `password_reset.py`).
3. Make calls with **httpx** and set an explicit timeout.
4. Fail **softly**: a failing integration should not break ingestion or login.
5. Mock the service in tests (never hit it live).
6. Document it here and in `15_FINDINGS_AND_GAPS.md` if it adds a privacy/legal obligation.
