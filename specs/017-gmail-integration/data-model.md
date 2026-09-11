# Data Model: Gmail Connection & Ingest Extensions

**Feature**: 017-gmail-integration | **Date**: 2026-09-10 | **Phase**: 1

## 1. Scope

Day 26 adds **three optional fields** to `connections` documents
(`token_expires_at`, `last_fetched_at`, `gmail_email`), **one optional field**
to `messages` (`subject`), and extends `ingest_message` to accept `subject`
and to self-analyze when no `BackgroundTasks` is supplied. No collection is
renamed/migrated; existing documents remain valid; all additions are
non-breaking.

## 2. Connection Document (MongoDB `connections`)

Existing shape (Day 19) — `_id`, `user_id`, `provider`, `status`,
`access_token` (encrypted), `refresh_token` (encrypted), `created_at`,
`updated_at`, unique index `(user_id, provider)` — is extended:

```json
{
  "_id": "ObjectId(…)",
  "user_id": "ObjectId(507f1f77…)",
  "provider": "gmail",
  "status": "connected | disconnected | error | coming_soon",

  "access_token": "uGEJh4…(AES-CBC, b64(IV+cipher))",
  "refresh_token": "uGEJh4…(AES-CBC, b64(IV+cipher))",
  "token_expires_at": "2026-09-10T10:41:00Z",     // NEW (Optional) — access token expiry (now + expires_in − 60s)
  "last_fetched_at": "2026-09-10T09:41:00Z",      // NEW (Optional) — new-email watermark (after:<epoch>)
  "gmail_email": "hamza@gmail.com",               // NEW (Optional) — connected account address (display only)

  "created_at": "2026-09-10T09:40:00Z",
  "updated_at": "2026-09-10T09:41:00Z"
}
```

### Field notes

- **`access_token` / `refresh_token`** — always `encrypt()`-ed (existing
  `utils/encryption.py`, AES-256-CBC, key `ENCRYPTION_KEY`). Never returned
  by any endpoint.
- **`token_expires_at`** — set on exchange and on each refresh; read by
  `ensure_access_token()` to decide proactive refresh. Missing/past → refresh.
- **`last_fetched_at`** — written after each successful poll; drives the
  `q=after:<epoch>` query (research §4). First poll defaults to
  `connected_at − 1h` so emails that arrived during connect are not missed.
- **`gmail_email`** — display-only nicety for the Connections page; fetched
  best-effort from Google tokeninfo at connect time. `None` on failure is
  fine.

### Provider guard

- Gmail connections are created ONLY by the OAuth callback. The generic
  `POST /connections` (used by WhatsApp) MUST reject `provider: "gmail"`
  with `400 {"detail": "Use the Gmail connect flow"}` to prevent mock-token
  rows.

### Status transitions

| From | Event | To |
|---|---|---|
| (none) | OAuth callback success + tokens stored | `connected` |
| `connected` | user clicks Disconnect → Google revoke succeeds/fails, tokens deleted, doc removed | (deleted) |
| `connected` | refresh/API returns `invalid_grant` (user revoked app) | `error` |
| `error` | user reconnects via fresh OAuth | `connected` (doc upserted) |
| `connected` | transient API failure (5xx, network) | stays `connected` (retry next poll) |

## 3. Message Document (MongoDB `messages`) — additive `subject`

The canonical message document (Days 23/25) gains one optional field:

```json
{
  "_id": "ObjectId(…)",
  "user_id": "ObjectId(…)",
  "source": "gmail",
  "sender": "teacher@example.com",
  "content": "Please submit the report.",
  "subject": "Project Submission",     // NEW (Optional) — Gmail only; absent for WhatsApp/simulate
  "message_type": "text",
  "status": "unread",
  "state": "active",
  "created_at": "…", "updated_at": "…", "received_at": "…",
  "messageId": "…", "threadId": null, "conversationId": null,
  "external_message_id": "1856f2d3…",   // dedup key (unique partial index exists)
  "ai_analysis": { … }
}
```

- `subject` is a plain optional string on the document. Existing messages
  simply lack it; the Inbox card renders it only "when present" (constitution
  Day 26 format rule 7). Non-email channels never set it.
- Dedup unchanged: unique partial index on `external_message_id` +
  `DuplicateKeyError` handling in `ingest_message` (spec FR-006).

## 4. `ingest_message` signature change

`backend/services/webhook_ingest.py::ingest_message`:

```python
async def ingest_message(
    user_id: str,
    source: str,
    sender: str,
    content: str,
    external_message_id: Optional[str] = None,
    message_type: str = "text",
    background_tasks: Optional[BackgroundTasks] = None,
    subject: Optional[str] = None,          # NEW
) -> str
```

Behavior:
- `doc["subject"] = subject` when not None (additive).
- When `background_tasks is None` AND a new message was inserted, spawn
  `asyncio.create_task(_analyze_and_store(content, message_id, user_id,
  thread_id))` and keep the task in a module-level `set()` to avoid GC. When
  `background_tasks` is provided (webhook/simulate), behavior is unchanged.
- Duplicate `external_message_id` returns the existing id without re-analysis
  (unchanged).

## 5. Indexes

| Collection | Index | Status |
|---|---|---|
| `connections` | `(user_id, provider)` unique | exists (unchanged) |
| `connections` | `(user_id)` | exists (unchanged) |
| `messages` | `external_message_id` unique partial | exists (unchanged) |
| `messages` | `(user_id, created_at)` | exists (unchanged) |

The poller's query `connections.find({"provider": "gmail", "status":
"connected"})` is served by the existing `(user_id)` index; no new indexes
required. No index touches tokens; page scans of encrypted token data are not
needed because lookups go through the `(user_id, provider)` filter.

## 6. API Response Mapping

- `ConnectionService.get_user_connections` continues to return only
  `{id, provider, status, created_at}` (+ `gmail_email` when present). Never
  tokens (Day 19 rule 2).
- `MessageResponse`: `subject` mapped from `doc.get("subject")` (None → omit).

## 7. Isolation guarantees

- All connection reads/writes filter `user_id` first
  (`ConnectionService` is fully user-scoped today).
- The callback's owner comes from the verified signed `state`
  (`sub` claim), which can only be minted server-side with `JWT_SECRET` for
  the authenticated user.
- The poller iterates connections WITHOUT cross-referencing message data; each
  connection's emails are ingested under that connection's own `user_id`.
- Cross-user access to a connection returns 404 identical to not-found
  (existing behavior, unchanged).