# Research: Day 26 Gmail Integration

**Feature**: 017-gmail-integration | **Date**: 2026-09-10 | **Phase**: 0

Purpose: resolve the technical unknowns for the Day 26 plan. All decisions
here are grounded in the existing backend (FastAPI + Motor + PyJWT +
`utils/encryption.py`), the Day 26 constitution section (v1.14.0), and the
feature spec.

## 1. Google OAuth 2.0 — flow & server-side exchange

**Decision**: Implement the standard OAuth 2.0 "authorization code with
PKCE-optional, `access_type=offline`" flow using direct HTTPS calls to
Google's documented endpoints. No SDK.

**Rationale**:
- The constitution explicitly permits "direct REST API calls to the Gmail
  API" as an alternative to the official client.
- The flow we need is only four manual HTTPS operations:
  1. Build the authorization URL (`https://accounts.google.com/o/oauth2/v2/auth`)
  2. Exchange the code (`https://oauth2.googleapis.com/token`,
     `grant_type=authorization_code`)
  3. Refresh (`grant_type=refresh_token`)
  4. Revoke (`https://oauth2.googleapis.com/revoke`)
  plus the Gmail API (`gmail.googleapis.com/gmail/v1/users/me/...`).
- Tests can monkeypatch a thin `httpx.AsyncClient` seam; `google-api-python-client` builds a large dependency tree and its own transport that is awkward to mock with the existing `monkeypatch` test style.

**Alternatives considered**:
- `google-api-python-client` + `google-auth-oauthlib`: official, robust, but
  heavy; rejected for FYP simplicity and testability (see Complexity
  Tracking in plan.md).
- `google-auth` only (token lib): still a dependency; the token endpoint
  calls are trivial to do directly with `httpx`.
- Client-side PKCE (`S256`): adds robustness but complicates a stateful
  multi-request flow; for a localhost FYP the signed-state approach (below)
  is sufficient. Will keep `response_type=code&access_type=offline&prompt=consent`.

**Key parameters**:

| Param | Value | Why |
|---|---|---|
| `scope` | `https://www.googleapis.com/auth/gmail.readonly` | Constitution: read-only only; no send/modify |
| `response_type` | `code` | Authorization-code flow |
| `access_type` | `offline` | Required to get a refresh token |
| `prompt` | `consent` | Forces the consent screen on reconnect so a fresh refresh token is always issued |
| `state` | signed short-lived JWT | Binds the callback to the logged-in user; CSRF protection |

## 2. OAuth `state` — identity + CSRF without extra storage

**Decision**: `state` = a JWT (PyJWT, signed with the existing `JWT_SECRET`)
with claims `{sub: <user_id>, purpose: "gmail_oauth", jti: <uuid4>, exp:
now+10min}`. The callback decodes it, checks `purpose`, and uses `sub` as the
owner.

**Rationale**:
- The callback arrives from the user's browser after the Google redirect; the
  session cookie is normally still present, but relying on `state` alone is
  stateless and does not depend on cookie transport quirks across the OAuth
  round trip.
- Signing prevents an attacker from minting a state for another user
  (CSRF/account-takeover guard). No DB/memory store to expire or clean.
- Reuses `JWT_SECRET` + PyJWT already in the codebase.

**Alternatives considered**:
- Server-side `{state → user_id}` map in memory or MongoDB: needs expiry
  cleanup and breaks after server restarts; rejected.
- Plain base64 `user_id` as state: forgeable; rejected.

## 3. Token handling & refresh

**Decision**: On exchange, store `encrypt(access_token)`,
`encrypt(refresh_token)`, `token_expires_at = now + expires_in - 60s`
(reuse `utils/encryption.py` AES-256-CBC, key from `ENCRYPTION_KEY`). A
single `ensure_access_token(connection)` helper refreshes when
`token_expires_at` is missing/past or the Gmail API returns 401, re-encrypts,
and persists. On `invalid_grant` during refresh or an API 401-after-refresh,
flip the connection to `status=error`.

**Rationale**:
- Google access tokens expire in ~1h; the stored `expires_in` lets us refresh
  proactively (no per-call tokeninfo lookup).
- The 60s skew avoids clock races at the expiry boundary.
- `invalid_grant` == the user revoked the app or the refresh token is dead →
  surface an error status and require re-connect (spec edge case).

## 4. Detecting new emails — date-based query (read-only safe)

**Decision**: Poll `users.messages.list` with `q=after:<unix_epoch>` where
epoch comes from a stored `last_fetched_at` on the connection (default:
connection time minus 1h on first poll). No `is:unread` filter. After a
successful poll, update `last_fetched_at = now`.

**Rationale**:
- We hold read-only scope and MUST NOT mark-as-read (`gmail.modify` would be a
  constitution violation). A pure `q=is:unread` query would re-return the same
  unread emails forever — dedup would suppress duplicates but every poll would
  still re-download and re-scan them, wasting quota and risking rate limits.
- `after:` filters by internal date, is read-compatible, and naturally gives
  us "emails since last poll". `external_message_id` dedup still protects
  against overlap/retries.
- Gmail `list` returns up to `maxResults=20` by default; we cap at 20 and the
  next poll picks up the rest — bounded work per cycle, no pagination loop.

**Alternatives considered**:
- Google Pub/Sub push notifications: official, but requires a Google Cloud
  Pub/Sub topic + subscription + a public push endpoint + credentials —
  heavy and asynchronous for a single uvicorn FYP. Rejected.
- `is:unread` + mark-read: violates read-only constitution rule. Rejected.

## 5. Poller runtime — asyncio task in the lifespan

**Decision**: Start a single `asyncio` loop task in `main.py`'s existing
`lifespan`:
`while True: await poll_connected_gmail(); await asyncio.sleep(interval)`.
`interval = int(os.getenv("GMAIL_POLL_INTERVAL_SECONDS", 30))`. Cancel the
task on shutdown. Each user's connection error is isolated per user.

**Rationale**:
- Matches the FastAPI + Motor async stack; no new deploy unit, no Celery, no
  external scheduler (Constitution Principle I).
- Default 30s comfortably meets the ≤ 5-minute success criterion while staying
  under Gmail quotas (~1000 requests/100s/user; we make ~2 requests per user
  per poll).
- The poller is kept behind an env-guard-friendly seam so tests can call
  `poll_connected_gmail()` directly (or monkeypatch the fetch path) without
  running the loop.

**Alternatives considered**:
- `BackgroundTasks` per poll: lifespan-bound by design, not reusable. Rejected.
- APScheduler/`schedule`: extra dependency + thread-per-scheduler. Rejected.

## 6. AI analysis after ingestion — extending `ingest_message`

**Decision**: `ingest_message` gains an optional `subject: Optional[str] = None`
param (stored as `doc["subject"]`, additive) and, when `background_tasks` is
`None` (i.e., not called from a request handler), spawns
`asyncio.create_task(_analyze_and_store(...))` itself, keeping a
module-level `set()` of task refs to prevent GC. Webhook/simulate callers that
pass a `BackgroundTasks` keep today's exact behavior.

**Rationale**:
- The Gmail poller runs outside a request, so there is no `BackgroundTasks`
  to attach to. Without this change, poller-ingested messages would be stored
  but never AI-analyzed (spec FR-007).
- Existing calls (`POST /webhooks/simulate`, `POST /webhooks/whatsapp`) are
  untouched — the `background_tasks` branch is preserved.
- `_analyze_and_store` already guards its own exceptions and never blocks
  ingestion (Progressive Enhancement).

## 7. Gmail → normalized message mapping

**Decision**: `normalize_email(raw_message: dict) -> dict` maps the Gmail API
`email`-parsed message to the canonical fields, and the poller hands them to
`ingest_message` (not the raw payload):

| Canonical field | From Gmail | Notes |
|---|---|---|
| `source` | constant `"gmail"` | enum value |
| `sender` | `From` header name, else address | `"Name <addr>"` → `"Name"`; fallback bare address |
| `content` | `text/plain` body part; else HTML stripped via stdlib `email` TextHandler semantics; else `""` | empty → `""`, never null, never dropped |
| `subject` | `Subject` header | optional, may be `"" ` |
| `external_message_id` | `messages.get(...).id` | dedup key |
| `received_at` | `Date` header → UTC; on parse failure server-now | constitution: server time on detection is the source of truth; header is best-effort |

Parsing: `email.message_from_bytes(base64.urlsafe_b64decode(payload.raw))`
(stdlib). Attachments ignored (body parts with `Content-Disposition:
attachment` skipped).

**Rationale**: Reuses the existing canonical `messages` document + unique
`external_message_id` index; the AI pipeline and dashboard remain
channel-agnostic (spec FR-005/FR-008, Day 23 normalization contract).

## 8. Env vars (new)

| Var | Example | Notes |
|---|---|---|
| `GOOGLE_CLIENT_ID` | `123...apps.googleusercontent.com` | OAuth web client |
| `GOOGLE_CLIENT_SECRET` | `GOCSPX-...` | OAuth web client secret; never exposed to frontend |
| `GOOGLE_REDIRECT_URI` | `http://localhost:8000/connections/gmail/callback` | MUST match the Authorized redirect URI in Google Cloud |
| `FRONTEND_URL` | `http://localhost:3000` | Where the callback redirects the browser after connect |
| `GMAIL_POLL_INTERVAL_SECONDS` | `30` | Poll loop interval (default 30) |

Existing deps reused: `ENCRYPTION_KEY` (AES), `JWT_SECRET` (state/session),
`MONGO_URI`. New runtime dep: `httpx` (already a dev/test dep — promote to the
main requirements list).

## 9. Risk register

| Risk | Mitigation |
|---|---|
| OAuth client misconfiguration (mismatched redirect URI) | Documented manual setup in quickstart.md; env-driven; clear 400 on callback mismatch |
| Refresh token never issued (first-time flow without `prompt=consent`) | `prompt=consent` always sent; callback fails loudly if `refresh_token` absent |
| Token revoked in Google settings | `invalid_grant` → `status=error` + re-connect prompt (spec edge case) |
| Poller floods rate limits | 30s interval + 20-message cap + per-user backoff on non-auth errors |
| Query overlap re-fetch | unique `external_message_id` index → skips duplicates, no second AI run |
| Server restart drops poller | reparsed from `last_fetched_at` (persisted) — no email lost, no duplicate |
| Callback state tampering/forgery | signed JWT state with `purpose` + short expiry |