# Messages API Contract: Better Inbox

**Feature**: 011-better-inbox  
**Date**: 2026-08-26  
**Status**: Complete

## Endpoints

### 1. Get Messages with Filters

**Endpoint**: `GET /messages`

**Purpose**: Retrieve messages for the authenticated user with optional filtering and search

**Query Parameters**:

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `tab` | string | No | Filter by priority tab: "all", "urgent", "important", "normal", "unread" | `?tab=urgent` |
| `source` | string | No | Filter by communication source | `?source=whatsapp` |
| `priority` | string | No | Filter by priority level: "urgent", "important", "normal", "low" | `?priority=important` |
| `start_date` | ISO datetime | No | Filter messages from this date | `?start_date=2026-08-01T00:00:00Z` |
| `end_date` | ISO datetime | No | Filter messages up to this date | `?end_date=2026-08-26T23:59:59Z` |
| `sender` | string | No | Filter by sender name | `?sender=Ali` |
| `search` | string | No | Search across sender, content, and summary | `?search=meeting` |
| `limit` | integer | No | Maximum messages to return (default: 100, max: 200) | `?limit=50` |
| `offset` | integer | No | Pagination offset (default: 0) | `?offset=100` |

**Request Headers**:
```
Cookie: access_token=<jwt_token>
```

**Response (200 OK)**:
```json
{
  "messages": [
    {
      "id": "507f1f77bcf86cd799439011",
      "sender": "Ali",
      "content": "Please review the FYP slides tonight",
      "source": "whatsapp",
      "status": "unread",
      "state": "active",
      "ai_analysis": {
        "priority": "urgent",
        "confidence": 0.95,
        "summary": "Urgent request to review FYP slides",
        "recommended_action": "Review slides before tonight",
        "needs_attention": true,
        "attention_reason": "Task with near deadline detected"
      },
      "created_at": "2026-08-26T10:30:00Z",
      "updated_at": "2026-08-26T10:30:00Z"
    }
  ],
  "total": 150,
  "limit": 100,
  "offset": 0
}
```

**Response (401 Unauthorized)**:
```json
{
  "detail": "Not authenticated"
}
```

**Response (400 Bad Request)**:
```json
{
  "detail": "Invalid date range: start_date must be before end_date"
}
```

**User Isolation**: 
- Query automatically filters by `user_id` from JWT token
- User cannot access messages belonging to other users

---

### 2. Get Filter Counts

**Endpoint**: `GET /messages/counts`

**Purpose**: Retrieve counts for each filter option without fetching all messages

**Query Parameters**: None (counts are for all user's messages)

**Request Headers**:
```
Cookie: access_token=<jwt_token>
```

**Response (200 OK)**:
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

**Response (401 Unauthorized)**:
```json
{
  "detail": "Not authenticated"
}
```

**User Isolation**: 
- Counts are computed only for messages belonging to the authenticated user

---

### 3. Get Unique Senders

**Endpoint**: `GET /messages/senders`

**Purpose**: Retrieve list of unique senders for the sender filter dropdown

**Query Parameters**:
| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `search` | string | No | Search senders by name | `?search=Ali` |

**Request Headers**:
```
Cookie: access_token=<jwt_token>
```

**Response (200 OK)**:
```json
{
  "senders": [
    "Ali",
    "Sara",
    "Ahmed",
    "Fatima"
  ]
}
```

**Response (401 Unauthorized)**:
```json
{
  "detail": "Not authenticated"
}
```

**User Isolation**: 
- Senders are extracted only from messages belonging to the authenticated user

---

### 4. Get Unique Sources

**Endpoint**: `GET /messages/sources`

**Purpose**: Retrieve list of unique sources for the source filter dropdown

**Query Parameters**: None

**Request Headers**:
```
Cookie: access_token=<jwt_token>
```

**Response (200 OK)**:
```json
{
  "sources": [
    "whatsapp",
    "gmail",
    "linkedin"
  ]
}
```

**Response (401 Unauthorized)**:
```json
{
  "detail": "Not authenticated"
}
```

**User Isolation**: 
- Sources are extracted only from messages belonging to the authenticated user

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

### 500 Internal Server Error
```json
{
  "detail": "An error occurred while processing your request"
}
```

## Rate Limiting

- No specific rate limiting for Day 20
- Existing API rate limits apply

## Caching

- Filter counts: Cache for 60 seconds per user
- Senders/sources: Cache for 300 seconds per user
- Message lists: No caching (real-time data)

## Pagination

- Default limit: 100 messages
- Maximum limit: 200 messages
- Offset-based pagination: `?offset=100&limit=100`
- Response includes `total` count for pagination UI