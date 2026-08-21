# Data Model: AI Recommended Action

**Date**: 2026-08-21
**Feature**: 005-ai-recommendation
**Branch**: 005-ai-recommendation

## Entities

### Message (existing, extended)

The `messages` collection stores all incoming communications. The `ai_analysis` subdocument is extended with a new field.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `_id` | ObjectId | yes | auto | Unique message identifier |
| `sender` | string | yes | - | Who sent the message |
| `content` | string | yes | - | Full message text |
| `source` | string | yes | - | Channel: "whatsapp", "gmail", etc. |
| `status` | string | yes | "unread" | Message state |
| `state` | string | yes | "active" | Lifecycle state |
| `created_at` | datetime | yes | utcnow | Creation timestamp |
| `updated_at` | datetime | yes | utcnow | Last update timestamp |
| `ai_analysis` | object | no | null | AI analysis results |

#### ai_analysis subdocument

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `priority` | string | yes | "normal" | "urgent" \| "important" \| "normal" \| "low" |
| `confidence` | float | yes | 0.0 | 0.0 - 1.0 |
| `explanation` | string | yes | "" | 1-2 sentence rationale |
| `summary` | string \| null | no | null | 1-2 sentence summary |
| `recommended_action` | string | no | "" | **NEW**: Single recommended action |
| `recommended_actions` | array | yes | [] | Legacy field (kept for compatibility) |
| `tasks_extracted` | array | yes | [] | Extracted tasks |
| `deadlines` | array | yes | [] | Detected deadlines |
| `provider` | string | yes | "groq" | LLM provider used |
| `analyzed_at` | datetime | yes | utcnow | Analysis timestamp |
| `status` | string | yes | "completed" | "completed" \| "pending" |

### Task (existing, no changes)

The `tasks` collection stores extracted tasks. No changes needed for this feature.

## Validation Rules

### recommended_action

- **Type**: string
- **Max length**: 100 characters (15 words × ~6 chars average)
- **Pattern**: Must start with a verb (imperative mood)
- **Default**: Empty string `""` when generation fails or message has no clear action
- **Language**: Must match the language of the message content

## State Transitions

### Message ai_analysis.status

```
[pending] → [completed]  (analysis succeeds)
[pending] → [pending]    (analysis fails, fallback applied)
```

No new states introduced for this feature.

## Relationships

```
Message (1) ──has──> (1) ai_analysis
Message (1) ──has──> (N) Task (via tasks_extracted array)
Message (1) ──has──> (0..1) recommended_action (new field in ai_analysis)
```

## Migration Notes

- Existing messages have `ai_analysis.recommended_actions: []` (empty array)
- New messages will have `ai_analysis.recommended_action: "string"` (non-empty)
- Old messages without `recommended_action` will default to `""` in the Pydantic model
- No database migration required — MongoDB is schema-less
