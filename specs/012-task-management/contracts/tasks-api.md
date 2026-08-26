# Tasks API Contract: Task Management

**Feature**: 012-task-management  
**Date**: 2026-08-26  
**Status**: Complete

## Endpoints

### 1. Get Tasks with Priority Sorting

**Endpoint**: `GET /tasks`

**Purpose**: Retrieve tasks for the authenticated user sorted by priority

**Query Parameters**:

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `include_completed` | boolean | No | Include completed tasks (default: false) | `?include_completed=true` |
| `include_snoozed` | boolean | No | Include currently snoozed tasks (default: false) | `?include_snoozed=true` |
| `limit` | integer | No | Maximum tasks to return (default: 100, max: 200) | `?limit=50` |

**Request Headers**:
```
Cookie: access_token=<jwt_token>
```

**Response (200 OK)**:
```json
{
  "tasks": [
    {
      "id": "507f1f77bcf86cd799439011",
      "description": "Send FYP slides",
      "deadline": "Tonight",
      "priority_indicator": "urgent",
      "requires_action": true,
      "status": "pending",
      "source_message_id": "507f1f77bcf86cd799439012",
      "source_message_preview": "Please send the FYP slides tonight",
      "created_at": "2026-08-26T10:30:00Z",
      "updated_at": null,
      "snoozed_until": null,
      "is_snoozed": false
    },
    {
      "id": "507f1f77bcf86cd799439013",
      "description": "Review documentation",
      "deadline": "Tomorrow",
      "priority_indicator": "important",
      "requires_action": true,
      "status": "pending",
      "source_message_id": "507f1f77bcf86cd799439014",
      "source_message_preview": "Please review the documentation by tomorrow",
      "created_at": "2026-08-26T09:15:00Z",
      "updated_at": null,
      "snoozed_until": null,
      "is_snoozed": false
    }
  ],
  "total": 25,
  "limit": 100
}
```

**Response (401 Unauthorized)**:
```json
{
  "detail": "Not authenticated"
}
```

**User Isolation**: 
- Query automatically filters by `user_id` from JWT token
- User cannot access tasks belonging to other users

**Sorting**:
- Primary: Priority (urgent → important → normal)
- Secondary: Creation date (newest first)

---

### 2. Update Task Status

**Endpoint**: `PUT /tasks/{task_id}/status`

**Purpose**: Update task status (complete, reopen, etc.)

**Path Parameters**:
| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `task_id` | string | Yes | Task ID | `507f1f77bcf86cd799439011` |

**Request Headers**:
```
Cookie: access_token=<jwt_token>
Content-Type: application/json
```

**Request Body**:
```json
{
  "status": "completed"
}
```

**Valid Status Values**:
- `pending` - Task awaiting action
- `in_progress` - Task being worked on
- `completed` - Task finished

**Response (200 OK)**:
```json
{
  "id": "507f1f77bcf86cd799439011",
  "description": "Send FYP slides",
  "deadline": "Tonight",
  "priority_indicator": "urgent",
  "requires_action": true,
  "status": "completed",
  "source_message_id": "507f1f77bcf86cd799439012",
  "source_message_preview": "Please send the FYP slides tonight",
  "created_at": "2026-08-26T10:30:00Z",
  "updated_at": "2026-08-26T14:30:00Z",
  "snoozed_until": null,
  "is_snoozed": false
}
```

**Response (400 Bad Request)**:
```json
{
  "detail": "Invalid status. Must be: pending, in_progress, or completed"
}
```

**Response (404 Not Found)**:
```json
{
  "detail": "Task not found"
}
```

**User Isolation**: 
- Task must belong to the authenticated user
- Returns 404 if task belongs to another user

---

### 3. Snooze Task

**Endpoint**: `PUT /tasks/{task_id}/snooze`

**Purpose**: Snooze a task for a specified duration

**Path Parameters**:
| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `task_id` | string | Yes | Task ID | `507f1f77bcf86cd799439011` |

**Request Headers**:
```
Cookie: access_token=<jwt_token>
Content-Type: application/json
```

**Request Body**:
```json
{
  "duration": "tomorrow"
}
```

**Valid Duration Values**:
- `1hour` - Snooze for 1 hour
- `tomorrow` - Snooze until same time tomorrow
- `nextweek` - Snooze until same time next week

**Response (200 OK)**:
```json
{
  "id": "507f1f77bcf86cd799439011",
  "description": "Send FYP slides",
  "deadline": "Tonight",
  "priority_indicator": "urgent",
  "requires_action": true,
  "status": "pending",
  "source_message_id": "507f1f77bcf86cd799439012",
  "source_message_preview": "Please send the FYP slides tonight",
  "created_at": "2026-08-26T10:30:00Z",
  "updated_at": "2026-08-26T14:30:00Z",
  "snoozed_until": "2026-08-27T14:30:00Z",
  "is_snoozed": true
}
```

**Response (400 Bad Request)**:
```json
{
  "detail": "Invalid duration. Must be: 1hour, tomorrow, or nextweek"
}
```

**Response (404 Not Found)**:
```json
{
  "detail": "Task not found"
}
```

**User Isolation**: 
- Task must belong to the authenticated user
- Returns 404 if task belongs to another user

---

### 4. Get Task Source Message

**Endpoint**: `GET /tasks/{task_id}/message`

**Purpose**: Retrieve the original message that created the task

**Path Parameters**:
| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `task_id` | string | Yes | Task ID | `507f1f77bcf86cd799439011` |

**Request Headers**:
```
Cookie: access_token=<jwt_token>
```

**Response (200 OK)**:
```json
{
  "message": {
    "id": "507f1f77bcf86cd799439012",
    "sender": "Ali",
    "content": "Please send the FYP slides tonight",
    "source": "whatsapp",
    "created_at": "2026-08-26T10:30:00Z"
  }
}
```

**Response (404 Not Found)**:
```json
{
  "detail": "Task or message not found"
}
```

**User Isolation**: 
- Task must belong to the authenticated user
- Message must belong to the same user
- Returns 404 if either belongs to another user

---

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 400 Bad Request
```json
{
  "detail": "Invalid parameter: <parameter_name> - <error_message>"
}
```

### 404 Not Found
```json
{
  "detail": "Task not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "An error occurred while processing your request"
}
```

## Rate Limiting

- No specific rate limiting for Day 21
- Existing API rate limits apply

## Caching

- Task lists: No caching (real-time data)
- Source messages: Cache for 60 seconds per user

## Pagination

- Default limit: 100 tasks
- Maximum limit: 200 tasks
- Response includes `total` count for pagination UI