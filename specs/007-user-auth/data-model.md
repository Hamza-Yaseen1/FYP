# Data Model: 007-user-auth

**Date**: 2026-08-21 | **Database**: MongoDB `communication_ai`

## Entity: User (NEW — collection `users`)

| Field | Type | Rules |
|-------|------|-------|
| `_id` | ObjectId | Auto |
| `name` | string | Required, 1–100 chars, trimmed |
| `email` | string | Required, valid format (EmailStr), lowercased, **unique index** |
| `password_hash` | string | bcrypt hash (60 chars, cost 12 default) — NEVER plaintext |
| `created_at` | datetime | UTC, set server-side |

Indexes:
- `{ email: 1 }` unique — created at app startup (`create_index`), the
  race-proof duplicate guard.

Validation rules (enforced by Pydantic `UserCreate`):
- name: required after trim
- email: RFC-format valid; stored lowercase
- password: min length 8; max length 72 (bcrypt input limit); no
  character restrictions

State transitions: none (single active state in Week 3; no
activation/deactivation).

API representation (`UserResponse`): `_id → id`, `name`, `email`,
`created_at`. **`password_hash` is never serialized.**

## Entity: Message (EXISTING — collection `messages`) — gains ownership

| Change | Detail |
|--------|--------|
| NEW field | `user_id`: string (owner's User id as str(ObjectId)) |
| Set by | Server-side at creation from the authenticated session — never from client payload |
| Query rule | Every request-path read/update/delete filters by `user_id` |
| Legacy docs | Ownerless docs are invisible to scoped queries; assign via `backend/scripts/assign_legacy_data.py` or delete |

Existing fields unchanged: sender, content, source, status, state,
ai_analysis, created_at, updated_at.

## Entity: Task (EXISTING — collection `tasks`) — gains ownership

Same treatment as Message: new `user_id` field, stamped server-side,
every query filtered by it. Existing fields unchanged: description,
deadline, priority_indicator, status, source_message_preview, created_at.

## Entity: Session Credential (not persisted)

JWT (HS256), 7-day expiry, delivered as httpOnly cookie `cai_token`.

| Claim | Value |
|-------|-------|
| `sub` | str(user `_id`) |
| `iat` | issued-at (UTC) |
| `exp` | iat + 7 days |

Verification: signature + expiry checked on every protected request;
any failure → 401. Token is stateless — logout clears the cookie only
(no server-side revocation in Week 3).

## Relationships

```text
User 1 ──── * Message      (messages.user_id → users._id)
User 1 ──── * Task         (tasks.user_id   → users._id)
Message 1 ── 1 ai_analysis  (embedded, inherits ownership)
Task * ───── 1 Message     (source_message_preview; same owner by construction)
```

## Isolation invariant (testable)

For every request R made by user U:
`every document read or written during R satisfies doc.user_id == U.id`.
Cross-user access attempts return 404 (existence not confirmed).
