# Data Model: Day 18 – User Isolation

**Date**: 2026-08-25
**Feature**: 009-user-isolation

## Entities

### User (unchanged)

| Field | Type | Required | Notes |
|---|---|---|---|
| `_id` | ObjectId | yes | Primary key, auto-generated |
| `name` | str | yes | 1–100 chars |
| `email` | str | yes | Unique index, lowercase |
| `password_hash` | str | yes | bcrypt hash |
| `created_at` | datetime | yes | UTC |

### Message (unchanged schema, verified user_id)

| Field | Type | Required | Notes |
|---|---|---|---|
| `_id` | ObjectId | yes | Primary key |
| `user_id` | str | yes | Owner's `_id` as string. SET by route handler from JWT. |
| `sender` | str | yes | Sender name |
| `content` | str | yes | Message body |
| `source` | str | yes | "whatsapp", "gmail", "simulated" |
| `status` | str | yes | "unread" or "read" |
| `state` | str | yes | "active" or "deleted" |
| `ai_analysis` | dict | no | Embedded analysis (priority, summary, tasks, etc.) |
| `created_at` | datetime | yes | UTC |
| `updated_at` | datetime | yes | UTC |

**Indexes**:
- `{ "user_id": 1, "created_at": -1 }` — supports per-user listing sorted
  by newest first.

### Task (user_id fix required)

| Field | Type | Required | Notes |
|---|---|---|---|
| `_id` | ObjectId | yes | Primary key |
| `user_id` | str | yes | Owner's `_id` as string. **BUG: currently not set by analyzer.** |
| `description` | str | yes | Task description |
| `deadline` | str | no | Original deadline wording from message |
| `priority_indicator` | str | no | Priority hint from message |
| `requires_action` | bool | yes | Always true |
| `status` | str | yes | "pending", "in_progress", "completed" |
| `source_message_id` | str | yes | Message `_id` as string |
| `source_message_preview` | str | yes | First 80 chars of message |
| `created_at` | datetime | yes | UTC |

**Indexes**:
- `{ "user_id": 1, "created_at": -1 }` — supports per-user listing sorted
  by newest first.

## Ownership Model

| Collection | Ownership Field | Set By | Filtered By |
|---|---|---|---|
| `users` | `_id` | System (registration) | N/A |
| `messages` | `user_id` | Route handler (from JWT) | Every query |
| `tasks` | `user_id` | Analyzer (from message) | Every query |

## Changes Summary

1. **`analyze_message()` signature**: Add `user_id: str` parameter.
2. **Task document creation**: Include `"user_id": user_id` in every task
   doc created by the analyzer.
3. **Route handlers**: Pass `user_id` when calling `analyze_message()`.
4. **Database indexes**: Add `{ "user_id": 1, "created_at": -1 }` on
   `messages` and `tasks` in the app lifespan.
