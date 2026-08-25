# Implementation Plan: Connection Architecture

**Branch**: `010-connection-architecture` | **Date**: 2026-08-25 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/010-connection-architecture/spec.md`

## Summary

Create a Connections page and database structure for Day 19 of the Communication AI project. Users will be able to view, connect, and disconnect external communication accounts (WhatsApp, Gmail, LinkedIn). The system stores connection records with encrypted tokens, enforcing strict user isolation and never exposing sensitive credentials to the frontend.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript 5.0+ (frontend)
**Primary Dependencies**: FastAPI (backend), Next.js 16.3 with App Router (frontend), Motor (MongoDB async driver)
**Storage**: MongoDB with Motor async driver
**Testing**: pytest (backend), Vitest + Testing Library (frontend)
**Target Platform**: Web application (Linux server backend, browser frontend)
**Project Type**: Web application with frontend/backend separation
**Performance Goals**: Dashboard loads in under 3 seconds, API responses under 500ms (excluding external API calls)
**Constraints**: University FYP timeline, must integrate with existing auth system
**Scale/Scope**: Single-user prototype extending to multi-user, 3 providers initially

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Simplicity First ✓
- Feature starts with simplest viable implementation (static provider list, basic CRUD)
- Complexity only added when proven necessary (token encryption, OAuth flow)
- Straightforward solutions preferred over clever ones

### Principle II: Vertical Slices ✓
- Feature delivers visible, testable value independently (Connections page with status display)
- End-to-end slice: UI → API → Database → Security
- Avoids horizontal layer building in isolation

### Principle IV: User Control ✓
- Users retain full control over connections (connect/disconnect with confirmation)
- No auto-connections without explicit user action
- Users can delete all connection data

### Principle V: Security and Privacy ✓
- Tokens encrypted at rest using AES-256
- Tokens never exposed to frontend
- Environment variables for encryption keys
- User isolation enforced (each user sees only their connections)
- 404 semantics for cross-user access attempts

### Day 19 Connection Architecture Rules ✓
- Tokens encrypted at rest: AES-256 or equivalent
- Tokens never exposed in API responses
- User isolation: every connection carries `user_id` from JWT
- Frontend shows only: provider, status, connect/disconnect buttons
- Backend handles all token operations

### User Isolation Rules ✓
- Every connection document carries `user_id` set server-side from JWT
- Every database query filters by `user_id` as first condition
- Requests for another user's connection return 404
- Connection deletion only affects authenticated user's connections

**Status**: All gates PASS. No violations detected.

## Project Structure

### Documentation (this feature)

```text
specs/010-connection-architecture/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── connections-api.yaml
└── tasks.md             # Phase 2 output (NOT created by /sp.plan)
```

### Source Code (repository root)

```text
# Web application structure (Option 2)
backend/
├── src/
│   ├── models/
│   │   └── connection.py      # Connection Pydantic model
│   ├── services/
│   │   └── connection.py      # Connection business logic
│   ├── routes/
│   │   └── connections.py     # Connection API endpoints
│   └── utils/
│       └── encryption.py      # Token encryption utilities
└── tests/
    ├── unit/
    │   └── test_connection.py
    └── integration/
        └── test_connections_api.py

frontend/
├── app/
│   └── (dashboard)/
│       └── connections/
│           └── page.tsx       # Connections page
├── components/
│   └── connections/
│       ├── ConnectionCard.tsx  # Provider card component
│       └── ConnectionList.tsx  # List of providers
└── lib/
    └── api/
        └── connections.ts     # API client for connections
```

**Structure Decision**: Web application structure with frontend/backend separation. Backend uses FastAPI with Motor for MongoDB. Frontend uses Next.js 16.3 with App Router. Existing project structure is followed.

## Complexity Tracking

> No Constitution Check violations detected. No complexity justifications required.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |

## Implementation Steps (Ordered)

### Phase 1: Database & Backend Foundation

1. **Create Connection model** (`backend/src/models/connection.py`)
   - Pydantic model with fields: user_id, provider, status, accessToken, refreshToken, createdAt
   - Validation rules for provider enum, status enum
   - Exclude tokens from response models

2. **Create encryption utility** (`backend/src/utils/encryption.py`)
   - AES-256 encryption/decryption functions
   - Environment variable for encryption key
   - Functions to encrypt before storage, decrypt when needed

3. **Create Connection service** (`backend/src/services/connection.py`)
   - CRUD operations for connections
   - User isolation filtering (always filter by user_id)
   - Token encryption/decryption handling
   - Status computation logic

4. **Create Connection API routes** (`backend/src/routes/connections.py`)
   - GET /connections - list user's connections (exclude tokens)
   - POST /connections - create/connect a new connection
   - DELETE /connections/{id} - disconnect a connection
   - All endpoints require authentication
   - All queries filter by user_id

5. **Create MongoDB indexes**
   - Compound index on (user_id, provider) for uniqueness
   - Index on user_id for efficient queries

### Phase 2: Frontend Implementation

6. **Create API client** (`frontend/lib/api/connections.ts`)
   - Functions to call backend endpoints
   - Type definitions for connection data (without tokens)

7. **Create ConnectionCard component** (`frontend/components/connections/ConnectionCard.tsx`)
   - Display provider name, status, connect/disconnect buttons
   - Handle loading and error states
   - "Coming Soon" label for unsupported providers

8. **Create ConnectionList component** (`frontend/components/connections/ConnectionList.tsx`)
   - Render list of ConnectionCard components
   - Handle empty state

9. **Create Connections page** (`frontend/app/(dashboard)/connections/page.tsx`)
   - Fetch connections from API
   - Render ConnectionList
   - Handle authentication redirect

### Phase 3: Integration & Testing

10. **Integration testing**
    - Test connection creation flow
    - Test connection deletion flow
    - Test user isolation (User A cannot see User B's connections)
    - Test token encryption (verify no plaintext in database)

11. **Security verification**
    - Verify API responses never contain tokens
    - Verify frontend never displays tokens
    - Verify 404 semantics for cross-user access

## Definition of Done

- [ ] Connections page displays at `/connections` with provider list
- [ ] WhatsApp and Gmail show "Connect" button when disconnected
- [ ] LinkedIn shows "Coming Soon" label
- [ ] Clicking "Connect" initiates OAuth flow (mocked for FYP)
- [ ] Connected accounts show "Connected" status with "Disconnect" button
- [ ] Disconnect shows confirmation dialog
- [ ] All tokens encrypted at rest in MongoDB
- [ ] No tokens visible in API responses or frontend
- [ ] User isolation test passes (two users see only their connections)
- [ ] 404 returned for cross-user connection access attempts
- [ ] Backend logs token access operations
- [ ] Frontend handles loading and error states gracefully
- [ ] All manual tests pass on target browser
