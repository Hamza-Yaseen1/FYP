# Implementation Plan: Day 26 Gmail Integration

**Branch**: `017-gmail-integration` | **Date**: 2026-09-10 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/017-gmail-integration/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Connect a user's Gmail account via Google's official OAuth 2.0 flow (no
passwords), store access/refresh tokens encrypted on the backend, then
automatically detect new emails and feed them through the existing
normalized ingest + AI pipeline so they appear on the dashboard alongside
WhatsApp messages. Connection status is shown and managed on the Connections
page; each connection is strictly user-owned.

Technical approach (from research):
- Direct REST against Google endpoints (`accounts.google.com`,
  `oauth2.googleapis.com`, `gmail.googleapis.com`) using `httpx` + stdlib
  `email`/`base64` for MIME parsing — no heavyweight Google SDK.
- Reuses the existing AES-256 encryption utility (`utils/encryption.py`),
  the `connections` collection (provider enum already includes `gmail`),
  and the canonical `services/webhook_ingest.py::ingest_message` path.
- A lightweight asyncio poller started in the FastAPI lifespan detects new
  emails every ~30s and triggers the AI pipeline on each.

## Technical Context

**Language/Version**: Python 3.13 (backend), TypeScript 5.x (frontend)
**Primary Dependencies**: FastAPI, Motor, Pydantic, `httpx` (NEW runtime dep; already present for tests), `cryptography` (already used), PyJWT (already used)
**Storage**: MongoDB — `connections` (extended) and `messages` (additive `subject`)
**Testing**: pytest + FastAPI TestClient (backend, existing pattern), Vitest/Testing Library (frontend, subject-line render only)
**Target Platform**: Web (browser) — Next.js frontend + FastAPI backend on localhost
**Project Type**: web (frontend + backend monorepo)
**Performance Goals**: A new email is reflected on the dashboard within 5 minutes (default poll ~30s); OAuth connect flow completes in under 2 minutes (human-paced)
**Constraints**: Gmail read-only scope (`gmail.readonly`) only; tokens encrypted at rest; zero token exposure to frontend; per-user isolation with 404 semantics; no outbound email
**Scale/Scope**: FYP — one Gmail connection per user, ≤ 20 connected mailboxes, single uvicorn process

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Gates derived from the Day 26 constitution section (v1.14.0) plus Days 18/19/23 rules:

1. **OAuth only, no passwords** — The design uses Google OAuth 2.0 only. No
   password field exists anywhere. ✅
2. **Minimal scope** — Auth request includes only
   `https://www.googleapis.com/auth/gmail.readonly`. ✅
3. **Encrypted at rest** — Access + refresh tokens encrypted with AES-256-CBC
   via the existing `encrypt()` utility before MongoDB storage. ✅
4. **Never exposed to frontend** — New/updated endpoints return only
   `{provider, status, created_at}` (+ optional display email); tokens stay
   backend-only. ✅
5. **Server-side ownership** — `user_id` derived from the JWT session
   (`get_current_user`) at auth-url time and carried in a signed short-lived
   OAuth state for the callback; never from client input. ✅
6. **Normalized message format** — Emails funnel through
   `ingest_message(source="gmail", ...)`; AI pipeline/dashboard never see
   Gmail payloads. Additive optional `subject` field per constitution. ✅
7. **Idempotence** — Existing unique partial index on
   `messages.external_message_id` + `DuplicateKeyError` handling in
   `ingest_message`. ✅
8. **Revoke on disconnect** — `DELETE /connections/{id}` extended to revoke
   the Google token before deleting the document. ✅
9. **Receive-only** — No `gmail.send`/`gmail.modify`; read-only scope
   enforced at consent and never used to mutate the mailbox. ✅
10. **User isolation** — All connection queries filter by `user_id` first;
    cross-user access returns 404 identical to not-found. ✅
11. **Progressive enhancement** — Email fetch failures leave existing
    messages untouched; per-user errors never block other users or ingestion. ✅
12. **Simplicity First** — Direct REST + stdlib MIME parsing instead of the
    full Google SDK; one poller, no queues, no new frameworks. ✅

No gate failures. Complexity Tracking below documents the one new runtime
component (poller) and the deliberate choice to use direct REST.

## Project Structure

### Documentation (this feature)

```text
specs/017-gmail-integration/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
│   └── gmail-oauth-api.md
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
backend/
├── main.py                        # lifespan: start poller task (create/cancel)
├── .env.example                   # + GOOGLE_CLIENT_ID/SECRET/REDIRECT_URI, FRONTEND_URL, GMAIL_POLL_INTERVAL_SECONDS
├── requirements.txt               # + httpx (runtime)
├── models/
│   └── connection.py              # + token_expires_at, last_fetched_at, gmail_email (optional)
├── routes/
│   ├── connections.py             # guard: reject POST for gmail (must use OAuth flow)
│   └── gmail.py                   # NEW: GET /connections/gmail/auth-url, GET /connections/gmail/callback
├── services/
│   ├── connection.py              # delete_connection revokes Google token for gmail; service reads/writes new fields
│   ├── gmail.py                   # NEW: OAuth URL builder, state sign/verify, token exchange/refresh/revoke, GmailClient (list/get), normalize_email
│   └── webhook_ingest.py          # ingest_message: + subject param; spawn asyncio task when no BackgroundTasks
└── tests/
    ├── test_gmail_oauth.py        # NEW: unit — URL/state/exchange/refresh/revoke/normalize
    └── test_gmail_integration.py  # NEW: integration — connect flow, delete revoke, poller ingest + dedup, isolation

frontend/
├── app/(dashboard)/
│   ├── connections/page.tsx       # read ?gmail=connected|error search param → banner
│   └── inbox/page.tsx             # Message.card: optional subject line; Message.subject?
├── components/connections/
│   └── ConnectionCard.tsx         # gmail Connect → fetch auth_url → window.location.assign
└── lib/api/connections.ts         # + getGmailAuthUrl()
```

**Structure Decision**: Follows the existing web monorepo layout (`backend/` +
`frontend/`). Gmail logic lives in a new `services/gmail.py` and a new
`routes/gmail.py` so the generic `connections` router stays provider-agnostic;
the poller is started in `main.py`'s existing lifespan (no new service/deploy
unit).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Background asyncio poller (new long-lived component) | Gmail has no webhook within scope; FR-005 requires automatic detection ≤ 5 min | Manual/button-triggered fetch fails "without any further action from the user"; APScheduler/Celery add dependencies and deploy complexity a single uvicorn process doesn't need |
| Direct REST instead of `google-api-python-client` | Constitution allows "official client OR direct REST API calls"; we only need list/get + OAuth endpoints | Google SDK pulls a large dependency tree and makes httpx-based test mocking harder; stdlib `email` MIME parsing is small and well-tested |

## Phase 0 (Research)

All unknowns resolved — see [research.md](research.md). Key decisions:
- Direct REST over Google endpoints with `httpx` (+ add `httpx` to runtime deps).
- OAuth `state` = short-lived signed JWT (PyJWT, JWT_SECRET) binding `user_id`.
- New-email detection via date-based Gmail query (`after:<epoch>`) tracked by
  a `last_fetched_at` field — read-only compatible (we cannot mark-as-read with
  a read-only scope, and dedup alone would re-scan unread mail forever).
- Poller started in `main.py` lifespan; `ingest_message` extended to spawn
  `asyncio.create_task(_analyze_and_store, ...)` when no `BackgroundTasks`.

## Phase 1 (Design)

- [data-model.md](data-model.md) — additive fields on `connections` and
  `messages`; state transitions; the `subject` ingest extension.
- [contracts/gmail-oauth-api.md](contracts/gmail-oauth-api.md) — endpoint
  contracts, request/response shapes, env-var table.
- [quickstart.md](quickstart.md) — manual Google Cloud setup + test runbook.
- Agent context updated via `update-agent-context.ps1 -AgentType opencode`.

Constitution Check re-run after design: still all pass (see above).