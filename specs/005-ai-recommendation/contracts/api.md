# API Contract: AI Recommended Action

**Date**: 2026-08-21
**Feature**: 005-ai-recommendation
**Branch**: 005-ai-recommendation

## Endpoints

### POST /webhooks/whatsapp

**Request**:
```json
{
  "sender": "string (required)",
  "message": "string (required)"
}
```

**Response** (200 OK):
```json
{
  "id": "string",
  "sender": "string",
  "content": "string",
  "source": "whatsapp",
  "status": "unread",
  "state": "active",
  "created_at": "2026-08-21T00:00:00Z",
  "updated_at": "2026-08-21T00:00:00Z",
  "ai_analysis": {
    "priority": "urgent | important | normal | low",
    "confidence": 0.85,
    "explanation": "string",
    "summary": "string | null",
    "recommended_action": "string (NEW)",
    "recommended_actions": [],
    "tasks_extracted": [
      {
        "description": "string",
        "deadline": "string | null",
        "priority_indicator": "string | null",
        "requires_action": true
      }
    ],
    "deadlines": ["string"],
    "provider": "groq",
    "analyzed_at": "2026-08-21T00:00:00Z",
    "status": "completed | pending"
  }
}
```

### GET /messages

**Response** (200 OK):
```json
[
  {
    "id": "string",
    "sender": "string",
    "content": "string",
    "source": "string",
    "status": "string",
    "state": "string",
    "created_at": "2026-08-21T00:00:00Z",
    "updated_at": "2026-08-21T00:00:00Z",
    "ai_analysis": {
      "priority": "string",
      "confidence": 0.85,
      "explanation": "string",
      "summary": "string | null",
      "recommended_action": "string (NEW)",
      "recommended_actions": [],
      "tasks_extracted": [...],
      "deadlines": [...],
      "provider": "string",
      "analyzed_at": "2026-08-21T00:00:00Z",
      "status": "string"
    }
  }
]
```

## Changes from Previous Version

| Field | Type | Location | Description |
|-------|------|----------|-------------|
| `recommended_action` | string | `ai_analysis` | **NEW**: Single recommended action for the user |

## Backward Compatibility

- Old clients that don't use `recommended_action` will ignore it (JSON field ignored by default)
- Old messages without `recommended_action` will return empty string `""` (Pydantic default)
- The `recommended_actions` (plural, array) field is kept for backward compatibility
