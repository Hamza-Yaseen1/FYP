# Data Model: Task Management

**Feature**: 012-task-management  
**Date**: 2026-08-26  
**Status**: Complete

## Existing Entities

### Task (existing - minor extensions required)

**Collection**: `tasks`

**Fields**:
| Field | Type | Description | Filterable | Sortable |
|-------|------|-------------|------------|----------|
| `_id` | ObjectId | Unique identifier | No | No |
| `user_id` | string | Owner's user ID (from JWT) | Yes (required) | No |
| `description` | string | Task description from AI extraction | No | No |
| `deadline` | string | Deadline text (e.g., "Tonight", "Tomorrow") | No | Yes (priority-based) |
| `priority_indicator` | string | Priority level: "urgent", "important", "normal" | Yes | Yes |
| `requires_action` | boolean | Whether task requires user action | No | No |
| `status` | string | Task status: "pending", "in_progress", "completed" | Yes | No |
| `source_message_id` | string | ID of original message | No | No |
| `source_message_preview` | string | Preview of source message | No | No |
| `created_at` | datetime | Creation timestamp | No | Yes |
| `updated_at` | datetime | Last update timestamp | No | No |
| `snoozed_until` | datetime | Snooze expiration timestamp (new field) | Yes | Yes |

**Existing Indexes**:
- `{ user_id: 1, created_at: -1 }` (compound index for user's tasks sorted by date)

**New Indexes Required**:
- `{ user_id: 1, priority_indicator: 1, created_at: -1 }` (compound index for priority-based sorting)
- `{ user_id: 1, snoozed_until: 1 }` (compound index for snooze expiration queries)

### Message (existing - no changes required)

**Collection**: `messages`

**Fields**:
| Field | Type | Description | Filterable | Searchable |
|-------|------|-------------|------------|------------|
| `_id` | ObjectId | Unique identifier | No | No |
| `user_id` | string | Owner's user ID (from JWT) | Yes (required) | No |
| `sender` | string | Message sender name | Yes | Yes |
| `content` | string | Message body text | No | Yes |
| `source` | string | Communication source (whatsapp, gmail, etc.) | Yes | No |
| `created_at` | datetime | Creation timestamp | Yes (date range) | No |

**Note**: Task's `source_message_id` references this collection.

### User (existing - no changes required)

**Collection**: `users`

**Fields**:
| Field | Type | Description |
|-------|------|-------------|
| `_id` | ObjectId | Unique identifier |
| `email` | string | User email (unique) |
| `name` | string | User name |

**Note**: Task's `user_id` references this collection.

## New Entities

### SnoozeRequest (request model)

**Purpose**: Validate snooze action parameters

**Request Structure**:
```json
{
  "duration": "1hour" | "tomorrow" | "nextweek"
}
```

**Validation Rules**:
- `duration` must be one of: "1hour", "tomorrow", "nextweek"
- Invalid duration should return 400 Bad Request

### TaskResponse (extended existing model)

**Purpose**: Return task data with computed fields

**Response Structure**:
```json
{
  "id": "string",
  "description": "string",
  "deadline": "string | null",
  "priority_indicator": "urgent | important | normal",
  "requires_action": true,
  "status": "pending | in_progress | completed",
  "source_message_id": "string",
  "source_message_preview": "string",
  "created_at": "datetime",
  "updated_at": "datetime | null",
  "snoozed_until": "datetime | null",
  "is_snoozed": false
}
```

**Note**: `is_snoozed` is a computed field indicating if task is currently snoozed.

## Data Relationships

```
User (1) ──< (many) Task
User (1) ──< (many) Message
Message (1) ──< (many) Task (via source_message_id)
```

## Validation Rules

### Task Status Values

| Status | Description | Allowed Transitions |
|--------|-------------|---------------------|
| `pending` | Task awaiting action | → `in_progress`, → `completed` |
| `in_progress` | Task being worked on | → `completed`, → `pending` |
| `completed` | Task finished | → `pending` (reopen) |

### Priority Indicator Values

| Value | Description | Visual Indicator |
|-------|-------------|------------------|
| `urgent` | Requires immediate attention | 🔴 |
| `important` | Important but not urgent | 🟡 |
| `normal` | Regular task | 🟢 |

### Snooze Duration Mapping

| Duration | Time Addition | Example |
|----------|---------------|---------|
| `1hour` | +1 hour from now | 2026-08-26 12:00 → 2026-08-26 13:00 |
| `tomorrow` | +1 day from now | 2026-08-26 12:00 → 2026-08-27 12:00 |
| `nextweek` | +7 days from now | 2026-08-26 12:00 → 2026-09-02 12:00 |

## State Transitions

### Task Status

```
[pending] ──(start)──> [in_progress]
[in_progress] ──(complete)──> [completed]
[completed] ──(reopen)──> [pending]
```

### Task Snooze State

```
[active] ──(snooze)──> [snoozed]
[snoozed] ──(expiration)──> [active]
[snoozed] ──(complete)──> [completed]
```

**Note**: Snooze state is determined by `snoozed_until` timestamp. If current time < snoozed_until, task is snoozed.

## Query Patterns

### Get Tasks with Priority Sorting

```python
# Base query - always include user_id
query = {"user_id": uid}

# Exclude completed tasks by default (unless specifically requested)
if not include_completed:
    query["status"] = {"$ne": "completed"}

# Exclude currently snoozed tasks (unless specifically requested)
if not include_snoozed:
    query["$or"] = [
        {"snoozed_until": {"$exists": False}},
        {"snoozed_until": {"$lte": datetime.now(timezone.utc)}}
    ]

# Sort by priority then by created_at
pipeline = [
    {"$match": query},
    {"$addFields": {
        "priority_order": {
            "$switch": {
                "branches": [
                    {"case": {"$eq": ["$priority_indicator", "urgent"]}, "then": 1},
                    {"case": {"$eq": ["$priority_indicator", "important"]}, "then": 2},
                    {"case": {"$eq": ["$priority_indicator", "normal"]}, "then": 3}
                ],
                "default": 4
            }
        }
    }},
    {"$sort": {"priority_order": 1, "created_at": -1}},
    {"$limit": 100}
]

tasks = await tasks_collection.aggregate(pipeline).to_list(100)
```

### Snooze Task

```python
# Calculate new deadline based on duration
def calculate_snooze_deadline(duration: str) -> datetime:
    now = datetime.now(timezone.utc)
    if duration == "1hour":
        return now + timedelta(hours=1)
    elif duration == "tomorrow":
        # Same time tomorrow
        return now + timedelta(days=1)
    elif duration == "nextweek":
        # Same time next week
        return now + timedelta(weeks=1)
    return now  # default

# Update task with snooze deadline
new_deadline = calculate_snooze_deadline(duration)
result = await tasks_collection.find_one_and_update(
    {"_id": ObjectId(task_id), "user_id": uid},
    {"$set": {"snoozed_until": new_deadline, "updated_at": datetime.now(timezone.utc)}},
    return_document=True
)
```

### Complete Task

```python
# Mark task as completed
result = await tasks_collection.find_one_and_update(
    {"_id": ObjectId(task_id), "user_id": uid},
    {"$set": {"status": "completed", "updated_at": datetime.now(timezone.utc)}},
    return_document=True
)
```

## Migration Considerations

### Adding snoozed_until Field

Existing tasks don't have `snoozed_until` field. Queries should handle missing field gracefully:

```python
# Query pattern for snoozed tasks
query = {
    "$or": [
        {"snoozed_until": {"$exists": False}},  # Never snoozed
        {"snoozed_until": {"$lte": datetime.now(timezone.utc)}}  # Snooze expired
    ]
}
```

### Backward Compatibility

- Existing task status values remain valid
- New `snoozed_until` field is optional (defaults to null)
- Frontend should handle tasks without `snoozed_until` field