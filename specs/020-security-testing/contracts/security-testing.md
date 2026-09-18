# Contracts: Security & Reliability Verification Surface (Day 29)

**Feature**: `020-security-testing` | **Date**: 2026-09-11

Day 29 introduces **no new public API endpoints and no request/response schema
changes**. This file documents (a) the existing endpoints the verification
suites exercise and the assertions each carries, and (b) the contract of the one
new internal function, `retry_pending_analyses()`.

## 1. Public endpoints under verification (no schema change)

| Endpoint | Auth | Asserted contract |
|---|---|---|
| `GET /messages` (+ `/counts`, `/senders`, `/sources`) | JWT cookie | lists only `{user_id}` docs; cross-user ids absent |
| `GET /messages/{id}` | JWT cookie | 404 (identical body) if other-user or non-existent |
| `PUT/DELETE /messages/{id}`, `PUT /messages/{id}/priority` | JWT cookie | 404 + no mutation of other-user docs |
| `POST /messages` | JWT cookie | 201 for owner; `user_id` from JWT, body claims ignored |
| `GET /tasks`, `PUT/DELETE /tasks/{id}/...` | JWT cookie | user-scoped; 404 for not-yours |
| `GET /connections`, `GET/DELETE /connections/{id}` | JWT cookie | user-scoped; 404 for not-yours |
| `GET /analytics?period=...` | JWT cookie | `user_id` is first `$match`; 401 unauthenticated |
| `POST /webhooks/whatsapp` | **signature only** (public by design) | 403 invalid/missing signature, 400 malformed body, 200 valid+well-formed |
| `GET /webhooks/whatsapp` | verify token (query) | 200 challenge echo on match; 403 on mismatch |
| `POST /webhooks/simulate` | JWT cookie | 200 only authenticated; owner from JWT |
| `GET /auth/me`, `/auth/register`, `/auth/login`, `/auth/logout` | mixed | existing auth contract (untouched) |

**404-indistinguishability contract**: for every user-owned resource, the
response to `GET /other_user's_id` MUST be byte-identical to `GET /random_valid_oid`
— same status, same body; existence is never revealed.

## 2. Webhook boundary contract

```
POST /webhooks/whatsapp (raw body)
  ├─ signature absent / invalid / no WHATSAPP_APP_SECRET configured → 403, nothing stored
  ├─ signature valid but JSON malformed / fails Pydantic → 400, nothing stored
  └─ signature valid + structurally valid → normalize → resolve owner (server-side) → ingest → 200
```
- Owner is resolved from connected-connection state (`provider: whatsapp,
  status: connected`), NEVER from payload fields.
- **Accepted limitation (FYP)**: single WABA deployment — the first connected
  WhatsApp connection owns inbound traffic. Multi-number/multi-user routing is
  out of scope and would require an explicit amendment.

## 3. Dedupe contract

- Key: `{user_id, external_message_id}` — a unique index is the final authority
  (race-safe); the app-layer check prevents re-analysis.
- Delivery of the same key twice (webhook redelivery, Gmail poll overlap,
  AI-retry) → one document; second delivery acknowledged, existing id returned,
  `process_message` NOT re-invoked.
- Key-less messages (`simulate`, manual `POST /messages`) are **explicitly
  exempt** — documented exemption per constitution Day 29 rule 5.
- Two users may independently hold the same provider id value; each gets its own
  document under its own `user_id`.

## 4. Internal retry contract — `retry_pending_analyses()`

```python
# backend/services/retry_pending.py
async def retry_pending_analyses(limit: int = 50) -> int:
    """Re-run the AI pipeline for stored messages whose analysis is pending.

    Returns the number of messages retried. Never creates a document.
    """
```

- Selector: `{"ai_analysis.status": "pending"}` (user-scoped; per-message
  `update_one` includes `user_id`).
- For each: `analysis = await process_message(content, message_id=..., user_id=...,
  thread_id=...)` — the Orchestrator single entry point (NEVER `analyze_message`),
  then `update_one({"_id": ..., "user_id": ...}, {"$set": {"ai_analysis": analysis}})`.
- Guarded end-to-end: exceptions are caught and logged per message; a failing
  retry leaves the document `pending` and never raises into the sweep loop or the
  request path.
- Idempotent: retrying updates the same document via `_id` + `user_id`; document
  count is invariant.
- Deployment: a rate-bounded `asyncio` loop in `main.py` lifespan runs it on an
  interval (`RETRY_INTERVAL_SECONDS`, default 60), skipped when
  `DB_NAME == "communication_ai_test"` (test DB) so suites call the function
  directly.
- Failure semantics: pending remains explicit (observable degradation); a quiet
  drop is a failure.