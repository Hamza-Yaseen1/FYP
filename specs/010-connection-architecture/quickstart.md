# Quickstart: Connection Architecture

**Date**: 2026-08-25
**Feature**: 010-connection-architecture
**Phase**: 1 - Design

## Overview

This guide helps you get the Connection Architecture feature running locally. The feature allows users to connect external communication accounts (WhatsApp, Gmail, LinkedIn) to the Communication AI system.

## Prerequisites

- Backend running on `http://localhost:8000`
- Frontend running on `http://localhost:3000`
- MongoDB running and accessible
- Authenticated user session (logged in)

## Environment Variables

Add these to your backend `.env` file:

```bash
# Encryption key for tokens (generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
ENCRYPTION_KEY=your-encryption-key-here

# MongoDB connection (if not already set)
MONGODB_URL=mongodb://localhost:27017/communication_ai
```

## Quick Test

### 1. View Connections Page

1. Open `http://localhost:3000/connections` in your browser
2. You should see "Connected Accounts" page with:
   - WhatsApp [Connect]
   - Gmail [Connect]
   - LinkedIn [Coming Soon]

### 2. Test API Endpoints

**List connections:**
```bash
curl -b "session_token=YOUR_JWT_TOKEN" http://localhost:8000/connections
```

Expected response:
```json
{
  "connections": [
    {
      "id": "507f1f77bcf86cd799439011",
      "provider": "whatsapp",
      "status": "disconnected",
      "createdAt": "2026-08-25T10:30:00Z"
    }
  ]
}
```

**Create connection:**
```bash
curl -X POST -b "session_token=YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"provider": "whatsapp"}' \
  http://localhost:8000/connections
```

Expected response:
```json
{
  "id": "507f1f77bcf86cd799439011",
  "provider": "whatsapp",
  "status": "connected",
  "createdAt": "2026-08-25T10:30:00Z"
}
```

**Delete connection:**
```bash
curl -X DELETE -b "session_token=YOUR_JWT_TOKEN" \
  http://localhost:8000/connections/507f1f77bcf86cd799439011
```

Expected: `204 No Content`

### 3. Verify Security

**Check that tokens are never exposed:**
```bash
# Create a connection
curl -X POST -b "session_token=YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"provider": "gmail"}' \
  http://localhost:8000/connections

# List connections - verify no tokens in response
curl -b "session_token=YOUR_JWT_TOKEN" http://localhost:8000/connections
```

The response should NOT contain `accessToken` or `refreshToken` fields.

**Check user isolation:**
1. Login as User A, create a connection
2. Login as User B, list connections
3. User B should NOT see User A's connections

## File Structure

```
specs/010-connection-architecture/
├── spec.md              # Feature specification
├── plan.md              # Implementation plan
├── research.md          # Research decisions
├── data-model.md        # Data model documentation
├── quickstart.md        # This file
└── contracts/
    └── connections-api.yaml  # API contract
```

## Implementation Checklist

- [ ] Create Connection model (`backend/src/models/connection.py`)
- [ ] Create encryption utility (`backend/src/utils/encryption.py`)
- [ ] Create Connection service (`backend/src/services/connection.py`)
- [ ] Create Connection API routes (`backend/src/routes/connections.py`)
- [ ] Create MongoDB indexes
- [ ] Create API client (`frontend/lib/api/connections.ts`)
- [ ] Create ConnectionCard component (`frontend/components/connections/ConnectionCard.tsx`)
- [ ] Create ConnectionList component (`frontend/components/connections/ConnectionList.tsx`)
- [ ] Create Connections page (`frontend/app/(dashboard)/connections/page.tsx`)
- [ ] Test connection creation flow
- [ ] Test connection deletion flow
- [ ] Test user isolation
- [ ] Verify token encryption
- [ ] Verify no token exposure in API responses

## Common Issues

### "Encryption key not set"
- Ensure `ENCRYPTION_KEY` is set in backend `.env`
- Generate key with: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`

### "Connection already exists"
- Each user can only have one connection per provider
- Disconnect existing connection before connecting again

### "Provider not supported"
- Only WhatsApp and Gmail are supported for now
- LinkedIn shows "Coming Soon"

### "Unauthorized"
- Ensure you're logged in and session cookie is valid
- Check that `/connections` route is protected in Next.js middleware

## Next Steps

After implementing this feature:
1. Add actual OAuth flow for WhatsApp/Gmail
2. Implement webhook processing for incoming messages
3. Add connection health monitoring
4. Implement token refresh logic
