# Research: Security & Reliability Verification (Day 29)

**Feature**: `020-security-testing` | **Date**: 2026-09-11

Phase 0 output for `/sp.plan`. This is a verification-first phase, so research
is a codebase audit of the four critical behaviors plus the concrete decisions
for the two small fixes. Each decision records alternatives considered.

---

## 1. User Isolation — verified in existing code

**Decision**: No code changes; extend the A/B test matrix to connections and
analytics with guessed-`ObjectId` probes and 404-body-equality assertions.

**Evidence (read directly from the current tree)**:
- `backend/dependencies.py` — `get_current_user` resolves identity ONLY from the
  HttpOnly JWT cookie (`cai_token`); invalid/missing token → 401. No identity is
  accepted from body/query/headers.
- `backend/routes/messages.py` — `get_messages`, `get_message`, `update_message`,
  `delete_message`, `override_priority`, `get_filter_counts`, senders/sources all
  include `{"user_id": uid}` as the base/first filter, and document lookups add
  `user_id` to the `_id` query so cross-user access yields `None` → 404 (identical
  to non-existent; never 403).
- `backend/routes/tasks.py`, `backend/routes/connections.py`,
  `backend/routes/analytics.py` — same pattern (analytics `user_id` is the first
  `$match` in every pipeline, per `services/analytics.py`).
- `backend/tests/test_user_isolation.py` already covers messages/tasks/dashboard/
  logout for A/B including guessed IDs.

**Gap found**: connections and `/analytics` are isolated by construction but
lack dedicated cross-user tests. The isolation matrix must be extended there.

---

## 2. Webhook security — verified in existing code

**Decision**: No code changes to `verify_signature`/payload validation; add
missing negative tests (malformed body → 400, signature header edge cases).

**Evidence**:
- `backend/routes/webhooks.py::verify_signature` — HMAC-SHA256 over the raw body
  with `WHATSAPP_APP_SECRET`, constant-time (`hmac.compare_digest`); an
  unconfigured secret rejects EVERY delivery (fail closed). Missing/odd header →
  rejected before any parsing.
- Payload is structurally validated by Pydantic (`MetaWebhookPayload.model_validate_json`)
  → `ValidationError` → 400, nothing stored.
- `GET /webhooks/whatsapp` verify-challenge path returns the challenge only when
  the verify token matches; otherwise 403.
- `POST /webhooks/whatsapp` has NO auth dependency by design — its security IS the
  signature (documented decision, public surface). `POST /webhooks/simulate`
  DOES require `get_current_user`.

**Gap found**: `_resolve_owner()` maps to the first `provider: whatsapp,
status: connected` connection with no user filter — correct for a single-WABA
deployment but not multi-number multi-user. Accepted limitation for the FYP
(Simplicity First); recorded in `contracts/`.

---

## 3. AI reliability — one real gap (retry)

**Verified (no change needed)**:
- `services/ai/orchestrate.py::process_message` is the single AI entry point and
  NEVER raises: `_analyze_with_fallback` catches provider-construction + analysis
  crashes and returns a `status: "pending"` fallback dict; trivial/no-content
  short-circuits to deterministic defaults.
- `services/webhook_ingest.py::ingest_message` stores the document (with
  `user_id`, identity fields) BEFORE scheduling analysis; `_analyze_and_store`
  guards persistence so ingestion never blocks on or dies with the AI.
- `routes/messages.py::create_message` runs analysis after persist, `process_message`
  guarantees a dict; pending fallback is stored.

**Gap found (the fix)**:
- Nothing retries `ai_analysis.status: "pending"` messages. The pending stub is
  persisted and the dashboard shows it, but analysis never completes later.
- **Decision**: add `backend/services/retry_pending.py::retry_pending_analyses()` —
  user-scoped sweep over `{"ai_analysis.status": "pending"}`; for each message call
  `process_message(content, message_id, user_id, thread_id)` then
  `update_one({"_id": ..., "user_id": ...}, {"$set": {"ai_analysis": analysis}})`.
  Started as a rate-bounded loop in `main.py` lifespan, skipped on
  `communication_ai_test` (same pattern as the Gmail poller), exported for direct
  unit testing.
- **Alternatives considered**:
  - *Retry inside the ingest background task only* — fails because a single failed
    attempt wouldn't retry again.
  - *Retry on next channel poll (Gmail/WhatsApp)* — couples retry cadence to
    message traffic; channels that go quiet would never retry.
  - *MongoDB TTL/separate queue collection* — violates "no new collections" and
    Simplicity First. Rejected.
  - *Sweep on every new message ingest* — unbounded latency on the request path.
    Rejected (never block ingestion).
  The periodic sweep is the smallest mechanism that satisfies "retried later" with
  idempotent in-place updates.

---

## 4. Duplicate prevention — one real gap (user scoping)

**Verified (no change needed)**:
- `services/webhook_ingest.py::ingest_message` dedupes on `external_message_id`
  via `DuplicateKeyError` catch (acknowledge + skip, no re-analysis).
- `backend/tests/test_webhooks.py` covers duplicate delivery → exactly one
  document, no second analysis call.
- Gmail poller funnels through the same `ingest_message` path (message id as key).

**Gap found (the fix)** — two-part:
- `backend/main.py` creates a unique index on `external_message_id` ALONE
  (partial). That is NOT user-scoped — the constitution (Day 29 rule 4) requires a
  user-scoped unique key.
- `ingest_message`'s `DuplicateKeyError` recovery does
  `find_one({"external_message_id": external_message_id})` with **no user filter**.
  If a duplicate-key error ever fired for a key owned by another user, the ingest
  path would return the OTHER user's message id — a silent identity error.
- **Decision**:
  1. Composite unique index `[("user_id", 1), ("external_message_id", 1)]` with
     `partialFilterExpression={"external_message_id": {"$type": "string"}}` in
     `main.py` lifespan.
  2. Scope the recovery lookup: `find_one({"user_id": user_id, "external_message_id": ...})`.
- **Alternatives considered**:
  - *Keep the app-layer check only, no index* — a race can insert two documents
    (constitution: "the database is the final authority"). Rejected.
  - *Keep the global unique index and add user_id to the check* — the global index
    would still let the SECOND user's legitimately-distinct same-key document hit
    `DuplicateKeyError`. Rejected; the key must be `{user_id, external_message_id}`.
  - *Deterministic key for key-less (simulate) messages* — a hash of
    user+source+sender+content can falsely dedupe two legitimate identical sends.
    Per constitution rule 5, simulate/manual messages are **explicitly exempted**
    and documented instead. Rejected deriving.
  - *Dedupe `POST /messages` (manual API create)* — manual CRUD, not a delivery/
    reprocessing path; duplicates there are user-meaningful. Explicitly out of
    scope, documented in `contracts/`.

---

## 5. No new dependencies, no new endpoints

**Decision**: The phase introduces zero new libraries and zero public API
changes. Existing deps (motor, pymongo, pytest, stdlib `hmac`/`hashlib`) cover
everything. The verification surface (which existing endpoints are exercised and
what each asserts) is documented in `contracts/security-testing.md`.

---

## Open questions

None. The only ambiguity (what "retried later" means) is resolved to a periodic,
rate-bounded background sweep run by `retry_pending_analyses()` and exercised by
direct unit tests rather than left to manual timing.