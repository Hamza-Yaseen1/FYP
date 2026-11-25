# 07 — Database

> The data model: what is stored, where, and how it is indexed. Sift uses **MongoDB Atlas** through the async driver **Motor**.

---

## 1. Overview

- **Database:** `communication_ai` (production) / `communication_ai_test` (tests). Set by `DB_NAME`.
- **Connection:** `backend/database.py` — `AsyncIOMotorClient` with `tz_aware=True`, 5 s server-selection and connect timeouts, and DNS resolvers pinned to 8.8.8.8 / 1.1.1.1 / 8.8.4.4 (to avoid SRV lookup timeouts on some networks).
- **Collections:** `users`, `messages`, `tasks`, `connections`, and `ai_analysis` (the last is registered as a collection but the live schema stores analysis **inside** each message — see note below).

> **Note on `ai_analysis`:** the AI analysis is stored as the `ai_analysis` **subdocument of a message**, not in a separate collection. The `ai_analysis` collection reference exists in `database.py` for legacy/historical reasons.

---

## 2. `users`

| Field | Type | Notes |
|-------|------|-------|
| `_id` | ObjectId | Primary key |
| `name` | string | Display name |
| `email` | string | **Unique** (index created in lifespan) |
| `password_hash` | string | bcrypt hash — plaintext never stored |
| `reset_token_hash` | string \| null | SHA-256 of the reset token (sparse index) |
| `reset_token_expires` | datetime \| null | 30-minute TTL |
| `created_at` | datetime | UTC |

**Indexes:**
- `email` — unique.
- `reset_token_hash` — sparse (so many users with no token don't collide).

---

## 3. `messages` (the core collection)

| Field | Type | Notes |
|-------|------|-------|
| `_id` | ObjectId | Primary key; also the `threadId` anchor when a thread forms |
| `user_id` | string (ObjectId) | **Owner — every query is scoped by this** |
| `source` | string | `gmail` \| `whatsapp` \| `simulate`/manual |
| `sender` | string | Normalised for thread matching |
| `subject` | string \| null | Gmail only (absent for WhatsApp) |
| `content` | string | Message body |
| `external_message_id` | string \| null | Provider id, used for dedupe |
| `received_at` | datetime | When the provider received it |
| `created_at` | datetime | When Sift stored it (used for "today"/analytics) |
| `is_read` | bool | Unread state |
| `messageId` | string | Always set server-side before insert |
| `threadId` | string \| null | Set only when linked (2nd in-window message) |
| `conversationId` | string \| null | Set only when linked |
| `ai_analysis` | object | See below |

### `ai_analysis` subdocument
```
ai_analysis: {
  status: "pending" | "completed" | "failed",
  provider: "groq" | "unknown",
  priority: "urgent" | "important" | "normal" | "low",
  confidence: number,
  explanation: string,
  summary: string,
  recommended_actions: [string],
  tasks_extracted: [ { title, deadline?, ... } ],
  deadlines: [ ... ],
  needs_attention: bool,
  attention_reason: string,
  reviewed: bool,
  verified: bool,
  context_updates: [ { field, value, source } ],   // popped before returning to the client
  routing: {
    agents_requested: [...],
    agents_run: [...],
    skipped: [...],
    llm_call_used: bool,
    reasons: [...]
  }
}
```

**Indexes:**
- `{ user_id, created_at }` — the workhorse for lists, counts, analytics.
- **Text index** on `sender`, `content`, `ai_analysis.summary` (background) — powers search.
- `{ user_id, external_message_id }` — **composite unique dedupe index** (replaced the old global index, which is dropped at startup).
- Gmail watermark support via `received_at`/`created_at`.

### Dedupe behaviour
- Two messages with the same `(user_id, external_message_id)` collide → the second insert is treated as a duplicate (skipped), and a `DuplicateKeyError` is recovered scoped to that composite key.
- Two **different users** with the same external id are independent.

---

## 4. `tasks`

| Field | Type | Notes |
|-------|------|-------|
| `_id` | ObjectId | |
| `user_id` | string | Owner |
| `source_message_id` | string \| null | Links back to the message that produced the task |
| `title` | string | Task text |
| `deadline` | datetime \| null | |
| `priority_indicator` | string | urgent/important/normal/low |
| `status` | string | `pending` \| `completed` |
| `snoozed_until` | datetime \| null | |
| `created_at` | datetime | UTC |

**Indexes** (`create_indexes()` in `database.py`):
- `{ user_id, priority_indicator, created_at }`.
- `{ user_id, snoozed_until }`.

**Listing rules** (`routes/tasks.py`):
- Excludes `completed` and tasks whose `snoozed_until` is in the future.
- Sorted by priority (urgent=1 … normal=3, default 4) then `created_at` desc.
- Limited to 100.

**Period scoping for analytics:** a task is attributed to its **parent message's `received_at`** (resolved via `source_message_id`, user-scoped `$in`), falling back to the task's own `created_at`.

---

## 5. `connections`

| Field | Type | Notes |
|-------|------|-------|
| `_id` | ObjectId | |
| `user_id` | string | Owner |
| `provider` | string | `whatsapp` \| `gmail` \| `linkedin` |
| `status` | string | `connected` \| `disconnected` \| `error` \| `coming_soon` |
| `access_token` | string \| null | **Encrypted** (AES) |
| `refresh_token` | string \| null | **Encrypted** (AES) |
| `token_expiry` | datetime \| null | |
| `email_address` | string \| null | For Gmail, the connected address |
| `last_fetched_at` | datetime \| null | Gmail poller watermark |
| `error_message` | string \| null | Shown as the Reconnect CTA when status is `error` |
| `created_at` / `updated_at` | datetime | |

**Indexes:**
- Unique `{ user_id, provider }` (`user_provider_unique`) — one connection per provider per user.
- `{ user_id }`.

Tokens are encrypted with `utils/encryption.py` (AES, key = `ENCRYPTION_KEY`).

---

## 6. Index creation and lifecycle

Indexes are created at startup in `main.py`'s lifespan (and `database.create_indexes()` for tasks):

| Index | Collection | Purpose |
|-------|-----------|---------|
| `email` (unique) | users | Prevent duplicate accounts |
| `reset_token_hash` (sparse) | users | Fast, safe reset lookup |
| `{user_id, created_at}` | messages | Lists/counts/analytics |
| text `sender, content, ai_analysis.summary` | messages | Search |
| `{user_id, external_message_id}` (unique) | messages | Dedupe |
| `{user_id, priority_indicator, created_at}` | tasks | Task list ordering |
| `{user_id, snoozed_until}` | tasks | Snooze filtering |
| `{user_id, provider}` (unique) | connections | One per provider |

> **Migration note:** the legacy **global** dedupe index on `external_message_id` is dropped at startup. The composite index is the current source of truth.

---

## 7. Access patterns (why the indexes exist)

| Operation | Query shape |
|-----------|-------------|
| Inbox list | `find({user_id, ...filters}).sort(created_at desc)` |
| Counts per tab | `count_documents({user_id, ...})` |
| Search | text index on `sender/content/summary`, user-scoped |
| Analytics | aggregations, **always** `$match` on `user_id` first |
| Task list | `find({user_id, status, snoozed_until}).sort(priority, created_at)` |
| Thread context | `find({user_id, threadId}).sort(created_at desc).limit(5)` |
| Dedupe | `find_one({user_id, external_message_id})` |

---

## 8. Multi-user isolation (the most important DB rule)

**Every** read and write is scoped by `user_id`, taken from the authenticated session — never from the request. This is what makes the app multi-tenant-safe. The security tests (`tests/test_security*.py`) verify:

- Cross-user `GET`/`DELETE` → **404** (not 403, to avoid id probing).
- Analytics never aggregates across users.
- Lists never include another user's documents.

---

## 9. Data lifecycle / retention

- Deleting a message is a hard delete (scoped to the owner).
- Deleting a connection removes its tokens (Gmail tokens are revoked at Google first, best-effort).
- There is **no automated retention/expiry** policy in the code; retention is whatever Atlas is configured for. This is an unresolved point in the legal docs (see `15_FINDINGS_AND_GAPS.md`).

---

## 10. Testing the database

- Tests run against `communication_ai_test`.
- `conftest.py` wipes `users`, `messages`, `tasks`, `connections` **before and after every test** (autouse `clean_db`), so tests never see each other's data.
- **Never** `await` motor under `asyncio.run` in a test — use the `TestClient` loop or a fake collection. (Motor is bound to the TestClient's event loop.)
- Analytics tests use a `_FakeAnalyticsMessages` collection to exercise aggregation pipelines deterministically.
