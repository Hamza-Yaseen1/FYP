# API Contract — Analytics (Day 28)

## `GET /analytics`

Read-only summary of the authenticated user's communication data. Requires the
session cookie (same auth as all `/messages`, `/tasks` endpoints). Returns 401
when unauthenticated.

### Query Parameters

| Param | Type | Required | Default | Description |
|---|---|---|---|---|
| `period` | string | no | `week` | `day` (last 24 h), `week` (last 7 days), `month` (last 30 days). Invalid value → 400. |

### Request

```http
GET /analytics?period=week
Cookie: signal_token=...
```

### 200 OK Response

```json
{
  "period": "week",
  "from": "2026-09-04T00:00:00Z",
  "to": "2026-09-11T23:59:59Z",
  "total": 247,
  "by_priority": {
    "urgent": 12,
    "important": 38,
    "normal": 151,
    "low": 46,
    "pending": 0
  },
  "by_source": {
    "whatsapp": 180,
    "gmail": 67
  },
  "tasks": {
    "total": 42,
    "completed": 28
  },
  "trends": [
    { "date": "2026-09-05", "count": 34 },
    { "date": "2026-09-06", "count": 41 }
  ]
}
```

### Field Semantics

- `total` — count of `messages` where `user_id` = session user AND `received_at`
  within `[from, to]`.
- `by_priority` — counts per priority bucket (see data-model.md bucket rule).
  Sum of the five buckets equals `total`.
- `by_source` — counts per distinct stored `source` value. Sum equals `total`.
- `tasks.total` — tasks whose parent message (by `source_message_id`) falls in
  the period; `tasks.completed` — subset with `status == "completed"`.
- `trends` — one entry per time bucket in `[from, to]`, zero-filled:
  - `period=day` → hourly buckets (`YYYY-MM-DDTHH:00:00Z` labels, or local-day
    hours as a fixed decision: use UTC hourly buckets).
  - `period=week|month` → daily buckets (`YYYY-MM-DD`).
  - No bucket is skipped; days/hours with zero messages return `count: 0`.

### Errors

| Status | Body | When |
|---|---|---|
| 401 | `{"detail":"Not authenticated."}` | missing/invalid session cookie |
| 400 | `{"detail":"Invalid period. Must be day, week, or month."}` | bad `period` value |

### Aggregation Notes (implementation guidance)

1. All pipelines start `$match: { "user_id": <uid>, ... }` — `user_id` first.
2. Use `$count`/`$group` over `messages` for `total`, `by_priority`, `by_source`;
   trends use `$group` on the bucket key then zero-fill in Python for the full
   range.
3. Tasks: load task docs for the user in range, resolve `source_message_id` in
   Python (or `$lookup`), count `completed` via `status`.
4. Date range computed server-side from `datetime.now(timezone.utc)` minus
   `timedelta(days=...)` — never trust client-provided `from`/`to`.

### Example: period boundary

| period | `from` | `to` (inclusive logic) |
|---|---|---|
| `day` | now − 24 h | now |
| `week` | now − 7 days | now |
| `month` | now − 30 days | now |