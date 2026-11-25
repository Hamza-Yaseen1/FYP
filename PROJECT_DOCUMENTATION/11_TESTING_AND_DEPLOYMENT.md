# 11 — Testing & Deployment

> How the project is tested, how to run the tests, and how it is deployed. Includes the honest caveats about what the tests do and don't cover.

---

## 1. Testing overview

Sift has **two independent test suites**:

| Suite | Tool | Location | What it covers |
|-------|------|----------|----------------|
| Backend | **pytest** + FastAPI `TestClient` | `backend/tests/` | API endpoints, auth, AI pipeline, assistant, integrations, security |
| Frontend | **vitest** + Testing Library (jsdom) | `app/**/__tests__/`, `components/**/__tests__/`, `tests/**/` | Components, hooks, API clients, realtime |

There are also **era-stale standalone scripts** at `backend/test_*.py` (5 files) that are *not* part of the maintained suite — see the warning in §5.

---

## 2. Running the tests

### Backend
```powershell
# from the repo root
python -m pytest backend/tests/ -v
```
- Uses `communication_ai_test` as `DB_NAME` (forced by `conftest.py`).
- Loads `backend/.env` for secrets/config.
- An autouse fixture wipes `users`, `messages`, `tasks`, `connections` before and after **every** test.
- The full suite can take a few minutes; allow a generous shell timeout (e.g. 600 s).

### Frontend
```powershell
npm test           # vitest run (single pass)
npm run test:watch # watch mode
npm run lint       # eslint
npx tsc --noEmit   # type-check
npm run build      # production build
```

---

## 3. Backend test structure

`conftest.py` provides:
- `sys.path` setup so `backend` is importable.
- `DB_NAME=communication_ai_test` (forced — never the real DB).
- Session fixtures: a `TestClient(app)` and a pymongo handle for cleanup.
- Autouse `clean_db`: wipes the four collections around every test.

The suite is organised by concern (29 modules). Representative modules:

| Module | Focus |
|--------|-------|
| `test_auth.py` | Register/login/JWT/hashing/isolation/protected routes (~25 tests) |
| `test_messages.py` | Filters, counts, senders, search, tabs, pagination, create-through-orchestrator, reanalyze, priority override (~44 tests) |
| `test_analytics.py` | Window scoping, priority buckets (incl. pending), sources, periods |
| `test_jarvis*.py` | Assistant phases: routing, actions, intents, messages, conversation |
| `test_security*.py` | Cross-user isolation, webhook signature, retry, dedupe |
| Others | threads, context, attention, token budget, gmail, connections, tasks, webhooks |

### Backend test rules (important)
1. **Never `await` motor under `asyncio.run`** — Motor is bound to the `TestClient` event loop; a fresh loop fails with *"Future attached to a different loop"*. Use the TestClient loop or a **fake collection**.
2. **Mock `httpx.AsyncClient`** for all Google/Brevo calls — tests never hit the network.
3. **Register a fresh email per test** (via `clean_db`); never re-register the same email inside one test (409).
4. **Pin time** where dates matter (e.g. `_FrozenDatetime`) and seed messages at `start_today + timedelta(hours=6/7)` — never `now - 1h`, which can cross midnight into yesterday.
5. AI tests either disable the LLM (`_llm_configured = False`) or install a fake provider.

---

## 4. Frontend test structure

- Runner config: `vitest.config.ts` (jsdom; includes `app`, `components`, `tests`).
- **Vitest globals are OFF** → every component test must call `afterEach(cleanup)` (RTL won't auto-clean).
- Fakes/helpers:
  - `components/__tests__/fakeWebSocket.ts` — a fake WebSocket.
  - Fake `speechSynthesis` / `SpeechRecognition` installed via `Object.defineProperty` for the assistant tests.
  - A `ResizeObserver` stub for recharts (analytics test).
- Focus areas: `SearchBar`, `FilterBar`, `InboxTabs`, `PriorityBadge`, `EmptyState`, `RealtimeProvider`, the whole `components/jarvis/` suite (assistant, actions, barge-in, mic, orb, panel, both speech hooks, API), analytics page, inbox page, logout route.

---

## 5. ⚠️ Era-stale scripts — do not chase

`backend/test_ai_analysis.py`, `backend/test_task_extraction.py`, `backend/test_priority_integration.py`, `backend/test_priority_edge_cases.py`, `backend/test_attention_pipeline.py` are **historical artifacts** from an earlier era. They:
- Call async collections synchronously, and
- Some require a live server / shared Atlas / real auth.

They are **not** part of the maintained suite. If they fail, that is expected — compare the failing set only against the maintained `backend/tests/` suite.

---

## 6. Verification checklist (before you claim something works)

```powershell
# Backend
python -m pytest backend/tests/ -q

# Frontend
npm test
npm run lint
npx tsc --noEmit
npm run build
```

A feature is "done" only when: tests pass, lint is clean, types are clean, and the build succeeds.

---

## 7. Deployment

### Topology
- **Frontend:** Vercel (Next.js). Public site: `https://fyp-f8vk.vercel.app`.
- **Backend:** Vercel (FastAPI). Example: `https://fyp-omega-peach.vercel.app`.
- **Database:** MongoDB Atlas.
- The frontend's `next.config.ts` **requires** `BACKEND_URL` in production and rewrites `/api/*` to it.

### Frontend environment variables
| Variable | Purpose |
|----------|---------|
| `BACKEND_URL` | Absolute backend URL used by the rewrite (required in prod) |
| `NEXT_PUBLIC_API_BASE` | API base path, default `/api` |
| `NEXT_PUBLIC_WS_URL` | Optional explicit WebSocket URL |
| `NEXT_PUBLIC_WS_USE_TOKEN` | Dev-only WS token fallback |

### Backend environment variables
See `backend/.env.example`. Critical: `MONGO_URI`, `DB_NAME`, `JWT_SECRET`, `ENCRYPTION_KEY`, `GROQ_API_KEY`. Feature-specific: Google, WhatsApp, Brevo. Behavioural: poll/retry intervals, cookie flags.

### Deployment steps (outline)
1. Deploy the backend; set all backend env vars in Vercel.
2. Deploy the frontend; set `BACKEND_URL` to the backend URL.
3. In Google Cloud Console, set the redirect URIs to the deployed backend.
4. In Meta, point the WhatsApp webhook at `https://<backend>/webhooks/whatsapp` with the verify token.
5. Verify `GET /health` responds.

### Production caveats
- **Cookie flags:** with the frontend and backend on different Vercel domains, cross-site cookies need `COOKIE_SAMESITE=None` and `COOKIE_SECURE=true`.
- **Long-lived loops:** the Gmail poller and retry sweep are in-process; on a runtime that scales to zero they may not run continuously.
- **WebSockets** are per-instance; a multi-instance backend would need a shared pub/sub.
- **Gmail restricted scope** needs Google verification before public use.

---

## 8. Seed / operational scripts

In `backend/scripts/` (dev/ops only):
- `setup_connection_indexes.py` — creates the `connections` unique index.
- `setup_whatsapp_connection.py` — creates a WhatsApp connection for the first user.
- `assign_legacy_data.py` — assigns `user_id` to legacy documents missing it.
- `simulate_meta_webhook.py` — signs and sends a realistic Meta payload locally.
- `test_webhook.py` — prints a webhook setup health check.
- `backend/check_models.py` — lists Groq models (useful when choosing `GROQ_MODEL`).

---

## 9. Test-coverage honesty

**Well covered:** auth, message listing/filtering, analytics aggregation, the AI pipeline (with fakes), the assistant (all phases), security isolation, webhook signature, dedupe, retry.

**Lightly or not covered:** real Google/Brevo/WhatsApp calls (mocked), browser-only voice behaviour (faked in jsdom), deployment/runtime behaviour, load/performance, accessibility (no axe), and end-to-end browser tests (no Playwright/Cypress). All security claims are **code-verified, not runtime-tested**.
