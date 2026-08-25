# Data Model: Better Inbox

**Feature**: 011-better-inbox  
**Date**: 2026-08-26  
**Status**: Complete

## Existing Entities

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
| `status` | string | Read status: "unread" or "read" | Yes | No |
| `state` | string | Message state: "active" or "archived" | Yes | No |
| `ai_analysis` | object | Nested AI analysis results | Yes (priority) | Yes (summary) |
| `created_at` | datetime | Creation timestamp | Yes (date range) | No |
| `updated_at` | datetime | Last update timestamp | No | No |

**AI Analysis Sub-fields**:
| Field | Type | Description | Filterable |
|-------|------|-------------|------------|
| `priority` | string | Priority level: "urgent", "important", "normal", "low", "pending" | Yes |
| `confidence` | float | AI confidence score (0.0-1.0) | No |
| `summary` | string | AI-generated summary | Yes (search only) |
| `recommended_action` | string | AI-recommended next step | No |
| `needs_attention` | boolean | Flag for attention required | No |

**Existing Indexes**:
- `{ user_id: 1, created_at: -1 }` (compound index for user's messages sorted by date)

**New Indexes Required**:
- Text index on `sender`, `content`, `ai_analysis.summary` for search functionality

## New Entities

### FilterCounts (read-only, computed)

**Purpose**: Return counts for each filter option without fetching all messages

**Response Structure**:
```json
{
  "tabs": {
    "all": 150,
    "urgent": 12,
    "important": 35,
    "normal": 98,
    "unread": 45
  },
  "sources": {
    "whatsapp": 80,
    "gmail": 65,
    "linkedin": 5
  },
  "priorities": {
    "urgent": 12,
    "important": 35,
    "normal": 98,
    "low": 5
  },
  "senders": {
    "Ali": 15,
    "Sara": 12,
    "Ahmed": 8
  }
}
```

**Note**: This is a computed response, not a stored entity. Generated via MongoDB aggregation pipeline.

## Data Relationships

```
User (1) ──< (many) Message
User (1) ──< (many) Task
Message (1) ──< (many) ExtractedTask (via ai_analysis.tasks_extracted)
```

## Validation Rules

### Filter Parameters

| Parameter | Type | Valid Values | Default |
|-----------|------|--------------|---------|
| `tab` | string | "all", "urgent", "important", "normal", "unread" | "all" |
| `source` | string | Any source from user's messages | null (all) |
| `priority` | string | "urgent", "important", "normal", "low" | null (all) |
| `start_date` | ISO datetime | Any valid date | null (no limit) |
| `end_date` | ISO datetime | Any valid date | null (no limit) |
| `sender` | string | Any sender from user's messages | null (all) |
| `search` | string | Any text query | "" (no search) |

### Date Range Validation

- `start_date` must be before or equal to `end_date`
- If `start_date` is provided without `end_date`, filter from start_date to now
- If `end_date` is provided without `start_date`, filter from beginning to end_date
- Invalid date ranges should return 400 Bad Request

## State Transitions

### Message State

```
[active] ──(archive)──> [archived]
[archived] ──(unarchive)──> [active]
```

### Message Status

```
[unread] ──(read)──> [read]
[read] ──(mark unread)──> [unread]
```

**Note**: Status transitions are not part of Day 20 scope. Messages are filtered by current status only.

## Query Patterns

### Get Messages with Filters

```python
# Base query - always include user_id
query = {"user_id": uid}

# Tab filter
if tab == "urgent":
    query["ai_analysis.priority"] = "urgent"
elif tab == "important":
    query["ai_analysis.priority"] = "important"
elif tab == "normal":
    query["ai_analysis.priority"] = "normal"
elif tab == "unread":
    query["status"] = "unread"

# Additional filters (compose with AND)
if source:
    query["source"] = source
if priority:
    query["ai_analysis.priority"] = priority
if sender:
    query["sender"] = sender
if start_date or end_date:
    query["created_at"] = {}
    if start_date:
        query["created_at"]["$gte"] = start_date
    if end_date:
        query["created_at"]["$lte"] = end_date
if search:
    query["$text"] = {"$search": search}

# Execute query
messages = await messages_collection.find(query).sort("created_at", -1).limit(100).to_list(100)
```

### Get Filter Counts

```python
# Aggregation pipeline for counts
pipeline = [
    {"$match": {"user_id": uid}},
    {"$facet": {
        "tabs": [
            {"$group": {"_id": "$ai_analysis.priority", "count": {"$sum": 1}}},
            {"$group": {"_id": None, "urgent": {"$sum": {"$cond": [{"$eq": ["$_id", "urgent"]}, "$count", 0]}}, ...}}
        ],
        "sources": [
            {"$group": {"_id": "$source", "count": {"$sum": 1}}},
            {"$push": {"k": "$_id", "v": "$count"}}
        ],
        # ... similar for priorities and senders
    }}
]
```