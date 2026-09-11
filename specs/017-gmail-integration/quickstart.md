# Quickstart: Gmail Integration (Day 26)

**Feature**: 017-gmail-integration | **Date**: 2026-09-10 | **Phase**: 1

Runbook to stand up the Google side of the integration, wire env vars, and
verify end-to-end. The app itself is unchanged until the feature is
implemented.

## Prerequisites

- Backend running (`uvicorn main:app --reload` in `backend/`, port 8000), Mongo connected.
- Frontend running (`npm run dev`, port 3000).
- A Google account to connect (the demo mailbox).

## Step 1 — Google Cloud OAuth client (manual, one-time, ~5 min)

1. Go to https://console.cloud.google.com/ → select or create a project
   (e.g. "Communication AI").
2. **APIs & Services → Enabled APIs and services → Enable**:
   `Gmail API`.
3. **APIs & Services → OAuth consent screen**:
   - User type: **External** (Test mode is fine for FYP).
   - App name: `Communication AI FYP`.
   - Add your test Google account to **Test users**.
   - **Add or remove scopes** → **Manually add scopes**:
     `https://www.googleapis.com/auth/gmail.readonly` → Save.
4. **APIs & Services → Credentials → Create credentials → OAuth client ID**:
   - Application type: **Web application**.
   - **Authorized JavaScript origins**: (leave empty).
   - **Authorized redirect URIs**:
     `http://localhost:8000/auth/google/callback`
   - Create. Copy the **Client ID** and **Client secret**.

> If the redirect URI differs from `GOOGLE_REDIRECT_URI` by even one
> character/slash, Google returns `redirect_uri_mismatch` — check this first
> when debugging the callback.

## Step 2 — Backend env vars

Open `backend/.env` and add:

```env
GOOGLE_CLIENT_ID=<client-id>
GOOGLE_CLIENT_SECRET=<client-secret>
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
FRONTEND_URL=http://localhost:3000
GMAIL_POLL_INTERVAL_SECONDS=30
```

Restart the backend so uvicorn picks them up (they're read at startup).

## Step 3 — Connect

1. Log in on the frontend (existing account).
2. **Connections → Gmail → Connect**.
3. Google consent screen appears (Test mode: pick any test user). Approve.
4. Browser redirects back: endpoint reads `?state=` (session-protected
   handshake) → exchanges the code → stores the encrypted tokens → redirects
   to `http://localhost:3000/connections?gmail=connected` with a success
   banner. Card now shows **Connected** for Gmail.

## Step 4 — Verify

- **Receive**: send an email to the connected mailbox → within ≤ 5 min the
  Inbox page shows it with `source: gmail` and (if the email has a subject)
  the subject line.
- **AI**: the message gets `ai_analysis` (routing etc.) like any other
  message — check MongoDB or the message detail.
- **Dedup**: send another mail while polling; no duplicate rows, no duplicate
  AI runs.
- **Disconnect**: **Connections → Gmail → Disconnect** → the Google token is
  revoked and polling for that user stops.
- **Quota sanity**: connect a second user; each user must only see their own
  connection and messages (log in as user B and confirm no cross-read).

## Debugging

| Symptom | Likely cause | Check |
|---|---|---|
| `redirect_uri_mismatch` on connect | Google Cloud redirect URI ≠ `GOOGLE_REDIRECT_URI` | Step 1.4 vs `backend/.env` |
| Backend logs `invalid_grant` during poll | User revoked the app / refresh token expired | Re-connect; connection flips to `error` |
| No emails appear | Poll interval, watermark, or wrong account | `GMAIL_POLL_INTERVAL_SECONDS`; `last_fetched_at` in Mongo; tokeninfo email |
| `400 Use the Gmail connect flow` | Frontend still calls `POST /connections` for gmail | Use auth-url flow (Step 3) |
| Callback shows `?gmail=error` after grant | Code exchange failed / `refresh_token` missing | Server logs at callback; consent screen must have been shown once (`prompt=consent`) |

## What is deliberately NOT here

- No sending, no replies, no read/unread toggling (read-only scope).
- No attachments — body-part non-text content is ignored.
- No backfill of historical mail (only `after: last_fetched_at`).