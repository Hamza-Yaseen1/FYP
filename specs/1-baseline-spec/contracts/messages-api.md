# API Contracts: Messages & Tasks

**Date**: 2026-08-19
**Base URL**: `http://localhost:8000`

## Messages

### POST /messages

Create a new message and trigger AI analysis.

**Request**:
```json
{
  "sender": "string",
  "content": "string",
  "source": "string"
}
```

**Response (201)**:
```json
{
  "id": "string",
  "sender": "string",
  "content": "string",
  "source": "string",
  "status": "unread",
  "state": "active",
  "ai_analysis": {
    "priority": "important",
    "confidence": 0.85,
    "summary": "Short summary of the message",
    "recommended_actions": ["Reply", "Schedule meeting"],
    "tasks_extracted": ["Send report by Friday"],
    "deadlines": ["2026-08-22"],
    "provider": "openai",
    "analyzed_at": "2026-08-19T10:30:00Z",
    "status": "completed"
  },
  "created_at": "2026-08-19T10:30:00Z",
  "updated_at": "2026-08-19T10:30:00Z"
}
```

**Error Response (500)** - AI Analysis Failed:
```json
{
  "id": "string",
  "sender": "string",
  "content": "string",
  "source": "string",
  "status": "unread",
  "state": "active",
  "ai_analysis": {
    "priority": "pending",
    "confidence": 0.0,
    "summary": null,
    "recommended_actions": [],
    "tasks_extracted": [],
    "deadlines": [],
    "provider": "openai",
    "analyzed_at": null,
    "status": "failed"
  },
  "created_at": "2026-08-19T10:30:00Z",
  "updated_at": "2026-08-19T10:30:00Z"
}
```

---

### GET /messages

Get all messages for the user, sorted by creation time (newest first).

**Query Parameters**:
- `state` (optional): "active" or "archived" (default: "active")
- `priority` (optional): Filter by AI priority level
- `limit` (optional): Max results (default: 100)

**Response (200)**:
```json
[
  {
    "id": "string",
    "sender": "string",
    "content": "string",
    "source": "string",
    "status": "string",
    "state": "string",
    "ai_analysis": { ... },
    "created_at": "datetime",
    "updated_at": "datetime"
  }
]
```

---

### GET /messages/{id}

Get a single message by ID.

**Response (200)**:
```json
{
  "id": "string",
  "sender": "string",
  "content": "string",
  "source": "string",
  "status": "string",
  "state": "string",
  "ai_analysis": { ... },
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

**Error Response (404)**:
```json
{
  "detail": "Message not found"
}
```

---

### PUT /messages/{id}

Update message fields (status, state, or override AI priority).

**Request**:
```json
{
  "status": "read",
  "state": "archived",
  "ai_priority_override": "urgent"
}
```

**Response (200)**: Updated message object

---

### DELETE /messages/{id}

Delete a message permanently.

**Response (204)**: No content

---

## Tasks

### GET /tasks

Get all tasks for the user.

**Query Parameters**:
- `status` (optional): "pending" or "completed" (default: all)
- `sort` (optional): "deadline" or "created" (default: "created")

**Response (200)**:
```json
[
  {
    "id": "string",
    "message_id": "string",
    "description": "Send report by Friday",
    "deadline": "2026-08-22T00:00:00Z",
    "status": "pending",
    "created_at": "2026-08-19T10:30:00Z",
    "updated_at": "2026-08-19T10:30:00Z"
  }
]
```

---

### PUT /tasks/{id}

Update a task (mark complete, edit description, update deadline).

**Request**:
```json
{
  "status": "completed",
  "description": "Updated description",
  "deadline": "2026-08-23T00:00:00Z"
}
```

**Response (200)**: Updated task object

---

### DELETE /tasks/{id}

Delete a task permanently.

**Response (204)**: No content

---

## Webhooks (Updated)

### POST /webhooks/whatsapp

Receive simulated WhatsApp message with AI analysis.

**Request**:
```json
{
  "sender": "string",
  "message": "string",
  "timestamp": "2026-08-19T10:30:00Z"
}
```

**Response (200)**:
```json
{
  "success": true,
  "message": "WhatsApp message received and analyzed",
  "data": {
    "id": "string",
    "sender": "string",
    "content": "string",
    "source": "whatsapp",
    "status": "unread",
    "state": "active",
    "ai_analysis": { ... },
    "created_at": "datetime",
    "updated_at": "datetime"
  }
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid message ID"
}
```

### 404 Not Found
```json
{
  "detail": "Message not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "AI analysis failed. Message stored without analysis."
}
```

---

## Authentication

**Note**: Authentication is P4 priority (deferred). All endpoints currently
operate in single-user development mode without authentication.

**Future**: JWT-based authentication with secure cookie storage.
