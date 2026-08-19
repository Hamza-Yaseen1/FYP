# Data Model: Communication AI

**Date**: 2026-08-19
**Feature**: Communication AI - AI Intelligence Layer

## Overview

Updated data models to support AI analysis results. The Message model gains
an embedded `ai_analysis` document. A new Task model tracks extracted tasks.

## Entity: Message (Updated)

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| _id | ObjectId | auto | Unique identifier |
| sender | string | yes | Message sender name/handle |
| content | string | yes | Full message text |
| source | string | yes | Channel: "whatsapp", "gmail", "simulated" |
| status | string | yes | "unread" or "read" |
| state | string | yes | "active" or "archived" (default: "active") |
| ai_analysis | object | no | Embedded AI analysis results |
| created_at | datetime | auto | Message timestamp |
| updated_at | datetime | auto | Last modification timestamp |

### ai_analysis Embedded Document

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| priority | string | yes | "urgent", "important", "normal", "low", "pending" |
| confidence | float | yes | 0.0 to 1.0 confidence score |
| summary | string | no | AI-generated summary (for messages >200 chars) |
| recommended_actions | array | yes | List of suggested actions |
| tasks_extracted | array | yes | List of extracted task descriptions |
| deadlines | array | yes | List of detected deadlines |
| provider | string | yes | LLM provider used ("openai", "groq", "gemini") |
| analyzed_at | datetime | yes | When analysis completed |
| status | string | yes | "completed", "pending", "failed" |

### State Transitions

```
Message States:
  active → archived (user action)
  archived → active (user action)

AI Analysis Status:
  pending → completed (analysis finished)
  pending → failed (analysis error)
  failed → pending (retry triggered)
```

### Indexes

```javascript
// Existing
db.messages.createIndex({ "created_at": -1 })
db.messages.createIndex({ "source": 1 })

// New for AI features
db.messages.createIndex({ "ai_analysis.priority": 1 })
db.messages.createIndex({ "state": 1 })
db.messages.createIndex({ "ai_analysis.status": 1 })
```

---

## Entity: Task (New)

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| _id | ObjectId | auto | Unique identifier |
| message_id | ObjectId | yes | Reference to source message |
| description | string | yes | Extracted task description |
| deadline | datetime | no | Detected deadline (if any) |
| status | string | yes | "pending" or "completed" |
| created_at | datetime | auto | Task creation timestamp |
| updated_at | datetime | auto | Last modification timestamp |

### State Transitions

```
Task States:
  pending → completed (user action)
  completed → pending (user action)
```

### Indexes

```javascript
db.tasks.createIndex({ "message_id": 1 })
db.tasks.createIndex({ "status": 1 })
db.tasks.createIndex({ "deadline": 1 })
db.tasks.createIndex({ "created_at": -1 })
```

### Validation Rules

- `description` must be non-empty string
- `status` must be one of: "pending", "completed"
- `deadline` must be valid datetime if provided
- `message_id` must reference existing message

---

## Entity: User (Existing - No Changes)

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| _id | ObjectId | auto | Unique identifier |
| email | string | yes | User email (unique) |
| password | string | yes | Hashed password |
| display_name | string | yes | User display name |
| created_at | datetime | auto | Account creation timestamp |

---

## Entity: Channel (Existing - No Changes)

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| _id | ObjectId | auto | Unique identifier |
| name | string | yes | Channel name (unique) |
| status | string | yes | "active" or "inactive" |
| configuration | object | no | Channel-specific settings |

---

## Relationships

```
User (1) ──┬── (N) Message
            └── (N) Task

Message (1) ──── (N) Task
Message (1) ──── (1) ai_analysis (embedded)
```

### Referential Integrity

- Tasks reference Messages via `message_id`
- Deleting a Message does NOT delete associated Tasks (orphaned tasks retained)
- Tasks can exist independently of Messages (user can create manual tasks)

---

## Query Patterns

### Get messages with AI analysis
```python
cursor = messages_collection.find(
    {"user_id": user_id, "state": "active"}
).sort("ai_analysis.priority", -1)
```

### Get pending tasks sorted by deadline
```python
cursor = tasks_collection.find(
    {"user_id": user_id, "status": "pending"}
).sort("deadline", 1)
```

### Get messages needing AI retry
```python
cursor = messages_collection.find(
    {"ai_analysis.status": "failed"}
)
```

---

## Migration Notes

### From Week 1 to Week 2

Existing messages will have no `ai_analysis` field. Frontend should handle:
- Missing `ai_analysis` → Show "Analysis pending" status
- Missing `state` → Default to "active"
- Existing `status` field (unread/read) preserved

### Adding AI Analysis to Existing Messages

Optional batch job to analyze existing messages:
```python
async def analyze_existing_messages():
    cursor = messages_collection.find({"ai_analysis": {"$exists": False}})
    async for doc in cursor:
        analysis = await ai_analyzer.analyze(doc["content"])
        await messages_collection.update_one(
            {"_id": doc["_id"]},
            {"$set": {"ai_analysis": analysis}}
        )
```
