# Data Model: Cross-Platform Dashboard

**Phase 1 output** — no schema changes. The dashboard is a read-only
consumer of the existing `messages` collection.

## Message (existing MongoDB document — unchanged)

The single source of truth for the dashboard. Every field a card draws
from already exists:

| Field | Type | Notes |
|---|---|---|
| `_id` / `messageId` | ObjectId / str | identity |
| `user_id` | str | owner — all dashboard queries are scoped to it |
| `sender` | str | display name (WhatsApp profile name / Gmail from-header) |
| `content` | str | message text |
| `source` | str (`whatsapp` \| `gmail` \| …) | enum; drives the source label |
| `subject` | str \| None | Gmail only; absent for WhatsApp |
| `status` | str (`unread` …) | read state (not used for grouping) |
| `created_at` | datetime | drives within-group recency (newest first) |
| `received_at` | datetime | server receive time (created_at equivalent here) |

### `ai_analysis` subdocument (existing — unchanged)

| Field | Type | Card usage |
|---|---|---|
| `priority` | `urgent` \| `important` \| `normal` \| `low` \| `pending` | group membership + priority badge |
| `confidence` | float 0–1 | PriorityBadge (unchanged) |
| `summary` | str \| None | title fallback |
| `tasks_extracted[].description` | str | primary title source |
| `tasks_extracted[].deadline` | str \| None | deadline pill (original wording) |
| `deadlines[]` | list[str] | available but not required for v1 cards |
| `recommended_action` | str | recommended-action box |
| `needs_attention` | bool | attention badge |
| `attention_reason` | str | "Why it matters" |

## Derived view (no storage)

### PriorityGroup

A client-side grouping of messages by `ai_analysis.priority`, in fixed
order:

| Group | `priority` value | Notes |
|---|---|---|
| URGENT | `urgent` | highest |
| IMPORTANT | `important` | |
| NORMAL | `normal` | |
| LOW | `low` | |
| Pending analysis | `pending` (or missing `ai_analysis`) | tail group; collapsed visually, `pending` badge |

Rules:
- A message belongs to exactly one group (by `priority`). Null/missing
  `ai_analysis` → Pending tail.
- Within a group, messages sort by `created_at` descending (stable for
  equal timestamps).
- Groups with zero messages are not rendered.
- The group is derived at render time from the fetched `GET /messages`
  payload; nothing is persisted and nothing is recomputed server-side.

## Relationships

- **User 1—N Message**: each message carries `user_id`; the dashboard
  shows messages where `user_id` = authenticated user. Cross-user access
  remains impossible (404 semantics unchanged).
- **Message 1—1 ai_analysis** (nullable): the analysis is embedded; when
  absent the message still renders in the Pending tail.

## Validation & constraints (carried over, untouched)

- No new writes: the dashboard **never** inserts, updates, or deletes
  messages itself. (Deletion remains a user action on existing pages.)
- No migrations required.
- `source` values outside `whatsapp`/`gmail` render a neutral label but
  never alter grouping.