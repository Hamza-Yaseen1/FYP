# Implementation Plan: Login, Protected Routes & Auth UI Polish

**Branch**: `008-login-route-protection` | **Date**: 2026-08-24 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/008-login-route-protection/spec.md`

## Summary

Complete the Week 3 authentication flow. Audit findings: the Day 16 and
Day 17 **backend already exists and is tested** — `POST /auth/login` (JWT in
httpOnly cookie), `GET /auth/me`, `POST /auth/logout`, bcrypt hashing, and
`get_current_user` enforcement on every data route were delivered during
feature 007's green phases, along with Next.js middleware protecting all six
workspace pages. The genuine remaining work is:

1. **Auth UI polish (the bulk)**: transform `/login` and `/signup` from
   functional-but-plain light pages into a modern dark-theme experience —
   scoped dark palette, gradient backdrop, password visibility toggle,
   refined spacing/typography/focus states — without changing any working
   behavior.
2. **End-to-end verification**: run the full flow (login → own data →
   refresh persistence → protection redirects → logout) against the spec's
   acceptance criteria, closing any gaps found.

Approach follows Simplicity First: zero new dependencies, zero schema
changes, no rebuild of working code.

## Technical Context

**Language/Version**: TypeScript 5.x (Next.js 16.3.1, React 19) / Python 3.13 (FastAPI)
**Primary Dependencies**: Tailwind CSS v4 + shadcn/ui; FastAPI + Motor + bcrypt + PyJWT (all installed)
**Storage**: MongoDB (`users`, `messages`, `tasks` collections; unique index on `users.email`)
**Testing**: pytest + httpx (backend/tests/test_auth.py — register/login/isolation/protected-surface suites exist); ESLint + manual browser verification (frontend)
**Target Platform**: localhost dev (browser + uvicorn); desktop and mobile-width viewports
**Project Type**: Web app — `app/` (Next.js at repo root) + `backend/`
**Performance Goals**: Login request < 2s; page redirect on anonymous access < 2s (per SC-001/SC-002)
**Constraints**: No new npm/pip packages; JWT_SECRET via env only; session = HS256 JWT, 7-day expiry, httpOnly cookie `cai_token`
**Scale/Scope**: 2 screens restyled, ~4 files touched, existing tests extended only where gaps are found

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Evidence |
|------|--------|----------|
| Simplicity First: simplest viable implementation | ✅ PASS | No new deps, no schema changes, reuse of existing endpoints/components; dark theme achieved with one wrapper div using the existing `.dark` token variant |
| Vertical Slices: end-to-end value | ✅ PASS | Each story ships a complete slice: login flow verified end-to-end (US1), protection verified end-to-end (US2), polished pages usable immediately (US3) |
| AI Assistive | ✅ N/A | No AI components touched |
| User Control | ✅ PASS | Logout exists; no automated actions added |
| Security & Privacy: hashed passwords, env secrets, generic errors, deny-by-default | ✅ PASS | bcrypt verify, JWT_SECRET from `.env`, single "Invalid email or password." error, public allowlist enforced by middleware + `get_current_user`; verified in existing test suites |
| Clean Code: TS frontend, PEP8-style Python | ✅ PASS | Follows existing file conventions; no comments unless clarifying |
| Progressive Enhancement | ✅ PASS | Dashboard data flows unchanged; no client-only trust introduced |
| Deny by default / server-side enforcement | ✅ PASS | All routers (`messages`, `tasks`, `webhooks`) require `get_current_user`; middleware guards six prefixes + bounces authed users off auth pages |
| Isolation: user_id filter on every query, ownership before write | ✅ PASS | Existing TestIsolation suite passes; no new collections |
| Auth pages share one dark design with loading/focus/error states | ✅ PLANNED | FR-015..021 → Phase A tasks |
| `POST /auth/login` issues signed HttpOnly JWT cookie; never localStorage | ✅ EXISTS | `backend/services/security.py` + `_set_session_cookie` |
| `GET /auth/me` resolves identity from token only, 401 otherwise | ✅ EXISTS | `backend/routes/auth.py::me` + `dependencies.py` |

**Gate result**: No violations. Complexity Tracking stays empty.

## Project Structure

### Documentation (this feature)

```text
specs/008-login-route-protection/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── auth.yaml        # OpenAPI contract for the auth surface (as-built)
└── tasks.md             # Phase 2 output (/sp.tasks - NOT created here)
```

### Source Code (repository root)

```text
app/
├── (auth)/
│   ├── layout.tsx            # UPDATE: dark wrapper (.dark), gradient backdrop, branding
│   ├── login/page.tsx        # UPDATE: polish — toggle, icons, spacing, focus states
│   └── signup/page.tsx       # UPDATE: parity polish, same system
├── globals.css               # UPDATE (minor): auth-scoped gradient utility if needed
components/
├── auth/
│   └── password-input.tsx    # CREATE: input + visibility toggle (shared by both pages)
├── ui/*                      # EXISTING shadcn primitives — reused, not modified
lib/api.ts                    # EXISTING — unchanged (401 handling already correct)
middleware.ts                 # EXISTING — unchanged (protection already complete)

backend/
├── routes/auth.py            # EXISTING — as-built contract source; change ONLY if audit finds a gap
├── services/security.py      # EXISTING — JWT/bcrypt helpers; no changes planned
├── dependencies.py           # EXISTING — get_current_user; no changes planned
└── tests/test_auth.py        # EXTEND only if the audit reveals an untested failure path
```

**Structure Decision**: Web layout already established in the repo —
Next.js App Router at root (`app/`, `components/`, `lib/`,
`middleware.ts`) with FastAPI under `backend/`. This feature modifies only
the `(auth)` route group and adds one shared component; backend files are
touched solely if the verification audit finds a real gap.

## Implementation Phases (ordered)

### Phase A — Verification Audit of Existing Flow (Day 16/17 backend)

1. Run `pytest` in `backend/` — confirm auth suites green.
2. Walk quickstart.md manually against AC-1…AC-10; log any gap.
3. Fix found gaps (expected: none; budget one small fix, e.g., cookie
   `secure=True` note deferred to deployment).

### Phase B — Auth Pages Dark Theme & Polish (the feature's core work)

1. Create `components/auth/password-input.tsx` (Input + eye toggle,
   aria-label, forwardRef-compatible).
2. Restyle `app/(auth)/layout.tsx`: wrap children in `.dark`, deep neutral
   gradient background, centered column max-w-sm, logo block.
3. Polish `login/page.tsx`: PasswordInput, leading mail/lock icons optional,
   refined spacing/gap scale, button loading spinner, focus-visible rings.
4. Apply identical system to `signup/page.tsx` (behavior frozen).
5. Responsive check at 360px / 768px / 1280px; keyboard pass (tab order,
   Enter submits, toggle reachable).

### Phase C — Definition of Done Sweep

1. `npm run lint` clean; `npx tsc --noEmit` clean; backend pytest green.
2. Manual two-user isolation re-check through the UI.
3. Zero plaintext passwords/tokens in responses or logs (spot check).

## Testing Plan

| Layer | What | How |
|-------|------|-----|
| Backend unit/integration (existing) | register/login/me/logout contracts, isolation, protected surface | `cd backend && pytest tests/test_auth.py -q` — must stay green untouched |
| Backend extension (only if gap found) | e.g., malformed JSON body → 401 not 500 on login | Add case to `TestLoginContract` |
| Frontend static | Types + lint | `npm run lint`, `npx tsc --noEmit` |
| Manual E2E (authoritative for this feature) | Full AC matrix incl. responsive + keyboard | Execute `quickstart.md` step-by-step on Chrome; record results |
| Visual consistency | Both pages side-by-side, same tokens | Manual comparison during Phase B step 5 |

## Definition of Done

1. All 10 acceptance criteria in spec.md verified manually and recorded in
   quickstart checklist.
2. Both auth pages render the shared dark design at 360/768/1280px with
   working focus, disabled, loading, visibility-toggle, and inline error
   states; keyboard operable.
3. Signup behavior byte-for-byte identical to pre-restyle (same requests,
   same validation, same errors).
4. `npm run lint`, `npx tsc --noEmit`, `backend pytest` all green.
5. Two-user isolation re-verified through the UI after changes.
6. Zero new dependencies; zero schema/route/middleware changes unless a
   documented audit gap required one.
7. Code reviewed (self-review acceptable per constitution) against the
   constitution compliance checklist.

## Complexity Tracking

> No constitution violations — table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |
