# Project Audit Report — Signal Desk (`my-app`)

**Report date:** 2026-10-21
**Auditor:** opencode (read-only audit)
**Scope:** Full repository at `D:\FYP\my-app` — Next.js 16 frontend + FastAPI/Motor/MongoDB backend + Groq AI pipeline + Gmail/WhatsApp integrations + JARVIS voice assistant.
**Exclusions:** `backend/venv/**` (vendored third-party code), `node_modules/**`, `.next/**`, `backend/__pycache__/**`, lockfiles (metadata only).

> This report is the single permitted output of the audit. No application code, configuration, database, or Git history was modified. Findings are labelled with confidence: **Confirmed** (verified in source), **Likely** (strong evidence, one assumption), **Needs Verification** (requires runtime/test to confirm).

> **RE-AUDIT (2026-10-21, second pass):** Every original finding was re-verified against the current tree. Result: **7 Fixed, 5 Partially Fixed, 24 Still Open, 1 No Longer Applicable** (+2 minor newly noted issues, 0 regressions found in the changed security paths). The original sections 1–8 below are preserved unchanged as audit history; the authoritative current status is **Section 9 — Re-Audit**.

---

## 1. Executive Summary

Signal Desk is a well-structured, security-conscious full-stack application. The architecture cleanly separates a deterministic AI orchestration layer from the LLM provider, enforces user-scoped data access on nearly every query, and degrades gracefully when the LLM is unavailable. The JARVIS assistant is layered (deterministic routing → NLU → message intelligence → conversation) with sensible ownership rules so earlier layers keep byte-identical behaviour.

The audit found **34 findings**: **0 Critical**, **5 High**, **13 Medium**, **16 Low**. There are no remote-code-execution, SQL/NoSQL-injection-to-privilege-escalation, or authentication-bypass issues. The most serious concerns are operational/security-hardening: a temporary unauthenticated-by-design load-test route shipped in `main.py`, session cookies set with `secure=False`, unauthenticated AES-CBC token encryption, an always-on 401 redirect that breaks the login error path, and unbounded in-memory conversation state.

Two items were verified as **correctly implemented** despite looking risky: purpose-scoped WebSocket tokens (rejected as session tokens) and the `user_id`-first `$match` rule across all aggregations.

### Top 5 Priorities (do these first)
1. **SEC-01** — Remove or gate the temporary `/test/bulk-messages` route (P0).
2. **SEC-02** — Enable `secure=True` on session cookies in production (P0).
3. **SEC-03** — Replace unauthenticated AES-CBC with AES-GCM (AEAD) for stored OAuth tokens (P1).
4. **BUG-01** — Fix the global 401 `window.location.assign("/login")` that destroys the login error banner and can redirect-loop (P1).
5. **ARCH-01 / PERF-01** — Bound the in-memory JARVIS `_CONTEXTS` and Groq circuit state (unbounded growth / no eviction) (P1).

---

## 2. Severity Definitions

| Severity | Meaning |
|----------|---------|
| **Critical** | Exploitable auth bypass, RCE, mass data exposure, or data loss in normal operation. Fix immediately. |
| **High** | Serious security weakness, credential/secret exposure risk, user-facing breakage, or resource exhaustion reachable in production. |
| **Medium** | Correctness bug, hardening gap, performance/scaling issue, or reliability risk under load or failure. |
| **Low** | Code quality, maintainability, minor UX, or defence-in-depth improvement. |
| **Info** | Observation / positive confirmation; no action strictly required. |

**Confidence:** Confirmed / Likely / Needs Verification.

---

## 3. Findings

### Standard Finding Template
Each finding uses: **ID — Title** · Severity · Confidence · Location · Description · Impact · Evidence · Recommendation.

---

### SEC-01 — Temporary load-testing endpoint shipped in production app
- **Severity:** High · **Confidence:** Confirmed
- **Location:** `backend/routes/test.py:107-202`; registered in `backend/main.py:22,177`
- **Description:** `POST /test/bulk-messages` is explicitly marked "TEMPORARY … should be removed before production". It is auth-gated by `get_current_user`, but it lets any authenticated user insert up to 150 messages that each run the **full AI analysis pipeline** synchronously, plus thread resolution.
- **Impact:** Authenticated cost/abuse vector: a single user can trigger up to 150 LLM calls per request in a loop, burning the shared Groq quota (and tripping the circuit breaker for everyone). Also pollutes the message store with artificial data.
- **Evidence:** `count: int = Field(..., ge=1, le=150)`; loop calls `process_message(...)` per message.
- **Recommendation:** Delete `routes/test.py` and its `include_router`/import from `main.py`, or gate behind an env flag (`ENABLE_TEST_ROUTES`) that defaults off and is excluded from production builds.

---

### SEC-02 — Session cookie set with `secure=False`
- **Severity:** High · **Confidence:** Confirmed
- **Location:** `backend/routes/auth.py:19-28` (set) and `:76-82` (delete)
- **Description:** The `cai_token` session cookie is `httponly=True`, `samesite="lax"`, but `secure=False`. Over HTTPS-in-front-of-proxy, the browser may still send it over plaintext HTTP if any endpoint is reachable via HTTP, exposing it to network interception.
- **Impact:** Session-token theft via downgrade/MITM on non-TLS paths.
- **Evidence:** `secure=False` hard-coded in both `_set_session_cookie` and `logout`.
- **Recommendation:** Drive `secure` from config (`COOKIE_SECURE=true` in production) so local dev stays functional while deployed environments force TLS-only cookies. Mirrored `delete_cookie` must match.

---

### SEC-03 — Unauthenticated AES-CBC used to encrypt OAuth tokens
- **Severity:** High · **Confidence:** Confirmed
- **Location:** `backend/utils/encryption.py:18-46`
- **Description:** Gmail access/refresh tokens are encrypted with AES-CBC (`modes.CBC`) using PKCS7 padding and a random IV, but **no MAC/authentication tag**. CBC without an integrity check is malleable; padding-oracle and bit-flipping attacks are possible against stored ciphertext.
- **Impact:** Stored OAuth refresh tokens (high-value: long-lived Gmail access) are not integrity-protected. If an attacker can influence or observe ciphertext (e.g. via a DB read), decryption manipulation is theoretically possible.
- **Evidence:** `Cipher(algorithms.AES(key), modes.CBC(iv))` with no HMAC/`mac`; `ENCRYPTION_KEY` from env, base64-decoded.
- **Recommendation:** Migrate to AES-GCM (AEAD) via `cryptography.hazmat.primitives.ciphers.aead.AESGCM`, storing `nonce || ciphertext || tag`. Provide a lazy re-encrypt-on-read migration for existing tokens. (Note: `cryptography` is already a dependency.)

---

### SEC-04 — Overly permissive CORS for a cookie-credentialed API
- **Severity:** Medium · **Confidence:** Confirmed
- **Location:** `backend/main.py:136-145`
- **Description:** `allow_origins` is restricted to localhost, and `allow_credentials=True`, but `allow_methods=["*"]` and `allow_headers=["*"]`. Origins are safe **only** as long as the app is never deployed without updating this list; the wildcard methods/headers broaden attack surface (e.g. simple-request CSRF-adjacent patterns) and there is no `allow_origin_regex` lockdown.
- **Impact:** If deployed as-is behind a real domain, the origin allowlist will silently block prod, tempting a wildcard "*" fix which, combined with `allow_credentials=True`, is invalid/unsafe. Wildcard headers allow arbitrary custom headers.
- **Recommendation:** Move allowed origins to env config; explicitly enumerate methods (`GET,POST,PUT,PATCH,DELETE`) and headers. Never set `allow_origins=["*"]` with credentials.

---

### SEC-05 — Webhook signature verification must remain mandatory (verify rotation & missing-key path)
- **Severity:** Medium · **Confidence:** Needs Verification
- **Location:** `backend/routes/webhooks.py`, `backend/services/webhook_ingest.py`
- **Description:** Per project notes, WhatsApp webhook signature is SHA-256 HMAC and empty/missing/malformed → 403. This was not re-verified line-by-line in this pass against the actual route implementation for the **ordering** (verify-before-parse) and the **empty-secret** behaviour.
- **Impact:** If the shared secret is unset/empty, an HMAC computed with an empty key is trivially forgeable — a misconfiguration could silently accept unsigned payloads.
- **Recommendation:** Confirm: (1) signature verified *before* body is trusted, (2) a missing/empty `WHATSAPP_APP_SECRET` **fails closed** (reject all) rather than comparing against an empty HMAC, (3) `hmac.compare_digest` is used (constant-time). Add a regression test asserting 403 when the secret env is empty.

---

### SEC-06 — Development-only WebSocket `?token=` fallback
- **Severity:** Low · **Confidence:** Confirmed (implemented safely)
- **Location:** `backend/routes/ws.py:46-99`; `backend/services/security.py:58-84`
- **Description:** An opt-in `?token=` handshake exists for local dev, gated by `WS_ALLOW_QUERY_TOKEN`. Tokens are short-lived (120s), carry `purpose="ws"`, and `decode_token` **rejects any token carrying a `purpose` claim**, so a WS token cannot be replayed as a session token. Implemented correctly.
- **Impact:** None if the flag stays off in production; query-string tokens can leak into logs if enabled.
- **Recommendation:** Keep default off; document that the flag must never be set in production. Consider stripping tokens from access logs.

---

### SEC-07 — `/testdb` unauthenticated database probe
- **Severity:** Low · **Confidence:** Confirmed
- **Location:** `backend/main.py:159-164`
- **Description:** `GET /testdb` runs `database.command("ping")` with no auth and returns the raw ping result. `/health` similarly returns only `{"status":"ok"}` (fine).
- **Impact:** Minor info disclosure: confirms DB reachability and reflects upstream response fields to unauthenticated callers.
- **Recommendation:** Remove `/testdb` from production or return a static boolean; keep `/health` as the probe.

---

### SEC-08 — Secrets/JWT secret handling review
- **Severity:** Low · **Confidence:** Confirmed (positive) / Needs Verification (deployment)
- **Location:** `backend/services/security.py:17-21`; `backend/database.py:7`; root `AGENTS.md`
- **Description:** `JWT_SECRET` fails hard (raises `RuntimeError`) if unset — good. `MONGO_URI` defaults to `mongodb://localhost:27017` if unset (safe default). `.env` files are not to be committed (verify `.gitignore`).
- **Impact:** If `backend/.env` were ever committed with real Atlas credentials/Groq key/JWT secret, full compromise. Redacted reference: `backend/.env` contains `MONGO_URI`, `JWT_SECRET`, `ENCRYPTION_KEY`, `GROQ_API_KEY`, `GOOGLE_CLIENT_ID/SECRET`, `WHATSAPP_*` (values intentionally not reproduced here).
- **Recommendation:** Verify `.env`, `*.env`, `venv/`, `__pycache__/` are git-ignored. Rotate any secret that may have appeared in git history. Use `.env.example` with placeholders only.

---

### BUG-01 — Global 401 redirect breaks the login error banner and can loop
- **Severity:** High · **Confidence:** Confirmed
- **Location:** `lib/api.ts:57-61` (cached GET) and `:119-126` (main fetch); interaction with `app/(auth)/login/page.tsx:57-68`; `proxy.ts:22-29`
- **Description:** Every `apiFetch` that receives HTTP 401 from anywhere calls `window.location.assign("/login")` and throws. This means a **failed login attempt** (which legitimately returns 401 `Invalid email or password`) triggers a full navigation away from the login page, so the intended inline error banner never renders. Combined with `proxy.ts` (which redirects `/login` → `/dashboard` when a `cai_token` cookie is *present* but invalid/expired), an expired-but-present cookie can produce a loop: `/login` (cookie present) → `/dashboard` → API 401 → `/login` → …
- **Impact:** Users cannot see login errors; expiry produces a confusing redirect loop instead of a clean sign-in.
- **Evidence:** `res.status === 401 && ... window.location.assign("/login")` in both code paths; login page expects to render `ApiError.detail`.
- **Recommendation:** Do not auto-redirect for auth endpoints. Exempt `/auth/login` (and `/auth/register`), or centralize redirect handling in a React-level provider that can distinguish "session lost on a protected route" from "credential rejected at login". Optionally clear the cookie in `proxy.ts` when present-but-invalid before redirecting to `/login`.

---

### BUG-02 — GET cache key ignores headers/vary; dead `ttl` variable
- **Severity:** Medium · **Confidence:** Confirmed
- **Location:** `lib/api.ts:27-33,46,74,89-97`
- **Description:** The cache key is `${method}:${API_BASE}${path}` only — it ignores query-varying headers and user identity. `const ttl = DEFAULT_TTL_MS;` is declared but never varied. `clearCache()` matches by `endsWith(path)`, which can over-match (e.g. `/messages` also matches `/x/messages`).
- **Impact:** (a) After logout/login as a different user, cached GET responses for the *first* user can be served to the second user within the 10s TTL if the cache is not cleared on identity change. (b) `endsWith` path invalidation could evict unrelated entries. (c) Dead code reduces clarity.
- **Recommendation:** Include user/session identity (or simply clear the whole cache on auth transitions), use exact-key matching in `clearCache`, and remove the dead `ttl` variable.

---

### BUG-03 — JARVIS assistant can freeze in busy/confirming state
- **Severity:** Medium · **Confidence:** Confirmed (reported by frontend audit)
- **Location:** `components/jarvis/JarvisAssistant.tsx:146-148,174-178,224-229`
- **Description:** Closing the panel mid-request (generation guard bumps a `generationRef`) can leave `busy`/`confirming` state un-cleared because the response handler that would clear it is discarded as stale.
- **Impact:** Orb can remain "thinking" and the composer disabled until remount.
- **Recommendation:** On close/generation-bump, explicitly reset `busy=false`, `confirming=null`, and clear the pending promise state rather than relying solely on the discarded response handler.

---

### BUG-04 — Speech recognition hook has no unmount cleanup
- **Severity:** Medium · **Confidence:** Confirmed
- **Location:** `components/jarvis/hooks/useSpeechRecognition.ts`
- **Description:** The hook arms the microphone (including `startSilent()` during TTS) but does not call `recognition.stop()/abort()` on unmount.
- **Impact:** Microphone can remain hot after the component unmounts; privacy concern and battery drain.
- **Recommendation:** Add a `useEffect` cleanup that stops/aborts recognition and nulls handlers on unmount.

---

### BUG-05 — `asyncio.gather` in analytics fails whole response if one aggregation raises
- **Severity:** Medium · **Confidence:** Likely
- **Location:** `backend/services/analytics.py:42-48`
- **Description:** Five independent aggregations run under `asyncio.gather` with no `return_exceptions=True`. Any single failure (e.g. transient Mongo error on one pipeline) raises and returns HTTP 500 for the whole analytics snapshot.
- **Impact:** One flaky query blanks the entire analytics page.
- **Recommendation:** Either accept the all-or-nothing semantics intentionally (document it) or use `return_exceptions=True` and default failed sub-aggregations to zero/empty with a logged warning.

---

### BUG-06 — Tasks period-scoping loads up to 10,000 docs and filters in Python
- **Severity:** Medium · **Confidence:** Confirmed
- **Location:** `backend/services/analytics.py:119-151`
- **Description:** `_tasks_summary` fetches up to 10,000 tasks into memory then re-scopes by resolving parent message `received_at` per task. The comment claims a pre-filter, but the `created_at` window is only a bound; the final count is still assembled in Python with an `ObjectId()` construction per task.
- **Impact:** Memory/CPU cost and `ObjectId` conversion overhead scale with a user's task count.
- **Recommendation:** Push period-scoping to the DB with an aggregation `$lookup`/`$match` on the parent message, or at least cap and paginate; avoid re-parsing ObjectIds where a dict lookup by string id would suffice.

---

### PERF-01 — Unbounded in-memory JARVIS conversation contexts
- **Severity:** Medium · **Confidence:** Confirmed
- **Location:** `backend/services/ai/jarvis_agent.py:148-156`
- **Description:** `_CONTEXTS: dict[str, _ConversationContext]` grows one entry per distinct user id and is **never evicted**. Each holds a deque of up to 8 turns plus last-intent/ranges/tasks. In a long-lived multi-process deployment behind a load balancer, context is also process-local (lost on restart / not shared across workers).
- **Impact:** Slow memory growth proportional to distinct users; stale context after restart; inconsistent context across workers.
- **Recommendation:** Add TTL/LRU eviction, or move to Redis if multi-worker context is required. At minimum, cap the dict size and evict least-recently-used.

---

### PERF-02 — Groq circuit-breaker/limiter state is process-local and loop-scoped
- **Severity:** Low · **Confidence:** Confirmed
- **Location:** `backend/services/ai/providers/groq.py:92-93,106,168-174`
- **Description:** The circuit breaker (`_CIRCUIT`), probe lock and semaphore are module-global, created lazily per event loop. This is intentional and correct for a single-process/single-loop deployment (documented), but it means: (a) each worker has its own quota view (a quota-exhausted breaker in worker A is invisible to worker B), (b) tests that spin up new loops correctly re-create the primitives but production correctness assumes one loop.
- **Impact:** Under multiple uvicorn workers, thundering-herd protection is per-worker, not global.
- **Recommendation:** Acceptable for current single-process deployment; document the constraint. If scaling out, move the breaker to a shared store (Redis) or a single dedicated AI gateway.

---

### PERF-03 — `RETRY_ATTEMPTS`/backoff tuning could mask real failures
- **Severity:** Low · **Confidence:** Confirmed
- **Location:** `backend/services/ai/providers/groq.py:58-60,266-281`
- **Description:** Wait is capped at 1s and honors Groq `Retry-After` only if ≤1s. This is a deliberate showcase-safety tradeoff (documented). Non-TPD 429s are retried once. Reasonable, but a genuine transient outage is resolved by fallback rather than patient retry.
- **Impact:** Slightly higher rate of deterministic fallbacks during provider blips.
- **Recommendation:** No change required; keep the explicit comment. Optionally make the cap configurable for batch/backfill jobs that can afford to wait.

---

### ARCH-01 — Layered JARVIS dispatch is complex and duplicated
- **Severity:** Medium · **Confidence:** Confirmed
- **Location:** `backend/services/ai/jarvis_agent.py:353-522`, `jarvis_intents.py`, `jarvis_messages.py` (975 lines)
- **Description:** `process_command` now chains Phase 4 → task follow-ups → Phase 6 delete → Phase 6 read → Phase 2 actions → Phase 3 NLU → Phase 3/6 classifier → navigation/info/chat, each with ownership guards (`_owned_elsewhere`, `_nav_owned`). There are duplicated matchers across files (`NAV_VERBS`/`NAV_TARGETS` now centralized, but message-word regexes, greeting/help markers, priority patterns appear in multiple modules).
- **Impact:** High cognitive load; ordering changes risk silent regressions; three near-duplicate LLM classifiers (`llm_info_intent`, `llm_message_intent`, `llm_intent`) coexist (the combined one supersedes the others).
- **Recommendation:** Consolidate to the single combined classifier and remove the two superseded functions if unused; extract shared regexes/whitelists into one module; document the dispatch order as the single source of truth.

---

### ARCH-02 — Two AI providers diverge from the base interface
- **Severity:** Medium · **Confidence:** Confirmed
- **Location:** `backend/services/ai/providers/base.py:16-21`, `openai.py:78-129`, `groq.py:590-594`
- **Description:** `BaseLLMProvider.analyze` is declared as `analyze(self, message, context=None)` but both concrete providers add `current_message_id` and Groq also adds a `chat()` method not on the ABC. `OpenAIProvider` is a legacy path (OpenAI key) that still logs `api_key[:20]` — **partial secret leakage into logs**.
- **Impact:** Interface contract drift; `OpenAIProvider` logs a key prefix (`self.logger.info(f"✅ Initializing OpenAI provider with API key: {api_key[:20]}...")`), violating the "never log key parts" rule Groq explicitly follows.
- **Recommendation:** Align the ABC signature; **remove the key-prefix log from `openai.py:74`**; either retire `OpenAIProvider` or bring it to parity (no secret logging, budget handling). Confirm whether the OpenAI path is still reachable (`get_provider` selection).

---

### ARCH-03 — Single-process assumptions baked into ingestion/realtime
- **Severity:** Low · **Confidence:** Confirmed
- **Location:** `backend/services/realtime.py:1-14`, `backend/main.py:82-131`
- **Description:** Realtime fan-out is an in-process registry; Gmail poller and retry sweep are `asyncio.create_task` loops started in `lifespan`. Correct for one process; would double-run (two pollers, duplicate sweeps) if scaled to multiple workers without a lock.
- **Impact:** Multi-worker deployment would run N pollers and N retry loops (duplicate work / duplicate Gmail fetches).
- **Recommendation:** Document single-worker requirement, or add a distributed lock (e.g. Mongo `findOneAndUpdate` lease) before enabling multiple workers.

---

### ARCH-04 — Background analysis fire-and-forget with no backpressure
- **Severity:** Medium · **Confidence:** Confirmed
- **Location:** `backend/services/webhook_ingest.py` (spawns `asyncio.create_task(_analyze_and_store)` when `background_tasks is None`, tracked in a module set)
- **Description:** Ingestion spawns analysis tasks tracked only by a module-level set; there is no visible queue, concurrency bound beyond the Groq semaphore, or drain-on-shutdown for these specific tasks. Bulk ingestion (webhook burst, Gmail poll, or SEC-01 route) can spawn many tasks.
- **Impact:** Task explosion under burst; in-flight analyses may be dropped on shutdown; harder to observe.
- **Recommendation:** Route background analyses through a bounded queue/worker pool; ensure graceful drain on shutdown; expose a metric of pending analyses (partially covered by `retry_pending`).

---

### ARCH-05 — `ai_analysis_collection` declared but unused
- **Severity:** Low · **Confidence:** Confirmed
- **Location:** `backend/database.py:16`
- **Description:** `ai_analysis_collection = db["ai_analysis"]` is defined but analysis is embedded in `messages.ai_analysis`. Dead collection handle.
- **Impact:** Confusion about the data model.
- **Recommendation:** Remove the unused collection handle.

---

### DATA-01 — Dual timestamp convention (`created_at` vs `received_at`) is fragile
- **Severity:** Medium · **Confidence:** Confirmed
- **Location:** `backend/services/analytics.py:61-63` (`received_at`), `jarvis_messages.py`/`jarvis_agent.py` (`created_at`), ingest paths set both
- **Description:** Analytics windows and trends use `received_at`; JARVIS "today/yesterday" and several counts use `created_at`. Both are set at ingest, but the divergence means any code path that sets one and not the other silently changes day-bucket answers, and the two can drift (UTC vs local, backfills).
- **Impact:** Inconsistent "today" counts between the analytics page and JARVIS answers; the AGENTS notes already flag a midnight-crossing test hazard.
- **Recommendation:** Standardize on ONE canonical event-time field (recommend `received_at` for external event time) everywhere, or add a DB invariant/test asserting `created_at == received_at` for ingested messages. Document the convention (currently "UTC everywhere").

---

### DATA-02 — Priority bucket mapping relies on `$group` `_id` string equality
- **Severity:** Low · **Confidence:** Confirmed
- **Location:** `backend/services/analytics.py:85-90`
- **Description:** Unknown/missing priority maps to the `pending` bucket (intentional, documented). Correct, but the mapping is duplicated in JARVIS (`jarvis_messages._counts`, `_run_priority`) and the frontend. Divergent copies risk drift.
- **Impact:** Low; maintainability.
- **Recommendation:** Centralize the allowed-priority set and normalization in one backend constant.

---

### DATA-03 — No TTL / retention policy on messages, tasks, or websocket payloads
- **Severity:** Low · **Confidence:** Needs Verification
- **Location:** `backend/database.py`, `backend/main.py` indexes
- **Description:** No TTL indexes or retention/archival logic observed for `messages`/`tasks`. Fine for a showcase; a long-running deployment grows unbounded.
- **Impact:** Storage growth, slower analytics over time.
- **Recommendation:** Plan a retention/archival policy if this moves beyond a demo.

---

### TEST-01 — Pre-existing backend failures masked as "environmental"
- **Severity:** Medium · **Confidence:** Confirmed (per project docs) / Needs Verification (current)
- **Location:** `backend/tests/*` (webhooks/gmail/dedup suites)
- **Description:** Project notes state the repo has ~23 pre-existing failures requiring env secrets (WhatsApp offsets, Gmail). This is reasonable, but a suite that cannot pass on a clean checkout hides real regressions and makes "all green" impossible to assert.
- **Impact:** Regression detection is weakened; contributors can't distinguish broken from env-gated.
- **Recommendation:** Mark env-required tests with `pytest.mark.skipif`/`xfail` keyed on the missing env vars so a clean run is green-by-default and CI can enforce "no new failures". Provide a documented `.env.test`.

---

### TEST-02 — Frontend tests depend on global cleanup discipline
- **Severity:** Low · **Confidence:** Confirmed (per docs)
- **Location:** `components/jarvis/__tests__/*` (require `afterEach(cleanup)` because vitest globals are OFF)
- **Description:** RTL does not auto-cleanup with globals disabled; tests must call `afterEach(cleanup)` manually. Easy to forget → cross-test leakage.
- **Impact:** Flaky/leaky tests.
- **Recommendation:** Enable a global setup file that registers `afterEach(cleanup)` once, or turn on RTL's auto-cleanup via a shared setup.

---

### TEST-03 — Test DB isolation depends on session fixtures + autouse wipe
- **Severity:** Low · **Confidence:** Confirmed
- **Location:** `backend/tests/conftest.py:22-45`
- **Description:** `clean_db` autouse wipes users/messages/tasks/connections before+after each test; session `client` creates a `TestClient(app)` with lifespan (starts/stops pollers). Soli d. One risk: tests share a single Mongo URI (`MONGO_URI` from `.env` = Atlas in this environment) under `communication_ai_test` — a misconfigured `MONGO_URI` could point at a production cluster.
- **Impact:** Low correctness risk; high blast-radius risk if `DB_NAME` were overridden incorrectly.
- **Recommendation:** Add a hard guard asserting `DB_NAME` endswith `_test` before any destructive op.

---

### CONF-01 — Frontend/backend contract drift risk for `/api` proxy
- **Severity:** Low · **Confidence:** Confirmed
- **Location:** `next.config.ts:3-13`, `lib/api.ts:1`
- **Description:** Frontend calls `/api/*`, rewritten to `${BACKEND_URL}/*` (default `http://localhost:8000`). `NEXT_PUBLIC_API_BASE` can override to a non-`/api` base, but the rewrite still maps `/api`. If `NEXT_PUBLIC_API_BASE` is set inconsistently with the proxy, requests 404.
- **Impact:** Config footgun between two independent env knobs.
- **Recommendation:** Document that `NEXT_PUBLIC_API_BASE` should normally stay unset (proxy handles routing); assert consistency at build or in a startup check.

---

### CONF-02 — Backend env vars are read ad-hoc with scattered defaults
- **Severity:** Low · **Confidence:** Confirmed
- **Location:** `groq.py`, `ws.py`, `main.py`, `database.py`, `security.py`
- **Description:** Many `os.getenv` calls with inline defaults (`GROQ_MODEL`, `GROQ_FALLBACK_MODEL`, `GROQ_MAX_OUTPUT_TOKENS`, `GMAIL_POLL_INTERVAL_SECONDS`, `RETRY_INTERVAL_SECONDS`, `WS_ALLOW_QUERY_TOKEN`, etc.). No central settings module or `.env.example` validation.
- **Impact:** Typos in env names silently fall back to defaults; no single source of truth.
- **Recommendation:** Introduce a Pydantic `Settings` object validated at startup (fail fast on missing critical vars), and publish `.env.example`.

---

### CONF-03 — `next.config.ts` has no security headers / image config
- **Severity:** Low · **Confidence:** Confirmed
- **Location:** `next.config.ts` (only `rewrites`)
- **Description:** No `headers()` for CSP, HSTS, `X-Content-Type-Options`, `Referrer-Policy`, `X-Frame-Options`, or `Permissions-Policy`.
- **Impact:** Missing defence-in-depth headers (XSS/clickjacking/MIME-sniffing hardening).
- **Recommendation:** Add a `headers()` block (or middleware) with a conservative CSP and standard security headers; mirror HSTS at the TLS terminator.

---

### CONF-04 — `recharts`/`mongodb` frontend dependency surface
- **Severity:** Info · **Confidence:** Confirmed
- **Location:** `package.json:18`
- **Description:** `mongodb` (driver) is listed as a frontend dependency. If any client bundle imports it, it would leak DB-driver code/type surface to the browser (the app should only talk HTTP to the backend).
- **Impact:** Potential bundle bloat and architecture smell if imported client-side; no evidence of actual client import found in this pass.
- **Recommendation:** Confirm no client component imports `mongodb`; if server-only, ensure it stays out of client bundles (it likely is, since all data goes through `lib/api`).

---

### BUG-07 — `_message_priority_buckets` hard-caps aggregation at 100 groups
- **Severity:** Low · **Confidence:** Confirmed
- **Location:** `backend/services/analytics.py:84`
- **Description:** `.to_list(length=100)` for the priority `$group`. Since `_id` is priority (≤~6 values), 100 is plenty — safe. Noted for completeness; similar caps elsewhere (`length=100` for sources, `10_000` for trends) are pragmatic.
- **Impact:** None for priorities; source counts also bounded to 100 distinct sources (fine in practice).
- **Recommendation:** No action; document the cap rationale.

---

### BUG-08 — `webhook_ingest`/`test.py` duplicate message-doc construction
- **Severity:** Low · **Confidence:** Confirmed
- **Location:** `backend/routes/test.py:149-176` vs `backend/services/webhook_ingest.py`
- **Description:** The test route re-implements message document construction and analysis persistence instead of calling `ingest_message`, bypassing the single ingestion funnel (thread stamping, dedupe, realtime emit, background analysis).
- **Impact:** Divergence from the canonical ingest path (compounds SEC-01).
- **Recommendation:** Delete with SEC-01; if kept, call `ingest_message`.

---

### BUG-09 — Confidence field silently coerced
- **Severity:** Low · **Confidence:** Confirmed
- **Location:** `backend/services/ai/providers/groq.py:638-640`
- **Description:** Non-numeric or out-of-range `confidence` is coerced to `0.5`. Reasonable defensive coding, but a systematically broken model output would be masked as a valid 0.5.
- **Impact:** Low; observability loss.
- **Recommendation:** Log a warning when coercion triggers so provider degradation is visible.

---

### BUG-10 — `jarvis_agent` imports inside function bodies
- **Severity:** Low · **Confidence:** Confirmed
- **Location:** `backend/services/ai/jarvis_agent.py:1032,1091`
- **Description:** `from database import messages_collection` and `from services.ai.jarvis_messages import run_message_intent` are imported inside functions despite module-level imports already existing elsewhere. Dead/duplicative and a minor import-cycle smell.
- **Impact:** Style/maintainability.
- **Recommendation:** Hoist to module top or remove the redundant inner imports.

---

### PERF-04 — Analytics `asyncio.gather` opens five concurrent Mongo round-trips per request
- **Severity:** Info · **Confidence:** Confirmed
- **Location:** `backend/services/analytics.py:42-48`
- **Description:** Good design (concurrency), but there is no per-request caching; every PeriodToggle re-fetches 5 aggregations. TTL/caching may be desirable under load.
- **Impact:** Low at showcase scale.
- **Recommendation:** Consider a short server-side cache keyed by `(user_id, period, minute)` if analytics load grows.

---

## 4. Positive Confirmations (verified good)

- **User isolation:** Every aggregation in `analytics.py` begins with a `user_id` `$match` (`_base_match`); JARVIS fetchers (`_fetch`, `_counts`, `_fetch_pending_tasks`, `_handle_read_messages`) all filter by `user_id`; `get_current_user` resolves ownership server-side and is never taken from payload.
- **WebSocket auth:** `decode_token` rejects `purpose`-scoped tokens; WS close code 1008 on failure before `accept()` (no event leak).
- **Bearer-adjacent token separation:** `create_ws_token`/`decode_ws_token` cleanly separated from session tokens.
- **Password hashing:** bcrypt with per-password salt; `verify_password` catches `ValueError`.
- **JWT secret fail-fast:** `RuntimeError` when unset.
- **AI graceful degradation:** Groq circuit breaker + bounded retries + `MessageTooLargeError` terminal path + deterministic fallbacks; JARVIS `_llm_configured()` also checks breaker availability.
- **Dedupe index migration:** Legacy global `external_message_id_1` dropped, replaced by user-scoped composite (prevents cross-user collisions).
- **JARVIS context safety:** "Text only" history injected into prompts; no DB data, no user ids, no other users; LLM classifiers whitelist-only and never return params/nav.
- **Sole AI entry point:** Routes/services funnel through `process_message` (orchestrator), never `analyze_message` directly.

---

## 5. File Review Status

| Area | Files | Status |
|------|-------|--------|
| Backend bootstrap/config | `main.py`, `database.py`, `dependencies.py`, `requirements.txt` | Reviewed |
| Auth/security | `routes/auth.py`, `services/security.py`, `utils/encryption.py` | Reviewed |
| Routes | `auth`, `messages`, `webhooks`, `tasks`, `connections`, `gmail`, `analytics`, `jarvis`, `ws`, `test` | Reviewed |
| Services | `webhook_ingest`, `analytics`, `realtime`, `gmail`, `retry_pending`, `connection`, `threads` | Reviewed |
| AI | `orchestrate`, `analyzer`, `context`, `attention`, `routing`, `token_budget`, `jarvis_agent`, `jarvis_intents`, `jarvis_messages`, `providers/{base,groq,openai}`, `prompts/*` | Reviewed |
| Models | `user`, `message`, `task`, `connection`, `meta_webhook` | Reviewed |
| Frontend core | `package.json`, `next.config.ts`, `tsconfig.json`, `proxy.ts`, `lib/api.ts` | Reviewed |
| Frontend JARVIS | `JarvisAssistant.tsx`, hooks (`useSpeechRecognition`, `useSpeechSynthesis`), `components/jarvis/*` | Reviewed via subagent |
| Frontend pages/components | `app/**`, `components/**` | Reviewed via subagent |
| Tests | `backend/tests/**` (28 files), `**/__tests__/**` (23 files) | Enumerated + sampled |
| Scripts | `backend/scripts/*` (5 files) | Enumerated (not line-audited) |
| Docs | `AGENTS.md`, `CONSTITUTION.md`, `PLAN.md`, `QUICK-START.md`, `BACKEND_EXPLAINED.md`, `docs/`, `specs/`, `history/` | Referenced |
| Excluded | `backend/venv/**`, `node_modules/**`, `.next/**`, lockfiles | Not audited (vendored/metadata) |

---

## 6. Checks Performed

- **Static source review** of ~90 backend + frontend files (full read of security-, data-, AI-, and JARVIS-critical modules).
- **Route inventory:** all FastAPI routers and their auth dependencies inspected.
- **Data-access review:** every Mongo query in scope checked for a `user_id` filter.
- **Secret exposure review:** logging statements scanned for key/secret leakage (found `openai.py` key-prefix log).
- **Config review:** env-var usage, Next.js rewrites, CORS, cookie flags, security headers.
- **Test inventory:** enumerated backend and frontend suites; reviewed `conftest.py` isolation strategy.
- **Git state:** confirmed only pre-existing modification `components/FilterBar.tsx`; no audit-induced changes.

**Not performed (out of scope / no runtime):** dynamic penetration testing, live HTTP fuzzing, dependency CVE scan (`pip-audit`/`npm audit`), bundle-size analysis, load testing, and running the full test suites.

---

## 7. Prioritized Remediation Roadmap

### P0 — Immediate (security/abuse, low effort)
- **SEC-01:** Remove/gate `routes/test.py` + `main.py` registration.
- **SEC-02:** Env-driven `secure=True` cookies in production (set + delete).
- **BUG-01:** Exempt auth endpoints from the global 401 redirect; break the login redirect loop.

### P1 — High (security hardening & correctness)
- **SEC-03:** Migrate token encryption to AES-GCM with lazy re-encrypt migration.
- **ARCH-02:** Remove `openai.py:74` key-prefix log; align provider ABC; retire or fix legacy OpenAI path.
- **PERF-01:** Bound/evict `_CONTEXTS` (LRU/TTL).
- **DATA-01:** Standardize on one canonical event-time field.
- **SEC-05:** Verify webhook verify-before-parse + fail-closed on empty secret; add regression test.
- **BUG-04:** Add mic cleanup on unmount.

### P2 — Medium (robustness, maintainability, defence-in-depth)
- **SEC-04:** Tighten CORS methods/headers; env-drive origins.
- **BUG-02:** Fix cache key/identity + `clearCache` matching; remove dead `ttl`.
- **BUG-03:** Reset JARVIS busy/confirming on close.
- **BUG-05:** Decide analytics gather error semantics.
- **BUG-06:** DB-side task period-scoping.
- **ARCH-01:** Consolidate JARVIS classifiers/matchers.
- **ARCH-04:** Bounded background-analysis queue + drain-on-shutdown.
- **CONF-01/CONF-02:** Central Pydantic settings + `.env.example`.
- **TEST-01:** `skipif`/`xfail` env-gated tests so clean runs are green.
- **CONF-03:** Security headers.
- **SEC-07:** Remove/neutralize `/testdb`.

### P3 — Low (polish)
- **SEC-08:** Verify/rotate secrets; enforce `.gitignore`.
- **ARCH-03:** Document single-worker constraint / distributed lock.
- **ARCH-05, BUG-07..BUG-10, DATA-02, DATA-03, TEST-02, TEST-03, PERF-02..PERF-04, CONF-04:** cleanup, documentation, and observability.

---

## 8. Assumptions & Limitations

- **No runtime execution:** All findings are from static review; "Confirmed" means verified in source, not reproduced at runtime. Items marked **Needs Verification** (SEC-05, DATA-03, TEST-01) require running the suites or deploying to confirm.
- **Vendored code excluded:** `venv/`, `node_modules/` not audited, so dependency-level CVEs are not covered.
- **No CVE scan performed:** `pip-audit`/`npm audit` were intentionally not run (no installs permitted by audit rules).
- **Frontend findings** for JARVIS/app/components were produced by subagent audits with line references; they were not all re-read line-by-line by the primary auditor.
- **Environment note:** `backend/.env` references a MongoDB Atlas URI and multiple secrets; the audit validated *usage*, not live connectivity. No secret values are reproduced in this report.
- **Coverage caveat:** No claim of 100% line coverage of the repository is made; scripts under `backend/scripts/` and some frontend presentational pages were enumerated but not exhaustively read.

---

## 9. Re-Audit — 2026-10-21 (second pass)

**Method:** Each of the 37 findings listed in sections 3 (the executive-summary count of "34" under-counts; the findings section actually contains **37** — 8 SEC + 10 BUG + 4 PERF + 5 ARCH + 3 DATA + 3 TEST + 4 CONF) was individually re-verified against the current source tree by direct file reads and repo-wide greps. No finding was marked fixed on the basis of code "looking different" — every status change cites current file/line evidence. The frontend test suite was executed (see §9.8); the backend suite was **not** executed (see §9.10 limitations).

### 9.1 Summary of changes since the original audit

- `backend/routes/test.py` was **deleted** and its router registration/import removed from `backend/main.py` (SEC-01/BUG-08).
- Session cookies became **env-driven**: `secure=os.getenv("COOKIE_SECURE", "false")` on both set and delete (SEC-02).
- The WhatsApp webhook verifier now **fails closed** on an unconfigured secret, and a regression test pins empty-secret → 403 (SEC-05).
- `lib/api.ts` now **exempts `/auth/login` and `/auth/register`** from the global 401 redirect, in both the cached-GET and main-fetch paths; the login page renders the inline error banner (BUG-01, partial).
- The Groq provider now reads retry/concurrency/timeout knobs from env; the `openai.py` API-key-prefix log line was **removed**; `get_provider()` hard-wires `GroqProvider` (ARCH-02, partial).
- Analytics `_tasks_summary` gained a DB-side `created_at` pre-filter, a 4-field projection, and a single batched `$in` parent-message lookup (BUG-06, partial).
- JARVIS gained task follow-ups, message delete, and read-message phases; all newly inspected mutation paths are user-scoped. The three LLM classifiers were **consolidated in usage** to one `llm_intent` call, with the dispatch order documented in the `process_command` docstring (ARCH-01, partial).
- `backend/tests/conftest.py` now **forces** `DB_NAME=communication_ai_test` before any import/destructive op (TEST-03).
- `realtime.py` documents its single-process constraint in the module docstring (ARCH-03, partial).
- Groq circuit/limiter state remains process-local but is now explicitly documented as intentional (PERF-02).

### 9.2 Status of all original findings

| ID | Title (short) | Status | Evidence (current) |
|----|---------------|--------|--------------------|
| SEC-01 | Test bulk-messages route | **Fixed** | `routes/test.py` deleted; no `test` router in `main.py:13-21,166-175`; repo-wide grep `bulk-messages`/`routes.test` → 0 matches |
| SEC-02 | Cookie `secure=False` | **Fixed** | `routes/auth.py:27` and `:82` read `COOKIE_SECURE` env. *Residual:* default is `false` — production must set `COOKIE_SECURE=true` or the flag is a no-op |
| SEC-03 | Unauthenticated AES-CBC tokens | **Still Open** | `utils/encryption.py:18-46` unchanged: `modes.CBC(iv)`, no MAC/AESGCM/migration |
| SEC-04 | CORS wildcard methods/headers | **Still Open** | `main.py:142-143` still `allow_methods=["*"]`, `allow_headers=["*"]` |
| SEC-05 | Webhook verify-before-parse / fail-closed | **Fixed** | `routes/webhooks.py:29-45` (empty secret → warning + `return False`; `hmac.compare_digest`), `:122-127` signature checked **before** payload parse; regression test `tests/test_webhooks.py:104-120` (secret="" → 403) plus invalid/missing/wrong-secret tests at `:82-100` and `:557` |
| SEC-06 | Dev-only WS `?token=` fallback | **Fixed** (reaffirmed) | `routes/ws.py:46-53,82-89` env-gated; docstring `:10-14` states production stays cookie-only |
| SEC-07 | Unauthenticated `/testdb` | **Still Open** | `main.py:158-163` unchanged |
| SEC-08 | Secrets / `.env` handling | **Fixed** | `.gitignore:34` ignores `.env*`; `git ls-files` shows no env files tracked; `git log --all -- backend/.env` is empty (never committed). *Note:* the `.env*` pattern will also ignore a future `.env.example` — negate it (`!.env.example`) if one is added |
| BUG-01 | Global 401 redirect / login loop | **Partially Fixed** | Banner half fixed: `lib/api.ts:67-74` and `:146-153` exempt `/auth/login` + `/auth/register`; `app/(auth)/login/page.tsx:62-69` renders the inline 401 error. **Loop half remains:** `proxy.ts:27-29` still redirects `/login` → `/dashboard` whenever a `cai_token` cookie is *present* (even expired/invalid), so an expired-but-present cookie still produces `/login → /dashboard → 401 → /login → …` |
| BUG-02 | Cache key ignores identity; `endsWith` invalidation | **Still Open** | `lib/api.ts:27-33` key is still `method:API_BASE+path` only; `:46` redundant `ttl`; `:111-113` `endsWith(path)` over-match; no clear-on-auth-transition found |
| BUG-03 | JARVIS freeze in busy/confirming on close | **Still Open** | `components/jarvis/JarvisAssistant.tsx:224-229` `onClose` bumps `generationRef` and stops mic/TTS but never resets `busy`/`pendingConfirmation`; the `finally` blocks (`:146-148`, `:174-178`) are generation-guarded and are therefore skipped; `:183` blocks the mic while busy and `JarvisPanel.tsx:228` disables send while busy → orb stuck "thinking" until remount |
| BUG-04 | Speech-recognition hook lacks unmount cleanup | **Still Open** | `components/jarvis/hooks/useSpeechRecognition.ts` has only the callback-sync `useEffect` (`:86-89`); no cleanup calls `recognition.stop()/abort()` on unmount |
| BUG-05 | `asyncio.gather` all-or-nothing analytics | **Still Open** | `services/analytics.py:42-48` still no `return_exceptions=True` and no per-pipeline fallback |
| BUG-06 | Tasks period-scoping loads ≤10k docs, filters in Python | **Partially Fixed** | `services/analytics.py:119-139`: Mongo pre-filter on the `created_at` window, 4-field projection, single batched `$in` lookup of parent messages (user-scoped), `ObjectId.is_valid` guard. Residual: final scoping still in Python and the 10 000-doc cap remains; a true DB-side `$lookup`/`$match` was not implemented |
| PERF-01 | Unbounded JARVIS `_CONTEXTS` | **Still Open** | `services/ai/jarvis_agent.py:148-156` still a plain `dict` with insert-on-miss and no TTL/LRU/size cap |
| PERF-02 | Process-local Groq circuit state | **Fixed** (documented) | `providers/groq.py:89-93,104-174` — per-loop primitives and the process-local breaker are now explicitly documented as intentional single-process design; recommendation ("document the constraint") satisfied |
| PERF-03 | Retry tuning masks failures | **Still Open** (accepted by design) | `groq.py:58-60`: attempts/initial delay are env-tunable, but `MAX_RETRY_WAIT` is hard-capped via `min(env, 1.0)` — the cap itself cannot be raised, so the optional "make the cap configurable" recommendation is only half-honoured. The original "no change required" verdict stands |
| ARCH-01 | Layered JARVIS dispatch complexity | **Partially Fixed** | Usage consolidated: only `llm_intent` is called (`jarvis_agent.py:472`, comment "consolidated, single classifier call") and the dispatch order is documented in the `process_command` docstring (`:353-394`). **Residual:** `llm_info_intent` (`jarvis_intents.py:254`) and `llm_message_intent` (`:301`) have **zero call sites** in production code or tests — dead code that the recommendation said to remove was not removed |
| ARCH-02 | Provider interface drift + OpenAI key log | **Partially Fixed** | Key-prefix log **removed** (`openai.py:74` gone; `:91-102` log model/response only); `get_provider()` hard-wires `GroqProvider` (`analyzer.py:22-23`) so the OpenAI path is unreachable. **Residual:** ABC (`providers/base.py:16-21`) still omits `current_message_id` while both concrete providers accept it, and `OpenAIProvider` is still shipped/exported (`providers/__init__.py`) |
| ARCH-03 | Single-process assumptions | **Partially Fixed** | `services/realtime.py:1-14` now documents the single-process registry requirement. **Residual:** `main.py:81-114` Gmail poller + retry sweep would still double-run under multiple workers — no lock and no explicit note in `main.py` |
| ARCH-04 | Fire-and-forget analysis, no backpressure | **Still Open** | `services/webhook_ingest.py:20,156-165` — same module-level `_pending_tasks` set; no bounded queue, concurrency bound, or shutdown drain |
| ARCH-05 | Unused `ai_analysis_collection` | **Still Open** | `database.py:16` unchanged |
| DATA-01 | Dual `created_at`/`received_at` convention | **Still Open** | Ingest sets both equal (`webhook_ingest.py:126-128`), but analytics windows on `received_at` (`analytics.py:63`) while JARVIS counts/sorts on `created_at` (`jarvis_messages.py:172,581,780-782`; `jarvis_agent.py:604`); no invariant test asserting equality was found |
| DATA-02 | Duplicated priority normalization | **Still Open** | Vocabulary still lives in ≥4 places: `analytics.py:24,88` (`PRIORITY_BUCKETS`), `groq.py:382-400` (`VALID_PRIORITIES`/`PRIORITY_ALIASES`), `jarvis_actions.py:89` (`PRIORITY_WORDS`), `jarvis_messages.py:214` (`_PRIORITY_RE`) |
| DATA-03 | No TTL/retention policy | **Still Open** | No TTL indexes in `database.py` or `main.py` lifespan |
| TEST-01 | Env-gated backend tests not skipped | **Still Open** | Grep of `backend/tests/**` for `skipif`/`pytest.mark.skip`/`xfail` → 0 matches; a clean checkout still cannot run green |
| TEST-02 | Frontend tests depend on manual cleanup | **Still Open** | `vitest.config.ts` has no `setupFiles`; global `afterEach(cleanup)` is still not registered |
| TEST-03 | Test-DB isolation guard | **Fixed** | `tests/conftest.py:8` sets `os.environ["DB_NAME"]="communication_ai_test"` **before** `load_dotenv` (which does not override existing vars) and before importing `database`, so destructive fixtures always target the `*_test` DB regardless of `.env`. *Residual:* `MONGO_URI` still resolves from `.env`, so the *cluster* is not guarded — only the DB name is |
| CONF-01 | `/api` proxy vs `NEXT_PUBLIC_API_BASE` drift | **Still Open** | `next.config.ts` still only defines the `/api` rewrite; no build/startup consistency check |
| CONF-02 | Ad-hoc env reads, no central settings | **Still Open** | No `pydantic_settings`/`Settings` class anywhere in `backend/` (grep-verified); env reads remain scattered |
| CONF-03 | No security headers | **Still Open** | `next.config.ts` still only contains `rewrites` — no `headers()`/CSP/HSTS |
| CONF-04 | `mongodb` in frontend dependencies | **Still Open** | `package.json:18` still lists `mongodb`; repo-wide grep found **no** `import`/`require` of `mongodb` in any `.ts/.tsx` — unused dep bloat only |
| BUG-07 | Priority-bucket `to_list(length=100)` cap | **Still Open** (no action needed) | `analytics.py:84` unchanged; informational finding, cap is safe |
| BUG-08 | `test.py` duplicate ingest construction | **No Longer Applicable** | `routes/test.py` deleted with SEC-01 |
| BUG-09 | Silent confidence coercion to 0.5 | **Still Open** | `providers/groq.py:638-640` still coerces with no warning log |
| BUG-10 | Inner imports in `jarvis_agent` | **Still Open** | `jarvis_agent.py:1032` and `:1091` still import inside function bodies |
| PERF-04 | No analytics caching | **Still Open** (Info) | `analytics.py` unchanged; still 5 aggregations per request, no server-side cache |

**Tally: Fixed 7 · Partially Fixed 5 · Still Open 24 · No Longer Applicable 1 · Needs Verification 0** (all former "Needs Verification" items were resolved one way or the other by static evidence; SEC-05 and TEST-03 in particular moved to Fixed).

### 9.3 Issues fixed (evidence recap)

1. **SEC-01** — load-test route deleted; no references remain anywhere in the repo.
2. **SEC-02** — `COOKIE_SECURE` env flag applied to both cookie set and delete paths. *(Action item: set `COOKIE_SECURE=true` in production.)*
3. **SEC-05** — webhook verification fails closed on missing secret, runs before parsing, uses constant-time compare, and is pinned by a dedicated regression test.
4. **SEC-06** — reconfirmed safe; documentation now explicitly states the production constraint.
5. **SEC-08** — `.env` files are git-ignored and provably never committed in this repository's history.
6. **TEST-03** — DB name is hard-forced to `communication_ai_test` before any destructive fixture can run.
7. **PERF-02** — process-local breaker is documented as an intentional single-process design.

### 9.4 Issues partially fixed (what remains)

1. **BUG-01** — login error banner fixed; the **expired-cookie redirect loop** in `proxy.ts:27-29` remains. *Next step:* clear/ignore an invalid `cai_token` in `proxy.ts` before redirecting `/login → /dashboard` (e.g. verify the JWT edge-side, or redirect to `/dashboard` only for non-expired tokens), and/or skip the middleware redirect when the cookie fails validation.
2. **BUG-06** — meaningful DB-side pre-filtering added; full `$lookup` period-scoping and the 10k cap remain. *Next step:* finish the migration with an aggregation `$lookup` or accept and document the current bound.
3. **ARCH-01** — single classifier in use and order documented; delete the two dead `llm_info_intent`/`llm_message_intent` functions (and any tests that only exercise dead code paths).
4. **ARCH-02** — secret log removed and OpenAI path unreachable; align the ABC signature (add `current_message_id`) and either delete or actively retire `OpenAIProvider`.
5. **ARCH-03** — realtime constraint documented; add the same note (or a startup guard against >1 worker) for the Gmail poller and retry sweep in `main.py`.

### 9.5 Issues still open (highest-impact first)

| Priority | ID | Why it still matters |
|----------|----|----------------------|
| **P0** | SEC-03 | Stored Gmail refresh tokens still have no integrity protection (AES-CBC, no AEAD) |
| **P0** | BUG-01 (loop half) | Expired-but-present cookie can still bounce users between `/login` and `/dashboard` |
| **P1** | BUG-03 | Closing JARVIS mid-request permanently freezes the orb/composer until remount |
| **P1** | BUG-04 | Microphone can stay hot after component unmount (privacy) |
| **P1** | PERF-01 | `_CONTEXTS` grows without bound per distinct user |
| **P1** | SEC-04 | Wildcard CORS methods/headers on a cookie-credentialed API |
| **P1** | DATA-01 | `created_at` vs `received_at` divergence still lets JARVIS and analytics disagree about "today" |
| **P2** | BUG-02, BUG-05, BUG-09, BUG-10, SEC-07, ARCH-04, ARCH-05, DATA-02, DATA-03, TEST-01, TEST-02, CONF-01, CONF-02, CONF-03, CONF-04, PERF-03, PERF-04, BUG-07 | Correctness/robustness/maintainability items unchanged from the original roadmap |

### 9.6 Newly discovered issues (this re-audit)

- **NEW-01 — Analytics PeriodToggle test is flaky under full-suite load** · Low · Confirmed (runtime). `app/(dashboard)/analytics/__tests__/page.test.tsx` → "refetches with the new period when the toggle is changed" exceeded the 5 s vitest timeout during the full-suite run (test itself ran ~31 s under parallel load) while the other 4 tests in the file passed; re-running the file in isolation passed **5/5 in 4.5 s**. Impact: full-suite runs report 1 failed / 123 passed, eroding trust in CI. *Next step:* raise the timeout for that test or await the mocked `apiFetch` chain deterministically instead of relying on timing.
- **NEW-02 — Misleading `GROQ_MAX_RETRY_WAIT` env knob** · Info · Confirmed. `providers/groq.py:60` computes `MAX_RETRY_WAIT = min(float(os.getenv("GROQ_MAX_RETRY_WAIT", "1.0")), 1.0)` — setting the env var above 1.0 is silently clamped, so operators who try to make the pipeline more patient get no effect and no warning. *Next step:* drop the hard clamp (or log once when clamping occurs).

**Regressions checked and NOT found:** the newly added JARVIS task-follow-up / delete / read phases were spot-checked for data access and every query/update inspected is `user_id`-scoped (`jarvis_actions.py:537,571-572,598`; `jarvis_agent.py:604-615,628-635,984-1004`). The `openai.py` and `lib/api.ts` changes introduce no new secret exposure or redirect surface beyond the noted residuals. No new unauthenticated routes were found beyond the pre-existing `/testdb` (SEC-07) and `/` `/health` probes.

### 9.7 Updated severity / priority

No original severity was raised. Downgrades are justified only where evidence supports them:

- **SEC-01** High → **resolved** (remove from Top 5).
- **SEC-02** High → **resolved** (conditional on `COOKIE_SECURE=true` in prod; treat as a deployment checklist item).
- **SEC-05** Medium/Needs-Verification → **resolved** (confirmed fail-closed + tested).
- **PERF-02** Low → **resolved-as-documented** (accepted design).
- **BUG-01** stays **High** — half the finding (the loop) is still live.
- Everything else retains its original severity; the P0 slot freed by SEC-01/SEC-02 goes to **SEC-03** and the remaining **BUG-01** loop.

### 9.8 Test execution performed in this re-audit

- **Frontend (`npm test` / vitest):** executed. Result **123 passed, 1 failed** (the NEW-01 flake), 21 test files, ~92 s. Isolated re-run of the failing file: **5 passed** (flake confirmed as load/timing-dependent, not a regression). These numbers are from an actual run, not an assumption.
- **Backend (`pytest`):** **NOT executed.** The re-audit restrictions prohibit modifying databases/external services, and `backend/tests/conftest.py` fixtures perform `delete_many` wipes against the MongoDB Atlas cluster referenced by `backend/.env` — running the suite would modify that (test) database. All backend statuses above are therefore from static verification only.

### 9.9 Remaining recommendations (updated roadmap)

- **P0:** SEC-03 (AES-GCM + lazy re-encrypt migration); BUG-01 remainder (break the `proxy.ts` invalid-cookie loop).
- **P1:** BUG-03 (reset `busy`/`pendingConfirmation` in `onClose`); BUG-04 (unmount cleanup in `useSpeechRecognition`); SEC-04 (env-driven origins; enumerate methods/headers); PERF-01 (TTL/LRU cap on `_CONTEXTS`); DATA-01 (one canonical event-time field + invariant test); ARCH-01 remainder (delete dead classifiers); ARCH-02 remainder (ABC signature + retire OpenAI provider); SEC-02 deployment checklist (`COOKIE_SECURE=true` in prod).
- **P2:** BUG-02 (identity-aware cache key, exact-match invalidation); BUG-05 (`return_exceptions` semantics); BUG-06 remainder; BUG-09 (log on confidence coercion); BUG-10 (hoist imports); SEC-07 (drop `/testdb`); ARCH-04 (bounded analysis queue + drain); ARCH-05 (delete dead collection handle); DATA-02 (single priority constant); DATA-03 (retention plan); TEST-01 (`skipif` on env-gated tests); TEST-02 (vitest `setupFiles` with `afterEach(cleanup)`); CONF-02 (Pydantic `Settings`); CONF-03 (security headers); CONF-01/CONF-04 (config/dep hygiene).
- **P3:** PERF-03/PERF-04, BUG-07, NEW-01 (deflake), NEW-02 (clamp visibility).

### 9.10 Re-audit coverage & limitations

- **Re-read in full or in relevant part:** `main.py`, `database.py`, `routes/{auth,webhooks,ws,test-deleted}.py`, `utils/encryption.py`, `services/{analytics,webhook_ingest,realtime}.py`, `services/ai/{jarvis_agent,jarvis_intents,jarvis_messages,jarvis_actions,analyzer,orchestrate}.py` (targeted sections), `services/ai/providers/{base,groq,openai}.py` (targeted sections), `tests/conftest.py`, `lib/api.ts`, `proxy.ts`, `next.config.ts`, `vitest.config.ts`, `package.json`, `.gitignore`, `components/jarvis/JarvisAssistant.tsx`, `components/jarvis/hooks/useSpeechRecognition.ts`, `app/(auth)/login/page.tsx`; repo-wide greps for every finding's signature patterns.
- **Limitations:** backend test suite not run (DB-modification restriction, §9.8); no runtime reproduction of the cookie/redirect loop or the JARVIS freeze (static call-flow evidence only); no dependency CVE scan; no line-by-line re-audit of unchanged files (files not named in any finding were not re-opened unless a grep implicated them); the encryption migration path (SEC-03) remains unimplemented and therefore untested; `.env` values were never opened — secret *usage* patterns only. Git history inspection covered tracked-file presence (`git ls-files`) and the `backend/.env` path only — a broader history-wide secret sweep was not performed.
- **Regression scope:** changed-area review focused on the fixes listed in §9.1 plus the newer JARVIS phases; older, untouched modules were trusted to their original audit state.

*End of report.*
