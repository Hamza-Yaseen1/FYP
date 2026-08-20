# Data Model: Task Extraction & Deadline Detection

**Feature**: 004-task-extraction-deadline
**Date**: 2026-08-20

## Updated Entities

### ExtractedTask (Pydantic Model — embedded in AIAnalysis)

Represents a single task extracted from a message. Stored inside the
message's `ai_analysis.tasks_extracted` array.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| description | string | yes | Clear, concise action description |
| deadline | string \| null | yes | Time expression from message, or null |
| priority_indicator | string \| null | yes | Urgency words from message, or null |
| requires_action | boolean | yes | Always true for extracted tasks |

**Validation rules**:
- `description` MUST be non-empty and under 200 characters
- `deadline` MUST be null or a string present in the original message
- `priority_indicator` MUST be null or a word/phrase from the original message
- `requires_action` is always `true` (tasks by definition require action)

**Example**:
```json
{
  "description": "Send FYP slides",
  "deadline": "Tonight",
  "priority_indicator": "tonight",
  "requires_action": true
}
```

---

### Task (MongoDB Document — tasks collection)

Represents an extracted task stored separately for the Tasks page.
Includes a reference back to the source message.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| _id | ObjectId | auto | MongoDB document ID |
| description | string | yes | Task description (from ExtractedTask) |
| deadline | string \| null | yes | Time expression or null |
| priority_indicator | string \| null | yes | Urgency words or null |
| requires_action | boolean | yes | Always true |
| status | string | yes | "pending" or "completed" |
| source_message_id | string | yes | ObjectId of source message (as string) |
| source_message_preview | string | yes | First 100 chars of message content |
| created_at | datetime | yes | When the task was extracted |

**State transitions**:
```
pending → completed (user marks done)
pending → deleted (user removes task)
```

**Indexes**:
- `status`: for filtering pending vs completed tasks
- `source_message_id`: for finding tasks by message
- `created_at`: for sorting by extraction time

---

### AIAnalysis (Updated Pydantic Model — embedded in Message)

The existing `AIAnalysis` model gains structured task objects.

| Field | Type | Before | After |
|-------|------|--------|-------|
| tasks_extracted | list | `list[str]` | `list[ExtractedTask]` |
| deadlines | list | `list[str]` | `list[str]` (unchanged) |

**Migration**: Existing messages with `tasks_extracted: []` (empty string arrays)
are compatible — empty arrays are valid for both types.

---

## Entity Relationships

```
Message (1) ──contains──► (N) ExtractedTask (embedded in ai_analysis)
Message (1) ──referenced-by──► (N) Task (tasks collection, via source_message_id)
```

- A message can produce 0 or more extracted tasks
- Each Task in the collection references exactly one source Message
- Deleting a message should cascade-delete its tasks (or leave orphaned tasks
  with a null source_message_id — simpler, defers cleanup)

---

## Validation Summary

| Entity | Field | Rule |
|--------|-------|------|
| ExtractedTask | description | Non-empty, max 200 chars |
| ExtractedTask | deadline | null or string from message |
| ExtractedTask | priority_indicator | null or string from message |
| Task | status | Must be "pending" or "completed" |
| Task | source_message_id | Valid ObjectId string |
| Task | source_message_preview | Max 100 chars |
