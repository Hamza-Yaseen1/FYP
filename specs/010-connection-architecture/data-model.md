# Data Model: Connection Architecture

**Date**: 2026-08-25
**Feature**: 010-connection-architecture
**Phase**: 1 - Design

## Entity: Connection

Represents a link between a user and an external communication provider.

### Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `_id` | ObjectId | Yes | Auto-generated | Unique identifier |
| `user_id` | string | Yes | - | Owner's user ID (from JWT) |
| `provider` | string | Yes | - | Provider name (whatsapp, gmail, linkedin) |
| `status` | string | Yes | "disconnected" | Connection status |
| `accessToken` | string | No | null | Encrypted access token |
| `refreshToken` | string | No | null | Encrypted refresh token |
| `createdAt` | datetime | Yes | Current time | Connection creation timestamp |
| `updatedAt` | datetime | Yes | Current time | Last update timestamp |

### Field Constraints

- **user_id**: Must be a valid ObjectId string referencing the users collection
- **provider**: Must be one of: "whatsapp", "gmail", "linkedin"
- **status**: Must be one of: "connected", "disconnected", "error", "coming_soon"
- **accessToken**: Encrypted string, never stored in plaintext
- **refreshToken**: Encrypted string, never stored in plaintext
- **createdAt**: ISO 8601 datetime
- **updatedAt**: ISO 8601 datetime

### State Transitions

```text
[initial] → disconnected (when record created)
disconnected → connected (when OAuth flow completes successfully)
connected → disconnected (when user explicitly disconnects)
connected → error (when token refresh fails or provider API unavailable)
error → connected (when user reconnects successfully)
error → disconnected (when user explicitly disconnects)
```

### Indexes

1. **Unique compound index**: `{ user_id: 1, provider: 1 }`
   - Ensures one connection per user per provider
   - Supports efficient per-user queries

2. **Single index**: `{ user_id: 1 }`
   - Supports efficient listing of user's connections

### Relationships

- **User**: Many-to-one (many connections belong to one user)
- **Message**: One-to-many (one connection can receive many messages) - future feature

### Validation Rules

1. **user_id required**: Every connection must have an owner
2. **provider required**: Must specify which provider
3. **status required**: Must track connection state
4. **tokens optional**: May be null before OAuth completion
5. **timestamps required**: Must track creation and updates

### Security Rules

1. **Encryption**: accessToken and refreshToken must be encrypted before storage
2. **Isolation**: Every query must filter by user_id as first condition
3. **No cross-user access**: Requests for another user's connection return 404
4. **No token exposure**: API responses never include accessToken or refreshToken

### Example Document

```json
{
  "_id": "507f1f77bcf86cd799439011",
  "user_id": "507f1f77bcf86cd799439010",
  "provider": "whatsapp",
  "status": "connected",
  "accessToken": "encrypted_access_token_here",
  "refreshToken": "encrypted_refresh_token_here",
  "createdAt": "2026-08-25T10:30:00Z",
  "updatedAt": "2026-08-25T10:30:00Z"
}
```

## Entity: User (Existing)

The users collection already exists. Connection references it via user_id.

### Fields (relevant subset)

| Field | Type | Description |
|-------|------|-------------|
| `_id` | ObjectId | User identifier |
| `email` | string | User email (unique) |
| `name` | string | User display name |

### Relationship to Connection

- One user can have many connections (0 to N)
- Each connection belongs to exactly one user
- Foreign key: `connection.user_id` → `user._id`

## Database Schema (MongoDB)

### Collection: connections

```javascript
// Indexes
db.connections.createIndex({ user_id: 1, provider: 1 }, { unique: true });
db.connections.createIndex({ user_id: 1 });

// Document structure
{
  _id: ObjectId,
  user_id: String,
  provider: String,  // enum: ["whatsapp", "gmail", "linkedin"]
  status: String,    // enum: ["connected", "disconnected", "error", "coming_soon"]
  accessToken: String,  // encrypted
  refreshToken: String, // encrypted
  createdAt: Date,
  updatedAt: Date
}
```
