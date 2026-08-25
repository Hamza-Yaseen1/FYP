# Tasks: Connection Architecture

**Input**: Design documents from `/specs/010-connection-architecture/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), data-model.md, contracts/

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/src/` for source, `backend/tests/` for tests
- **Frontend**: `frontend/` for Next.js app

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 [P] Create backend directory structure per implementation plan (backend/src/models, backend/src/services, backend/src/routes, backend/src/utils, backend/tests/unit, backend/tests/integration)
- [x] T002 [P] Create frontend directory structure per implementation plan (frontend/app/(dashboard)/connections, frontend/components/connections, frontend/lib/api)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 Create Connection Pydantic model in backend/src/models/connection.py with fields: user_id, provider, status, accessToken, refreshToken, createdAt, updatedAt
- [x] T004 [P] Create encryption utility in backend/src/utils/encryption.py with AES-256 encrypt/decrypt functions
- [x] T005 [P] Add ENCRYPTION_KEY environment variable to backend/.env.example
- [x] T006 Create MongoDB indexes for connections collection (compound index on user_id+provider, single index on user_id)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - View Connected Accounts (Priority: P1) 🎯 MVP

**Goal**: Users can see all their connected external accounts on a single page

**Independent Test**: Navigate to `/connections` and verify the page displays a list of available providers with their connection statuses

### Implementation for User Story 1

- [x] T007 [P] [US1] Create ConnectionService read operations in backend/src/services/connection.py (get_user_connections, get_connection_by_id)
- [x] T008 [P] [US1] Create GET /connections API endpoint in backend/src/routes/connections.py (list user's connections, exclude tokens)
- [x] T009 [P] [US1] Create API client for connections in frontend/lib/api/connections.ts (getConnections function, Connection type)
- [x] T010 [P] [US1] Create ConnectionCard component in frontend/components/connections/ConnectionCard.tsx (display provider, status, coming soon label)
- [x] T011 [US1] Create ConnectionList component in frontend/components/connections/ConnectionList.tsx (render list of ConnectionCard, handle empty state)
- [x] T012 [US1] Create Connections page in frontend/app/(dashboard)/connections/page.tsx (fetch connections, render ConnectionList, handle auth redirect)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Connect a New Account (Priority: P2)

**Goal**: Users can connect external accounts (WhatsApp, Gmail) via OAuth flow

**Independent Test**: Click "Connect" on a provider, complete the OAuth flow (mocked), and verify the connection status changes to "Connected"

### Implementation for User Story 2

- [x] T013 [P] [US2] Create ConnectionService create operations in backend/src/services/connection.py (create_connection, encrypt_tokens)
- [x] T014 [P] [US2] Create POST /connections API endpoint in backend/src/routes/connections.py (create connection, validate provider, check duplicates)
- [x] T015 [US2] Add connect button to ConnectionCard component in frontend/components/connections/ConnectionCard.tsx (handle click, loading state)
- [x] T016 [US2] Add createConnection function to API client in frontend/lib/api/connections.ts
- [x] T017 [US2] Implement mock OAuth flow handling in backend (for FYP demo purposes)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Disconnect an Account (Priority: P3)

**Goal**: Users can disconnect existing accounts with confirmation

**Independent Test**: Click "Disconnect" on a connected account, confirm the action, and verify the status changes to "Disconnected"

### Implementation for User Story 3

- [x] T018 [P] [US3] Create ConnectionService delete operations in backend/src/services/connection.py (delete_connection, verify_user_ownership)
- [x] T019 [P] [US3] Create DELETE /connections/{id} API endpoint in backend/src/routes/connections.py (delete connection, verify ownership, return 404 for cross-user)
- [x] T020 [US3] Add disconnect button with confirmation dialog to ConnectionCard component in frontend/components/connections/ConnectionCard.tsx
- [x] T021 [US3] Add deleteConnection function to API client in frontend/lib/api/connections.ts

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Security verification and user isolation testing

- [x] T022 Verify token encryption: create connection, check database has encrypted tokens (no plaintext)
- [x] T023 Verify API responses never contain accessToken or refreshToken fields
- [x] T024 Verify user isolation: User A cannot see User B's connections through UI or API
- [x] T025 Verify 404 semantics: requesting another user's connection by ID returns 404
- [x] T026 Add error handling for connection failures with user-friendly messages
- [x] T027 Add logging for token access operations (create, read, delete)
- [x] T028 Run quickstart.md validation to verify setup works end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User Story 1 (P1) can start first
  - User Story 2 (P2) can start after US1 (uses same ConnectionCard component)
  - User Story 3 (P3) can start after US1 (uses same ConnectionCard component)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Builds on US1's ConnectionCard component
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Builds on US1's ConnectionCard component

### Within Each User Story

- Models before services
- Services before endpoints
- Endpoints before frontend components
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1 tasks can start
- US2 and US3 can be worked on in parallel after US1 is complete
- All tasks marked [P] within a story can run in parallel

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2 (after US1 component ready)
   - Developer C: User Story 3 (after US1 component ready)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- Security is critical: never expose tokens, always filter by user_id
