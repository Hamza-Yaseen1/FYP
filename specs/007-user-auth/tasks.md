---
description: "Task list for 007-user-auth — Week 3 Authentication & Multi-User System"
---

# Tasks: User Authentication & Multi-User System

**Input**: Design documents from `/specs/007-user-auth/`
**Prerequisites**: plan.md ✅ | spec.md ✅ | research.md ✅ | data-model.md ✅ | contracts/auth-api.md ✅ | quickstart.md ✅

**Tests**: INCLUDED — required by constitution Quality Bar (unit tests for
business logic, integration tests for API endpoints) and by plan.md's
testing strategy (pytest + httpx against `communication_ai_test` DB).
Test tasks are written FIRST within each story and must FAIL before
implementation.

**Organization**: Tasks grouped by user story from spec.md.
US1 Signup (P1) is Day 15 and ships first as the MVP slice.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US4)
- Include exact file paths in descriptions

## Path Conventions

This repo uses its existing monorepo layout (per plan.md):

- **Backend**: `backend/` (FastAPI + Motor, flat modules)
- **Frontend**: `app/` (Next.js App Router), `components/`, `lib/`
- **Tests**: `backend/tests/` (new directory this feature)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Dependencies and secrets needed before any auth code runs

- [x] T001 Append `bcrypt`, `PyJWT`, and `email-validator` to
      `backend/requirements.txt`; append `pytest` and `httpx` under a
      `# dev/test` comment; run `pip install -r backend/requirements.txt`
- [x] T002 [P] Generate a strong secret (`python -c "import secrets; print(secrets.token_hex(32))"`)
      and add `JWT_SECRET=<value>` to `backend/.env`; document the key in
      `backend/.env.example` with an empty value

**Checkpoint**: Environment ready — imports work, secret available

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared building blocks every user story depends on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 Expose `users_collection = db["users"]` in `backend/database.py`
- [x] T004 Create `backend/services/security.py` with four functions:
      `hash_password(plain) -> str` (bcrypt `gensalt()` default cost),
      `verify_password(plain, hashed) -> bool`, `create_access_token(user_id) -> str`
      (PyJWT HS256, claims `sub=str(user_id)`, `iat`, `exp=iat+7d`,
      secret from `JWT_SECRET` env), `decode_token(token) -> str | None`
      (returns user_id or None on ANY failure); load `JWT_SECRET` via
      `os.getenv` with startup assertion that it is set
- [x] T005 [P] Create `lib/api.ts`: typed fetch wrapper exporting
      `apiFetch(path, options)` that prefixes `http://localhost:8000`,
      sets `credentials: "include"` and `Content-Type: application/json`,
      parses JSON error bodies into thrown `ApiError {status, message}`,
      and redirects to `/login` via `window.location.assign("/login")`
      when status === 401

**Checkpoint**: Foundation ready — hashing, tokens, users collection,
and frontend fetch path all exist

---

## Phase 3: User Story 1 — Sign Up for an Account (Priority: P1) 🎯 MVP · Day 15

**Goal**: A visitor registers via `/signup`, the password is bcrypt-hashed
into MongoDB `users`, and they land signed-in on `/dashboard`. Unauthenticated
visitors cannot open workspace pages.

**Independent Test**: Submit valid details on `/signup` → account created
(hash-only in DB), session cookie set, redirect to `/dashboard`; invalid
submissions rejected with specific field errors; duplicate email rejected;
direct visits to `/dashboard` while logged out redirect to `/login`.

### Tests for User Story 1 (write FIRST, must FAIL) ⚠️

- [x] T006 [US1] Create `backend/tests/test_auth.py` with TestClient
      fixtures (separate `communication_ai_test` DB, unique-index setup)
      and FAILING contract tests for `POST /auth/register`: 201 with
      `Set-Cookie: cai_token` + body WITHOUT `password_hash`; 409 on
      duplicate email; 409 on same email different casing; 422 on
      password shorter than 8 chars; 422 on malformed email; 422 on
      missing fields
- [x] T007 [US1] Add FAILING unit tests to `backend/tests/test_auth.py`
      for `backend/services/security.py`: hash/verify roundtrip passes
      with correct password and fails with wrong password; two hashes of
      the same password differ (salted); token encode/decode roundtrip
      returns the user_id; tampered signature returns None; expired
      token returns None

### Implementation for User Story 1

- [x] T008 [US1] Create `backend/models/user.py`: `UserCreate(name: str
      min_length 1, email: EmailStr, password: str min_length 8
      max_length 72)`, `UserLogin(email: EmailStr, password: str)`,
      `UserResponse(id, name, email, created_at)` (no hash field), and
      `user_doc_to_response(doc)` mapping `_id → id`
- [x] T009 [US1] Implement `POST /auth/register` in
      `backend/routes/auth.py`: accept `UserCreate`, normalize
      `email.lower().strip()`, pre-check duplicates → HTTPException 409
      "An account with this email already exists.", insert doc with
      `hash_password(password)` and UTC `created_at`, issue token via
      `create_access_token`, set cookie `cai_token` (httponly=True,
      samesite="lax", secure=False for localhost dev, max_age=604800,
      path="/"), return 201 `UserResponse`

      **AC**: response body contains id/name/email/created_at and NO
      password material; cookie flags exactly as above; second register
      with same normalized email returns 409
- [x] T010 [US1] Update `backend/main.py`: include the auth router and
      add a startup hook (FastAPI lifespan or `@app.on_event`) that
      calls `users_collection.create_index("email", unique=True)`
- [x] T011 [US1] Run `pytest backend/tests/test_auth.py -q` and make all
      US1 tests pass (fix implementation, never weaken assertions)
- [x] T012 [US1] Rewrite `app/(auth)/signup/page.tsx` as a client form:
      controlled inputs Name/Email/Password/Confirm Password, client
      validation mirroring server rules (all fields present, email
      format, password ≥ 8, confirm matches) shown inline per field,
      submit calls `POST /auth/register` through `lib/api.ts`, loading
      state disables the button, server errors render as a friendly
      alert, success routes to `/dashboard` via next/navigation router

      **AC**: each invalid state shows its specific message without
      network call where client-checkable; valid submission lands on
      `/dashboard` signed-in; raw exceptions never visible
- [x] T013 [US1] Create `app/middleware.ts`: matcher list of protected
      paths (`/dashboard`, `/inbox`, `/tasks`, `/attention`,
      `/connections`, `/settings`); if no `cai_token` cookie → redirect
      `/login`; if cookie present and path is `/login` or `/signup` →
      redirect `/dashboard`. Presence check ONLY (no crypto at edge)

      **AC**: logged-out visit to any protected path lands on `/login`;
      logged-in visit to `/signup` lands on `/dashboard`
- [x] T014 [US1] Execute quickstart.md Slice 1 manually end-to-end and
      tick the Day 15 Definition of Done in plan.md

**Checkpoint**: MVP demoable — signup works end-to-end, Day 15 done

---

## Phase 4: User Story 2 — Log In to My Account (Priority: P2) · Day 16

**Goal**: Returning users log in with email+password; failures return one
generic error; identity endpoint and logout exist.

**Independent Test**: Register, clear cookies, log in with correct
credentials → dashboard with own data; wrong password and unknown email
produce byte-identical 401 bodies.

### Tests for User Story 2 (write FIRST, must FAIL) ⚠️

- [x] T015 [US2] Add FAILING contract tests to
      `backend/tests/test_auth.py`: login 200 + cookie + UserResponse;
      wrong password 401 `{"detail": "Invalid email or password."}`;
      unknown email returns the IDENTICAL status and body; `GET /auth/me`
      200 with registered user then 401 after clearing cookies;
      `POST /auth/logout` clears `cai_token` (Max-Age=0) and subsequent
      `/auth/me` is 401

### Implementation for User Story 2

- [x] T016 [US2] Implement `POST /auth/login` in
      `backend/routes/auth.py`: normalize email, look up user, verify
      with `verify_password`, on failure raise 401 "Invalid email or
      password." for BOTH unknown-email and wrong-password cases, on
      success set the same `cai_token` cookie and return `UserResponse`

      **AC**: identical 401 body/status for both failure modes (test
      asserts equality); successful login sets cookie with same flags
      as register
- [x] T017 [US2] Create `backend/dependencies.py`: FastAPI dependency
      `get_current_user` reading `cai_token` from request cookies,
      decoding via `decode_token`, loading the user from
      `users_collection`, raising 401 "Not authenticated." on missing/
      invalid/expired token or missing user, returning the user doc
- [x] T018 [US2] Implement `GET /auth/me` (depends on
      `get_current_user`, returns `UserResponse`) and `POST /auth/logout`
      (deletes `cai_token` cookie, returns 204) in
      `backend/routes/auth.py`
- [x] T019 [US2] Rewrite `app/(auth)/login/page.tsx` as a client form:
      email+password, inline validation, generic error display for 401,
      loading state, success routes to `/dashboard`
- [x] T020 [US2] Execute quickstart.md Slice 2 manually (wrong password,
      unknown email, correct login, persistence across browser restart)

**Checkpoint**: Users can return — identity lifecycle complete

---

## Phase 5: User Story 3 — Strong User Isolation (Priority: P3) · Days 17–18

**Goal**: Every message/task carries a server-set `user_id`; every query
is owner-scoped; cross-user access behaves as not-found.

**Independent Test**: Two registered users A and B; B sees zero of A's
records in lists AND direct ID-based requests return 404; A's data
unchanged after B's attempts.

### Tests for User Story 3 (write FIRST, must FAIL) ⚠️

- [x] T021 [US3] Add FAILING isolation tests to
      `backend/tests/test_auth.py` (register A and B via API, create a
      message as each): B's `GET /messages` contains none of A's docs;
      `GET /messages/{A_id}` as B → 404; `PUT` and `DELETE` on A's
      message as B → 404 with A's doc unchanged; same assertions for
      `GET /tasks`; new message created via API contains the creator's
      `user_id`

### Implementation for User Story 3

- [x] T022 [US3] Update `backend/routes/messages.py`: add
      `current_user = Depends(get_current_user)` to every route; stamp
      `user_id: str(current_user["_id"])` server-side on create
      (ignoring any client-supplied value); filter reads/updates/deletes
      by `{"_id": oid, "user_id": uid}` so foreign docs yield 404

      **AC**: no route reachable without a valid session; a foreign ID
      is indistinguishable from a nonexistent one (404, empty detail);
      client-sent `user_id` in payload never overrides the session
      identity
- [x] T023 [US3] Update `backend/routes/tasks.py` with the same
      dependency + scoping pattern as messages
- [x] T024 [US3] Update `backend/routes/webhooks.py`: require
      `get_current_user` on message-ingest routes and stamp the
      authenticated `user_id` on ingested messages (documented Week 3
      decision from research.md R6)
- [x] T025 [P] [US3] Switch frontend data fetching to `lib/api.ts` in
      `components/MessageList.tsx`,
      `components/NeedsAttentionSection.tsx`,
      `components/SimulateMessage.tsx`, and
      `app/(dashboard)/dashboard/page.tsx` (tasks fetch), replacing raw
      `fetch("http://localhost:8000/…")` calls so cookies flow and 401s
      redirect
- [x] T026 [US3] Create `backend/scripts/assign_legacy_data.py`: CLI
      taking `--email`, resolving the user, and
      `$set: {user_id}` on ALL documents in `messages` and `tasks` that
      lack `user_id`; prints counts; safe to re-run
- [x] T027 [US3] Execute quickstart.md Slice 4 manually (two browser
      profiles, cross-access attempts, guessed IDs) and run
      `pytest backend/tests/test_auth.py -q` green including isolation

**Checkpoint**: Isolation proven — the highest-stakes guarantee holds

---

## Phase 6: User Story 4 — Protected Access (Priority: P4) · Day 19

**Goal**: The full public/protected surface audit passes; anonymous
access is impossible anywhere; logout leaves no residual access.

**Independent Test**: With cleared cookies, hit every known page URL and
data endpoint → redirect or 401 everywhere; only `/login`, `/signup`,
`/health` respond anonymously.

### Tests for User Story 4 (write FIRST, must FAIL) ⚠️

- [x] T028 [US4] Add FAILING surface tests to
      `backend/tests/test_auth.py`: anonymous GET on `/messages`,
      `/tasks`, `GET /messages/{id}`, `POST /messages`, webhook ingest
      → 401; `GET /health` remains 200 anonymously; after logout,
      replaying the old cookie value still yields 401 on `/auth/me`
      once cookies are cleared client-side (stateless JWT contract)

### Implementation for User Story 4

- [x] T029 [US4] Audit every router in `backend/routes/` against the
      contract: assert each has `Depends(get_current_user)` except the
      public allowlist (`/auth/register`, `/auth/login`, `/health`);
      fix any gaps found and record the final allowlist in
      `specs/007-user-auth/contracts/auth-api.md`
- [x] T030 [US4] Verify post-logout back-button behavior in the browser:
      after logout, navigating Back to `/dashboard` triggers the
      middleware redirect (cookie gone) and any in-flight data call
      401-redirects via `lib/api.ts`; adjust if stale content renders
- [x] T031 [US4] Execute quickstart.md Slice 3 manually and confirm the
      spec SC-003 redirect timing (< 2s) feels instant

**Checkpoint**: Deny-by-default verified across the whole surface

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: UX finishing and governance sign-off

- [x] T032 Add user chip + logout button to `components/Navbar.tsx`:
      fetch `GET /auth/me` on mount via `lib/api.ts`, show name initial
      avatar + name, logout button calls `POST /auth/logout` then
      routes to `/login`
- [x] T033 Verify session-expiry UX: manually expire a token (set
      `exp` in the past with a temporary script or wait), confirm the
      next action redirects to `/login` with no crash and no partial
      private data rendered
- [x] T034 Run the full suite `pytest backend/tests/test_auth.py -q`,
      run `npm run lint` and `npx tsc --noEmit`, then walk the
      constitution v1.4.0 Compliance Review checklist (auth items) and
      record the result in the feature's PR description

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies — start immediately
- **Foundational (Phase 2)**: depends on Phase 1 (needs installed libs +
  JWT_SECRET) — BLOCKS all stories
- **US1 Signup (Phase 3)**: depends on Foundational — Day 15 MVP
- **US2 Login (Phase 4)**: depends on US1 (registered user + shared
  cookie helper patterns)
- **US3 Isolation (Phase 5)**: depends on US2 (`get_current_user` from
  T017) — the scoping work consumes it
- **US4 Protected Access (Phase 6)**: depends on US3 (audits the
  dependency coverage US3 introduced)
- **Polish (Phase 7)**: depends on all stories

### User Story Dependencies

- **US1 (P1)**: independent after Foundational — delivers MVP alone
- **US2 (P2)**: needs US1's users to exist; no other coupling
- **US3 (P3)**: needs US2's `get_current_user`; touches only data routes
- **US4 (P4)**: verification-heavy; audits everything before it

### Within Each Story

1. Tests first (must FAIL)
2. Models/services
3. Endpoints/UI
4. Green tests
5. Manual quickstart checkpoint

### Parallel Opportunities

- T002 (env secret) ∥ T001 (requirements)
- T005 (lib/api.ts) ∥ T003–T004 (backend foundation)
- T025 (frontend fetch switch) ∥ T022–T024 (backend scoping)
- All frontend form work (T012, T019) independent of backend test
  debugging within their phases

---

## Implementation Strategy

### MVP First — Day 15 (US1 only)

1. Phase 1 + Phase 2 → foundation ready
2. Phase 3 (US1) → signup vertical slice
3. STOP and VALIDATE: quickstart Slice 1 + Day 15 DoD
4. Demo-ready: real accounts with hashed passwords

### Incremental Delivery

1. Foundation → US1 → **Day 15 demo** (MVP!)
2. +US2 → returning-user demo (Day 16)
3. +US3 → isolation proof (Days 17–18)
4. +US4 → locked-down surface (Day 19)
5. Polish → compliance sign-off (Day 20)

Each increment leaves the app fully working; no half-wired states.

---

## Notes

- Every task includes its exact file path; paths are relative to repo root
- Tests are mandatory here (constitution Quality Bar) — never delete or
  weaken assertions to go green
- Security invariants that out-rank any task's convenience: no plaintext
  passwords anywhere; identity from session only; cross-user → 404;
  deny-by-default allowlist
- Commit after each task or logical group; stop at every checkpoint to
  validate the story independently
