# API Contracts: Task Extraction & Deadline Detection

**Feature**: 004-task-extraction-deadline
**Date**: 2026-08-20

## Updated Endpoints

### POST /messages — Create Message with AI Analysis

**Request**:
```json
{
  "sender": "Ali",
  "content": "Send me the FYP slides tonight.",
  "source": "whatsapp"
}
```

**Response** (201):
```json
{
  "id": "64a1b2c3d4e5f6a7b8c9d0e1",
  "sender": "Ali",
  "content": "Send me the FYP slides tonight.",
  "source": "whatsapp",
  "status": "unread",
  "state": "active",
  "ai_analysis": {
    "priority": "urgent",
    "confidence": 0.92,
    "explanation": "Message contains deadline 'tonight' and action request",
    "summary": "Ali requests FYP slides by tonight.",
    "recommended_actions": ["Reply"],
    "tasks_extracted": [
      {
        "description": "Send FYP slides",
        "deadline": "Tonight",
        "priority_indicator": "tonight",
        "requires_action": true
      }
    ],
    "deadlines": ["Tonight"],
    "provider": "groq",
    "analyzed_at": "2026-08-20T10:30:00Z",
    "status": "completed"
  },
  "created_at": "2026-08-20T10:30:00Z",
  "updated_at": "2026-08-20T10:30:00Z"
}
```

**Changes from current**:
- `ai_analysis.tasks_extracted` is now `list[ExtractedTask]` (was `list[str]`)
- `ai_analysis.deadlines` remains `list[str]`
- Tasks are also stored in `tasks` collection (side effect, not in response)

---

### GET /messages — List Messages (unchanged structure, new fields)

**Response** (200):
```json
[
  {
    "id": "64a1b2c3d4e5f6a7b8c9d0e1",
    "sender": "Ali",
    "content": "Send me the FYP slides tonight.",
    "source": "whatsapp",
    "status": "unread",
    "state": "active",
    "ai_analysis": {
      "priority": "urgent",
      "confidence": 0.92,
      "tasks_extracted": [
        {
          "description": "Send FYP slides",
          "deadline": "Tonight",
          "priority_indicator": "tonight",
          "requires_action": true
        }
      ],
      "deadlines": ["Tonight"]
    },
    "created_at": "2026-08-20T10:30:00Z",
    "updated_at": "2026-08-20T10:30:00Z"
  }
]
```

---

## New Endpoints

### GET /tasks — List All Extracted Tasks

**Query Parameters**:
- `status` (optional): Filter by "pending" or "completed". Default: all.

**Response** (200):
```json
[
  {
    "id": "64a1b2c3d4e5f6a7b8c9d0e2",
    "description": "Send FYP slides",
    "deadline": "Tonight",
    "priority_indicator": "tonight",
    "requires_action": true,
    "status": "pending",
    "source_message_id": "64a1b2c3d4e5f6a7b8c9d0e1",
    "source_message_preview": "Send me the FYP slides tonight.",
    "created_at": "2026-08-20T10:30:00Z"
  }
]
```

**Errors**: None under normal conditions (empty array if no tasks exist).

---

### PUT /tasks/{task_id}/status — Update Task Status

**Request**:
```json
{
  "status": "completed"
}
```

**Response** (200):
```json
{
  "id": "64a1b2c3d4e5f6a7b8c9d0e2",
  "description": "Send FYP slides",
  "deadline": "Tonight",
  "status": "completed",
  "source_message_id": "64a1b2c3d4e5f6a7b8c9d0e1",
  "source_message_preview": "Send me the FYP slides tonight.",
  "created_at": "2026-08-20T10:30:00Z"
}
```

**Errors**:
- `400`: Invalid task ID or invalid status value
- `404`: Task not found

---

### DELETE /tasks/{task_id} — Delete a Task

**Response**: `204 No Content`

**Note**: Deleting a task does NOT delete the source message. The message
remains on the dashboard; only the task entry is removed from the
`tasks` collection.

**Errors**:
- `400`: Invalid task ID
- `404`: Task not found
