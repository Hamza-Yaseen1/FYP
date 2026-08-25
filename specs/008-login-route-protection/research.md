# Research & Decisions: 008-login-route-protection

**Date**: 2026-08-24 | **Status**: Complete — no NEEDS CLARIFICATION items remain

## R1: What is the actual remaining scope? (code audit)

**Decision**: The Day 16/17 backend and route protection are ALREADY BUILT
and tested; the feature's real work is the auth UI polish plus an
end-to-end verification audit.

**Evidence**:
- `backend/routes/auth.py`: register/login/me/logout all implemented;
  login verifies bcrypt hash, returns user without secret material,
  sets `cai_token` cookie (httpOnly, samesite=lax, path=/).
- `backend/services/security.py`: HS256 JWT (`sub`, `iat`, `exp` 7d),
  `JWT_SECRET` required from env at startup.
- `backend/dependencies.py::get_current_user`: cookie → decode → load
  user → 401 on any failure; applied to `messages`, `tasks`, `webhooks`
  routers; queries filter by `user_id`.
- `middleware.ts`: guards `/dashboard`, `/inbox`, `/tasks`, `/attention`,
  `/connections`, `/settings`; bounces authenticated users from
  `/login`//`signup` to `/dashboard`.
- `backend/tests/test_auth.py`: register contract, security units, login
  contract, isolation, protected surface suites exist.
- Frontend `app/(auth)/login/page.tsx`: functional validation, generic
  error, loading state — but plain light-theme card, no password toggle.

**Rationale**: Planning against reality avoids rebuilding working,
tested code (Simplicity First; constitution DoD #4 "does not break
existing functionality").

**Alternatives considered**: Re-implementing login/protection from
scratch per the spec's framing — rejected: duplicates tested code,
adds regression risk, violates Simplicity First.

## R2: How to apply the dark theme? (auth-only vs global)

**Decision**: Scope dark tokens to the `(auth)` route group by rendering
the auth layout content inside a `<div className="dark">`. The dashboard
keeps its current light theme.

**Rationale**: Tailwind v4 in this repo defines `@custom-variant dark
(&:is(.dark *))` and a full `.dark` token block in `globals.css`
(line 93), so a wrapper div re-themes every descendant with zero new
dependencies or config. The spec's UI requirements target the Login and
Signup pages specifically ("dark theme preferred") while requiring
consistency "with the rest of the dashboard style" — shared components
and palette family provide that consistency regardless of theme mode.
This also honors the plan constraint of not changing working pages.

**Alternatives considered**:
- Global dark mode (`class="dark"` on `<html>`): rejected — changes the
  entire dashboard's appearance, which is outside this feature's scope
  and risks regressions across six untouched pages.
- Hardcoded dark color classes on auth elements only (no token switch):
  rejected — fights the shadcn token system, produces inconsistent
  hover/focus/border states, more classes to maintain.
- next-themes package for toggling: rejected — adds a dependency for a
  feature with no user-facing theme toggle requirement.

## R3: Password visibility toggle pattern

**Decision**: One small client component
`components/auth/password-input.tsx` wrapping the existing shadcn
`Input`: type switches between `password`/`text`, lucide `Eye`/`EyeOff`
icon button inside the field with `aria-label="Show password" /
"Hide password"`, `tabIndex` in natural order.

**Rationale**: Required by FR-017; both pages share it (FR-015/016);
pure composition of installed primitives — zero dependencies.

**Alternatives considered**: Inline duplicate logic in each page —
rejected: violates the consistency rule and duplicates code.

## R4: Session mechanism confirmation

**Decision**: Keep the as-built mechanism exactly as-is: HS256 JWT with
7-day expiry containing `sub` (user id), delivered in httpOnly
SameSite=Lax cookie `cai_token`; no refresh-token rotation, no sliding
expiry.

**Rationale**: Satisfies FR-003 (signed, expiry-bounded, script-
inaccessible, survives refresh), matches the constitution's "JWT-based
with secure cookie storage", and is already covered by passing tests.
The spec explicitly defers scheme details to planning; planning confirms
no change is warranted for an FYP demo scope. Cookie `secure=True` is
correctly off for localhost HTTP today; enabling it belongs to
deployment hardening, noted in quickstart as a production checklist item.

**Alternatives considered**:
- Refresh-token pair: rejected — meaningful added complexity with no FYP
  requirement (Out of Scope: configurable lifetimes).
- Server-side session store: rejected — replaces stateless JWT the
  constitution names, extra collection + lookups per request.

## R5: Testing strategy for the restyled frontend

**Decision**: No component-test framework introduced. Backend stays
protected by its pytest suites (must remain green untouched); the
restyled UI is verified through lint/typecheck plus the manual AC matrix
in quickstart.md (responsive widths + keyboard pass included).

**Rationale**: Constitution testing expectations: unit/integration tests
required for business logic (already exist server-side), E2E optional
for FYP, manual testing mandatory for UI changes — exactly what the
quickstart provides. Adding Vitest/Playwright now would violate
Simplicity First for one restyle slice.

**Alternatives considered**: Playwright E2E suite — rejected for this
phase (dependency + CI weight); revisit if Week 4 adds flows.

## R6: Backend test extension criteria

**Decision**: Extend `tests/test_auth.py` ONLY if the verification
audit finds an untested failure path. Pre-identified candidates checked
during audit: malformed JSON body on login (expect 401/422 handled
gracefully, never 500), login response shape contains no
`password_hash`, logout requires authentication.

**Rationale**: Keeps test work proportional to risk; existing suites
already cover contracts, isolation, and protected surface.
