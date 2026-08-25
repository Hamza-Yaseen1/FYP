# Implementation Plan: User Authentication & Multi-User System

**Branch**: `007-user-auth` | **Date**: 2026-08-21 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/007-user-auth/spec.md`

## Summary

Convert Communication AI into a multi-user application. Day 15 delivers
the signup vertical slice: a `/signup` page posting to `POST /auth/register`,
passwords hashed with bcrypt, users stored in MongoDB. Days 16–20 add
login, JWT-in-httpOnly-cookie sessions, route protection (Next.js
middleware + FastAPI dependency), and strict per-user query scoping so
every message/task belongs to exactly one authenticated user.

## Technical Context

**Language/Version**: TypeScript 5 (Next.js 16 App Router, React 19) /
Python 3.x (FastAPI)
**Primary Dependencies**: Tailwind CSS v4 + shadcn-style components,
lucide-react / FastAPI, Motor (async MongoDB), Pydantic; NEW: bcrypt,
PyJWT, email-validator
**Storage**: MongoDB (`communication_ai` DB) — new `users` collection;
existing `messages`, `tasks` collections gain `user_id`
**Testing**: pytest + FastAPI TestClient (backend, added this phase);
manual browser verification (frontend, per constitution)
**Target Platform**: localhost dev (Next.js :3000, FastAPI :8000)
**Project Type**: Web application (monorepo: `app/` frontend, `backend/` API)
**Performance Goals**: Register/login respond < 500ms (excl. network);
bcrypt cost = library default
**Constraints**: Deny-by-default; no plaintext passwords anywhere;
isolation errors return not-found; secrets via `.env` only
**Scale/Scope**: Single-server FYP demo; handful of test users; 4 auth
endpoints; 3 existing route files gain user scoping

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Principle | Status | Notes |
|------|-----------|--------|-------|
| G1 | I. Simplicity First | ✅ PASS | Standard bcrypt + JWT-cookie patterns; no custom crypto, no auth frameworks |
| G2 | II. Vertical Slices | ✅ PASS | Day 15 = complete signup slice (page → endpoint → DB → signed-in state) |
| G3 | III. AI Assistive | ✅ N/A | Pipeline behavior unchanged; ownership metadata only |
| G4 | IV. User Control | ✅ PASS | Logout provided; no auto-actions introduced |
| G5 | V. Security & Privacy | ✅ PASS | This feature IS the principle: hashing, secrets in .env, OWASP-aligned |
| G6 | VI. Clean Code | ✅ PASS | TS frontend / Python backend, typed models, focused functions |
| G7 | VII. Progressive Enhancement | ✅ PASS | Auth failure degrades to login redirect; dashboard logic untouched |
| G8 | Auth & Multi-User §Core Security | ✅ PASS | Deny-by-default allowlist; server-side enforcement (middleware + dependency); fail closed |
| G9 | Auth §User Isolation | ✅ PASS | Server-set `user_id`; every request-path query filtered; cross-user → 404 |
| G10 | Auth §Password Handling | ✅ PASS | bcrypt, ≥8 chars, unique normalized email index, generic login errors |
| G11 | Auth §Protected Surface | ✅ PASS | Protected page/API lists match spec FR-010/011; webhooks get explicit auth decision |
| G12 | Auth §Quality Bar | ✅ PASS | Two-user isolation test + zero-plaintext checks included in testing plan |

**Gate result**: No violations. Complexity Tracking not needed.

## Project Structure

### Documentation (this feature)

```text
specs/007-user-auth/
├── plan.md              # This file
├── research.md          # Phase 0 output: tech decisions
├── data-model.md        # Phase 1 output: entities & indexes
├── quickstart.md        # Phase 1 output: verify-it-works guide
├── contracts/           # Phase 1 output: API contracts
│   └── auth-api.md
├── checklists/
│   └── requirements.md  # Spec quality checklist (done)
└── spec.md              # Feature specification
```

### Source Code (repository root)

```text
backend/
├── main.py                  # UPDATE: include auth router
├── database.py              # UPDATE: users_collection
├── dependencies.py          # NEW: get_current_user (cookie -> user)
├── requirements.txt         # UPDATE: bcrypt, PyJWT, email-validator
├── models/
│   └── user.py              # NEW: UserCreate/UserLogin/UserResponse
├── routes/
│   ├── auth.py              # NEW: register/login/logout/me
│   ├── messages.py          # UPDATE: set user_id, scope queries
│   ├── tasks.py             # UPDATE: scope queries
│   └── webhooks.py          # UPDATE: require auth, stamp user_id
├── services/
│   └── security.py          # NEW: hash/verify password, JWT encode/decode
└── tests/
    └── test_auth.py         # NEW: pytest suite (unit + integration)

app/
├── middleware.ts            # NEW: edge route protection (cookie presence)
├── (auth)/
│   ├── signup/page.tsx      # REWRITE: real registration form
│   └── login/page.tsx       # REWRITE: real login form (Day 16)
├── (dashboard)/dashboard/page.tsx   # UPDATE: redirect target after signup
└── ...

components/
├── MessageList.tsx          # UPDATE: fetch via lib/api helper
├── NeedsAttentionSection.tsx# UPDATE: fetch via lib/api helper
├── SimulateMessage.tsx      # UPDATE: fetch via lib/api helper
└── Navbar.tsx               # UPDATE: user name + logout (Day 19)

lib/
└── api.ts                   # NEW: fetch wrapper (credentials, 401 -> /login)
```

**Structure Decision**: Extend the existing monorepo in place. Auth gets
one backend router + one service module + one shared dependency; the
frontend reuses the existing `(auth)` route group and gains a single
middleware file plus one fetch helper. No new top-level layers.

## Implementation Sequence

### Slice 1 — Day 15: Signup (this plan's DoD)

1. `pip install bcrypt pyjwt email-validator` (backend/requirements.txt)
2. `backend/database.py`: add `users_collection`
3. `backend/models/user.py`: UserCreate (name, email EmailStr, password
   min-length 8), UserResponse (no hash)
4. `backend/services/security.py`: `hash_password`, `verify_password`,
   `create_access_token`, `decode_token` (PyJWT, HS256, `JWT_SECRET`
   from env, 7-day expiry)
5. `backend/routes/auth.py`: `POST /auth/register` — validate, normalize
   email casing, reject duplicates (unique index + pre-check), hash,
   insert, set httpOnly Secure cookie, return user
6. `backend/main.py`: register auth router; startup hook creates unique
   index on `users.email`
7. `lib/api.ts`: fetch wrapper adding `credentials: "include"` and
   central 401 → `/login` redirect
8. `app/(auth)/signup/page.tsx`: form (Name, Email, Password, Confirm),
   client validation mirroring server rules, error display, loading
   state, redirect to `/dashboard` on success
9. `app/middleware.ts`: redirect unauthenticated users away from
   protected paths (cookie presence check only); bounce signed-in users
   away from `/login`//signup`
10. Manual E2E verify (quickstart.md) + pytest for hashing/JWT/register

### Slice 2 — Day 16: Login

11. `POST /auth/login` (generic invalid-credentials error), login page,
    `GET /auth/me`, `POST /auth/logout` (clear cookie)

### Slice 3 — Day 17: Protect the data

12. `backend/dependencies.py`: `get_current_user` (read cookie → decode →
    load user → 401 on any failure)
13. Apply dependency to messages, tasks, webhooks routers; stamp
    `user_id` server-side on writes; filter every read/write by it
14. Update frontend components to use `lib/api.ts`

### Slice 4 — Day 18: Isolation proof

15. Two-user isolation test (pytest + manual): cross-access returns
    not-found; guessed IDs leak nothing; legacy data assignment script

### Slice 5 — Days 19–20: Polish

16. Navbar user chip + logout; session-expiry UX; final compliance review

## Testing Plan

- **Unit (pytest)**: password hash/verify roundtrip (wrong password
  fails); JWT encode/decode roundtrip; expired/tampered token rejected;
  email normalization
- **Integration (pytest + TestClient)**: register success (201, cookie
  set, no hash in response); duplicate email (409); short password
  (422); invalid email (422); missing fields (422); protected endpoint
  without cookie (401); with valid cookie (200, scoped data)
- **Isolation (pytest)**: users A and B; B cannot read/update/delete
  A's message or task by ID (404); B's list endpoints never contain
  A's records
- **Manual (browser)**: full quickstart.md walkthrough per slice;
  back-button after logout; expired-session redirect; UI shows friendly
  errors, never raw exceptions

## Definition of Done — Day 15

- [ ] `POST /auth/register` live: validates, hashes (bcrypt), stores,
      sets session cookie, returns user without hash
- [ ] Duplicate email rejected with clear message (unique index in place)
- [ ] Passwords < 8 chars and mismatched confirm rejected with specific
      field errors; invalid email format rejected
- [ ] `/signup` page functional: four fields, inline validation, loading
      state, auto-signin redirect to `/dashboard`
- [ ] Zero plaintext passwords in DB, responses, logs, or code
- [ ] Unauthenticated visit to a protected page redirects to `/login`
- [ ] pytest suite green (hashing, token, register integration)
- [ ] Manual quickstart walkthrough passed on target browser
- [ ] Existing functionality unaffected (messages/tasks still work)

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

None — all gates pass with the simple standard-pattern approach.
