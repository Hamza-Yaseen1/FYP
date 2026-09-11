# Data Model — Analytics (Day 28)

**Date**: 2026-09-11 | **Branch**: 019-analytics

## Scope

Analytics is a **read-only view** over two existing collections. No new
collections, no schema changes, no migrations. MongoDB aggregation pipelines
compute everything on demand per request.

## Existing collections (read-only reuse)

### `messages`

Relevant fields for analytics:

| Field | Type | Used For |
|---|---|---|
| `_id` | ObjectId | identity |
| `user_id` | string | ownership — **first filter in every pipeline** |
| `source` | string (`whatsapp`, `gmail`, ...) | Communications by Source chart |
| `received_at` | datetime | period filter (today/week/month) and trend buckets |
| `ai_analysis.priority` | string (`urgent`/`important`/`normal`/`low`/`pending`) | priority buckets + Pending bucket |
| `ai_analysis.status` | string (`pending`/...) | distinguishing un-analyzed messages |

Priority bucket rule:

- `urgent` → Urgent
- `important` → Important
- `normal` → Normal
- `low` → Low
- anything else (including `pending`) or missing `ai_analysis` → **Pending**

### `tasks`

Relevant fields for analytics:

| Field | Type | Used For |
|---|---|---|
| `_id` | ObjectId | identity |
| `user_id` | string | ownership — first filter |
| `source_message_id` | string (ObjectId) | join to parent `message._id` for period scoping |
| `status` | string (`pending`/`in_progress`/`completed`) | completed vs total |
| `created_at` | datetime | fallback ordering |

Task period scoping: join to the parent message via `source_message_id` and use
the message's `received_at` so task numbers align with the selected message
period. If the parent message is missing, the task is scoped by `created_at`.

## Analytics snapshot (response — not persisted)

The API returns a read-only snapshot object:

| Field | Type | Meaning |
|---|---|---|
| `period` | string | `day` / `week` / `month` echoed back |
| `from` / `to` | datetime | resolved UTC range used for the query |
| `total` | int | total messages in range |
| `by_priority` | { urgent, important, normal, low, pending: int } | counts per priority bucket |
| `by_source` | { whatsapp: int, gmail: int, ... } | counts per stored `source` value |
| `tasks` | { total: int, completed: int } | extracted vs completed |
| `trends` | [{ date: str, count: int }] | per-bucket volume (daily/hourly), zero-filled |

## Validation rules

- `period` MUST be exactly `day`, `week`, or `month`; anything else → 400.
- Every aggregation pipeline MUST begin with `$match: { user_id: <session user> }`.
- Empty results are valid and MUST be represented (e.g., all counts 0), never
  a 404.
- No cross-user expansion: `user_id` is never sourced from request body/query.

## State transitions

N/A — analytics requests are pure reads; nothing transitions state.