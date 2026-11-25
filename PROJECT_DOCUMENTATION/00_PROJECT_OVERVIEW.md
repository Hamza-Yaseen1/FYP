# 00 — Project Overview

> A plain-English explanation of what this project is, who it is for, and what it actually does — followed by the technical details. Everything in this document is based on the **actual source code** in the repository, not on the marketing README. Where the code and the README disagree, the code wins and the difference is called out in `15_FINDINGS_AND_GAPS.md`.

---

## 1. In one paragraph (for anyone)

This is a **web application that collects messages from different places (Gmail and WhatsApp), uses AI to sort them by importance, summarises them, and pulls out the tasks and deadlines hidden inside them.** It then shows everything in one dashboard, a filtered inbox, a "needs attention" view, a task list, and simple charts. It also has a built-in assistant called **Kestrel** (the code still calls it "JARVIS" internally) that you can talk to or type to, and which can answer questions about your messages or move you between screens.

It was built as a **Final Year Project (FYP)** by **Hamza Yaseen** at **BBSUL**.

---

## 2. The problem it is trying to solve

People get too many messages across too many apps. Important requests get buried under newsletters and chatter. Deadlines hide inside long emails. Nobody has time to read everything.

The project's answer:

1. **Put everything in one place** — Gmail (read-only, via Google OAuth) and WhatsApp (via webhook) both flow into one database.
2. **Let AI do the first read** — every message gets a priority, a short summary, a recommended action, and any tasks/deadlines it contains.
3. **Surface only what matters** — a dedicated "Attention" view shows only messages the AI flagged as needing a human.
4. **Turn words into work** — extracted tasks become a real task list you can complete or snooze.
5. **Let you ask instead of scroll** — the assistant answers "what came in today?" or "what needs my attention?" by voice or text.

---

## 3. The name: "Sift" vs "JARVIS" vs "Kestrel"

The codebase is mid-rename and this confuses almost everyone on first look:

| Name | Where it lives | Meaning |
|------|----------------|---------|
| **Sift** | `lib/brand.ts` → `BRAND_NAME = "Sift"` | The **product/brand** name. This is what users see in the UI. |
| **Kestrel** | `lib/brand.ts` → `ASSISTANT_NAME = "Kestrel"` | The **assistant** name shown to users. |
| **JARVIS** | Backend files `services/ai/jarvis_*.py`, `routes/jarvis.py`, frontend `components/jarvis/*` | The **internal/original code name** for the assistant. It never reaches the screen because `lib/brand.ts::localizeAssistantReply()` rewrites `JARVIS → Kestrel` and `Signal Desk → Sift` before a reply is shown. |
| **Signal Desk** | Old references in prompts/comments | An even older brand name, also rewritten to `Sift`. |

**Takeaway:** when you see "JARVIS" in the code, read it as "the assistant (Kestrel)". When you see "Signal Desk", read it as "Sift".

---

## 4. Who it is for

- **Primary audience:** the FYP examiner/supervisor and the student author.
- **Intended real-world user:** a busy professional who lives in email and chat and wants a single triage surface.
- **Not for:** teams/enterprises (there is no organisation/tenant concept — every account is independent), or anyone who needs a guaranteed, supported commercial service (there is no SLA).

---

## 5. What is actually implemented (high-level)

The following are **implemented and wired end-to-end** in code:

| Capability | Status |
|-----------|--------|
| Email/password sign-up, login, logout (bcrypt + JWT session cookie) | ✅ Implemented |
| Password reset by email (Brevo) with hashed, single-use, 30-min tokens | ✅ Implemented |
| Manual/simulated message ingestion | ✅ Implemented |
| WhatsApp webhook ingestion (HMAC-signature verified) | ✅ Implemented |
| Gmail ingestion via Google OAuth 2.0 (read-only) + background poller | ✅ Implemented |
| Rule-based AI routing + single-call Groq analysis | ✅ Implemented |
| Priority, summary, recommended action, task & deadline extraction | ✅ Implemented |
| Deterministic thread linking + AI "context memory" across a thread | ✅ Implemented |
| Inbox with tabs/filters/search/date range | ✅ Implemented |
| Attention view | ✅ Implemented |
| Task list with complete/snooze | ✅ Implemented |
| Analytics (day/week/month charts) | ✅ Implemented |
| Realtime WebSocket updates (+ polling fallback) | ✅ Implemented |
| Assistant (Kestrel/JARVIS): navigation, real-data answers, message intelligence, actions, conversation, voice + barge-in + chunked TTS | ✅ Implemented |
| Dark/light/system theme | ✅ Implemented |
| Privacy Policy & Terms pages | ✅ Implemented |
| Multi-tenant isolation (every query scoped by `user_id`) | ✅ Implemented |
| AI failure handling: `pending` state + retry sweep + circuit breaker | ✅ Implemented |

## 6. What is **not** implemented (do not claim these)

These appear in the README or in comments but are **not** in the code:

- ❌ No "Sign in with Google" (Google OAuth is only for the optional Gmail connection).
- ❌ No AI-drafted *replies sent to anyone* — the assistant can produce a *draft* shown in the panel, but there is no send path.
- ❌ No "Sentiment & Intent" analysis as a separate feature.
- ❌ No organisation/team/multi-user accounts.
- ❌ No self-service "delete my account" button (deletion is manual by email).
- ❌ No LinkedIn integration (shown as "coming soon" only).
- ❌ No true multi-agent system — it is a **single LLM call with deterministic routing**, described honestly in `06_AI_AND_AGENTIC_SYSTEM.md`.
- ❌ No advertising trackers or third-party analytics scripts.
- ❌ No data export tool.

---

## 7. Technology stack (verified from the code)

### Frontend
- **Next.js 16.3.1** (App Router, React 19.2.8, TypeScript 5) — `package.json:19-21`
- **Tailwind CSS v4** with CSS-variable design tokens — `app/globals.css`
- **shadcn/ui "base-nova"** primitives on top of `@base-ui/react` — `components.json`, `components/ui/*`
- **lucide-react** icons — `package.json:17`
- **recharts 3.10** charts (lazy-loaded) — `package.json:22`, `app/(dashboard)/analytics/page.tsx:13-24`
- **vitest** + Testing Library (jsdom) — `vitest.config.ts`
- **Web Speech API** (recognition + synthesis) for voice — `components/jarvis/hooks/*`

### Backend
- **Python 3.13** + **FastAPI** + **Uvicorn** — `backend/requirements.txt`
- **Motor** (async MongoDB driver) + **Pydantic** — `backend/database.py`, `backend/models/*`
- **Groq** LLM API (primary), **OpenAI** SDK present but unused — `backend/services/ai/providers/*`
- **bcrypt** (passwords), **PyJWT** (tokens), **cryptography** (AES token encryption) — `backend/requirements.txt`
- **httpx** (Google/Brevo REST calls) — `backend/requirements.txt`

### Data & infrastructure
- **MongoDB Atlas** (database) — `backend/database.py`
- **Vercel** (frontend + backend hosting) — `next.config.ts`, `.env.example`
- **Brevo** (transactional email) — `backend/services/password_reset.py`
- **Google Gmail API** (read-only) — `backend/services/gmail.py`
- **Meta / WhatsApp Business Platform** (webhook) — `backend/routes/webhooks.py`

---

## 8. How the pieces fit together (60-second tour)

```
Browser (Next.js app)
  │  /api/* is rewritten by Next.js to the FastAPI backend
  │  httpOnly cookie "cai_token" carries the session
  ▼
FastAPI backend
  ├── routes/auth.py        register / login / me / forgot+reset password
  ├── routes/messages.py    list / create / delete / counts / priority
  ├── routes/webhooks.py    WhatsApp webhook + simulate
  ├── routes/gmail.py       OAuth connect / callback / manual refresh
  ├── routes/connections.py list / create / delete connections
  ├── routes/tasks.py       list / complete / snooze / view source
  ├── routes/analytics.py   day/week/month aggregates
  ├── routes/jarvis.py      POST /jarvis/chat  (the assistant)
  └── routes/ws.py          WebSocket /ws  (realtime)
        │
        ├── services/ai/orchestrate.py  ← the ONE AI entry point
        │       routing → single Groq call → attach routing record
        ├── services/ai/jarvis_*.py     ← the assistant's deterministic layers
        ├── services/gmail.py           ← OAuth + inbox poller
        ├── services/webhook_ingest.py  ← shared ingest for all sources
        ├── services/threads.py         ← deterministic thread linking
        └── services/realtime.py        ← per-user WebSocket fan-out
              │
              ▼
        MongoDB Atlas (users, messages, tasks, connections)
```

Full diagrams are in `02_SYSTEM_ARCHITECTURE.md`.

---

## 9. Honest assessment for the viva

**Strengths (defensible in a viva):**
- A genuinely end-to-end system: real OAuth, real webhook verification, real AI, real realtime, real tests.
- Strong security posture for a student project: per-user scoping everywhere, encrypted OAuth tokens, hashed reset tokens, signed webhook payloads, HMAC verification, circuit breaker.
- Deterministic-first AI design: the system still works when the LLM is down; failures are visible (`pending`) and retried.
- Unusually good test coverage for an FYP (29 backend test modules; ~500+ frontend test assertions).

**Weaknesses / things an examiner may probe:**
- The "agentic" framing is generous — the AI is a single analysis call plus rule-based routing, not autonomous agents.
- Some UI is presentational only (e.g. "Sign out everywhere" and "Delete account" in Settings do nothing).
- A temporary load-testing button (`BulkTestButton`) is still shipped in the dashboard.
- Several legal/operational facts are unresolved (jurisdiction, retention, age threshold).
- Gmail's `gmail.readonly` is a Google *restricted* scope: production use needs Google verification (and likely a CASA security assessment) that has not been completed.
- No runtime verification was performed while writing these docs — everything is **code-verified, not runtime-tested**.

---

## 10. Where to go next

- Read `README.md` in this folder for the full reading order.
- New to the project? Read `12_LEARN_MY_PROJECT.md` first.
- Preparing for the viva? `14_VIVA_INTERVIEW_QA.md`.
- Preparing a video? `13_VIDEO_SCRIPTS.md`.
- Want to know what is missing or risky? `15_FINDINGS_AND_GAPS.md`.
