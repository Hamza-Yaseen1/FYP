# Contracts: Gmail OAuth & Polling API

**Feature**: 017-gmail-integration | **Date**: 2026-09-10 | **Phase**: 1

Base URL: `http://localhost:8000` (dev). Auth: existing cookie JWT
(`get_current_user`) unless noted. All bodies `application/json`.

## 1. GET /connections/gmail/auth-url

Returns the Google authorization URL for the authenticated user. Requires the
session cookie. No tokens are exposed.

**Auth**: required (JWT → `user_id`)

**Request**: none (query params optional/must-be-ignored; not used for state)

**Response `200 OK`**:
```json
{ "auth_url": "https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id=…&redirect_uri=…&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fgmail.readonly&access_type=offline&prompt=consent&state=<signed-jwt>" }
```

**Errors**:
- `401` (not authenticated) — `{"detail": "Not authenticated"}`

**State JWT** (value of top-level `state` query param inside `auth_url`):
- Header/algorithm: HS256 (PyJWT).
- Claims: `{ "sub": "<user_id>", "purpose": "gmail_oauth", "jti": "<uuid4>", "exp": "<now+600s>" }`.
- Signed with `JWT_SECRET`. Verified by the callback; unchanged parameters ⇒
  a user's own completed OAuth cannot be replayed against another user.

## 2. GET /auth/google/callback  (Google OAuth redirect target)

The Google Authorized redirect URI configured in Cloud Console must match
`GOOGLE_REDIRECT_URI` in `backend/.env` exactly. In this deployment:
`http://localhost:8000/auth/google/callback`. The legacy alias
`GET /connections/gmail/callback` delegates to the same handler — both are
registered and interchangeable.

Not cookie-authenticated — identity comes from `state`. Google redirects the
browser here after the consent screen.

**Query params (from Google)**:
- `code` (string) — authorization code (one-time).
- `state` (string) — the signed JWT from 1.
- `error` (string, sometimes) — e.g. `access_denied` on user cancel.

**1. Verify state**: decode + verify HS256 (`JWT_SECRET`); check
`purpose == "gmail_oauth"` and `exp`. Failure ⇒ log warning, `302 → FRONTEND_URL/connections?gmail=error`.

**2. If `error` present**: log, `302 → FRONTEND_URL/connections?gmail=error`.

**3. Exchange code** at `https://oauth2.googleapis.com/token`:
```
POST  (application/x-www-form-urlencoded)
  code, client_id, client_secret, redirect_uri,
  grant_type=authorization_code
```
Success body: `{ access_token, token_type, expires_in, refresh_token, scope }`.
`refresh_token` REQUIRED (we always send `access_type=offline&prompt=consent`);
missing ⇒ status `error`, `302 → …?gmail=error`.

**4. Persist connection** (upsert `{user_id, provider:"gmail"}`):
- `access_token = encrypt(...)`, `refresh_token = encrypt(...)`,
  `token_expires_at = now + expires_in − 60s`, `status = "connected"`.
- `gmail_email`: best-effort `GET https://oauth2.googleapis.com/tokeninfo?access_token=…`
  → `email` (failure ⇒ `None`, still connected).

**5. Respond**: `302 → FRONTEND_URL/connections?gmail=connected`

**Errors** (non-redirectable):
- Invalid/nonexistent `code` or network failure on exchange ⇒ status
  `error`, `302 → …?gmail=error`. Minimum-viable: the browser always ends on
  the Connections page with a banner; details logged server-side.

## 3. DELETE /connections/{id}  (extended: revoke for gmail)

Existing `204` behavior for WhatsApp; extended so that when the target
connection is `provider: "gmail"`:

1. Load connection WITH tokens (user-scoped; not found ⇒ `404`).
2. `POST https://oauth2.googleapis.com/revoke` with `token=refresh_token` —
   best effort; log if it fails (400/network).
3. Delete the connection document.
4. `204 No Content`.

`404` for unknown id OR another user's id (identical message — isolation).

## 4. Ingest — internal contract extension

Not an HTTP endpoint; `ingest_message(user_id, source, sender, content,
external_message_id=None, message_type="text", background_tasks=None,
subject=None) -> str`:
- `subject` stored as `doc["subject"]` when provided (optional, additive).
- When `background_tasks is None` and message was newly inserted, the
  function spawns `asyncio.create_task(_analyze_and_store(...))` (task ref
  kept in a module-level set). Request-handler callers that pass
  `BackgroundTasks` behave exactly as today.
- Duplicate `external_message_id` ⇒ existing id returned; no re-analysis.

## 5. Poller — internal runtime contract

`poll_connected_gmail()` (in `services/gmail.py`), iterated by an
`asyncio` loop started in `main.py` lifespan:
1. `connections.find({"provider":"gmail","status":"connected"})`.
2. Per connection: passwordlessly load + `decrypt()` tokens only in memory;
   `ensure_access_token()` (refresh when `token_expires_at` past/missing or
   Gmail 401; `invalid_grant` ⇒ `status = error`, skip).
3. Refs/watermark: `start_epoch = last_fetched_at − 1h if missing else last_fetched_at`.
4. `GET gmail.googleapis.com/gmail/v1/users/me/messages?q=after:<epoch>&maxResults=20`.
5. Per returned id: `GET …/messages/<id>?format=raw` → `normalize_email()` →
   `ingest_message(source="gmail", …)` (dedup via unique index).
6. After success: `last_fetched_at = now` (write-back guarded per user — a
   user error never blocks others).
7. Loop sleeps `GMAIL_POLL_INTERVAL_SECONDS` (default `30`).

## 6. Environment variables

| Var | Required | Example | Notes |
|---|---|---|---|
| `GOOGLE_CLIENT_ID` | yes (gmail) | `123-abc.apps.googleusercontent.com` | OAuth web client |
| `GOOGLE_CLIENT_SECRET` | yes (gmail) | `GOCSPX-…` | OAuth web client secret |
| `GOOGLE_REDIRECT_URI` | yes (gmail) | `http://localhost:8000/auth/google/callback` | Must match Google Cloud Authorized redirect URI exactly |
| `FRONTEND_URL` | yes (gmail) | `http://localhost:3000` | Post-connect redirect target |
| `GMAIL_POLL_INTERVAL_SECONDS` | no | `30` | Poll loop interval; default 30 |

Reused: `ENCRYPTION_KEY`, `JWT_SECRET`, `MONGO_URI`, `FRONTEND_URL`. No new
CORS scope — `FRONTEND_URL` (localhost:3000) is already allowed.

## 7. Frontend calls

- `lib/api/connections.ts`: `getGmailAuthUrl(): Promise<string>` →
  `GET /connections/gmail/auth-url` (apiFetch) → `res.auth_url`; caller does
  `window.location.assign(auth_url)`.
- `ConnectionCard` (gmail): click "Connect" → disable button ("Redirecting to
  Google…") → fetch auth URL → assign. WhatsApp path untouched.
- `connections/page.tsx`: read `useSearchParams()`;
  `?gmail=connected` ⇒ success banner; `?gmail=error` ⇒ error banner; banner
  cleared on navigation. Inbox: render `subject` line only when present.