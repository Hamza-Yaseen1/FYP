# Research: 007-user-auth

**Date**: 2026-08-21 | **Status**: Complete — no NEEDS CLARIFICATION items
remain. All decisions resolved against the spec, constitution v1.4.0, and
established industry practice.

## R1: Password hashing library

**Decision**: Use the `bcrypt` package directly (`hashpw`, `checkpw`,
`gensalt`) — not passlib.

**Rationale**: The user asked for "bcrypt or passlib". passlib 1.7.4 is
effectively unmaintained (last release 2020) and has a known breakage
with bcrypt ≥ 4.1 (it reads `bcrypt.__about__.__version__`, which was
removed), producing import-time errors/warnings. Calling bcrypt directly
is two functions for our needs (hash, verify) — Simplicity First. Cost
factor stays at the library default (12).

**Alternatives considered**:
- `passlib[bcrypt]` with pinned `bcrypt==4.0.1`: works but pins an old
  dependency and adds a wrapper layer we don't need.
- `argon2-cffi`: stronger memory-hardness, but constitution names
  "bcrypt (or argon2id)" and bcrypt is the simpler, more familiar choice
  for a university FYP demo.
- Hand-rolled PBKDF2 via hashlib: rejected — never roll your own crypto
  parameter management.

## R2: JWT library

**Decision**: `PyJWT` (HS256 tokens).

**Rationale**: Actively maintained, minimal API (`encode`/`decode` with
algorithms + secret), no known recent CVEs. python-jose has had security
advisories and slower maintenance; authlib is larger than needed.

**Alternatives considered**:
- `python-jose`: CVE history (2022-…), maintenance concerns.
- `authlib`: full OAuth/OIDC framework — overkill; violates Simplicity
  First.
- Opaque session tokens in a `sessions` collection: viable and simple,
  but the constitution already mandates "JWT-based with secure cookie
  storage"; stateless JWT avoids a DB round-trip per request.

## R3: Token delivery & session strategy

**Decision**: JWT in an httpOnly, SameSite=Lax, Secure (in prod)
cookie named `cai_token`; 7-day expiry; `sub` = user id string.

**Rationale**: Constitution mandates secure-cookie storage — httpOnly
keeps the token out of reach of XSS; SameSite=Lax fits our same-site
dev setup (localhost:3000 → localhost:8000 share the `localhost` site;
cookies ignore ports) while giving basic CSRF resistance. CORS already
sends `allow_credentials=True` with an explicit origin allowlist.
Frontend never touches the token; it just sends cookies
(`credentials: "include"`).

**Alternatives considered**:
- localStorage + Authorization header: vulnerable to XSS token theft;
  rejected by constitution.
- Short-lived access + refresh token rotation: real-world best practice
  but adds a refresh endpoint and state — out of scope for FYP
  (documented as future hardening).
- Next.js `next-auth`/Auth.js: would work, but adds a library and its
  own session model on top of an existing FastAPI backend that must
  authorize every request anyway; two sources of truth.

## R4: Route protection split (Next.js middleware vs FastAPI)

**Decision**: Two layers, each doing only what it can verify:
- `app/middleware.ts` (edge): checks cookie PRESENCE for protected page
  paths → redirect to `/login`. Presence-only; signature verification
  happens server-side.
- FastAPI `get_current_user` dependency: full JWT verification +
  user lookup on EVERY data request → 401 on any failure.

**Rationale**: Middleware cannot be trusted for authorization (edge
runtime, presence check only) but gives instant UX redirects without a
server round-trip. Real enforcement lives where the data lives —
constitution §Core Security rule 3 ("hiding UI elements alone is never
sufficient"). This matches spec FR-010/FR-011 exactly.

**Alternatives considered**:
- Verifying JWT inside middleware: requires shipping the secret to the
  edge runtime env and duplicating decode logic; unnecessary since all
  data endpoints verify anyway.
- Client-side-only guards: rejected — cosmetic only.

## R5: Email validation & uniqueness

**Decision**: Pydantic `EmailStr` (adds `email-validator` dep) +
lowercase normalization before storage/lookup + MongoDB unique index on
`users.email` created at app startup.

**Rationale**: EmailStr gives standards-based format validation for one
small dependency. Normalizing casing prevents "Ali@x.com" vs
"ali@x.com" duplicates (spec edge case). A DB-level unique index is the
only race-proof guarantee for concurrent duplicate signups (spec edge
case); the pre-check exists purely to return a friendlier 409.

**Alternatives considered**:
- Regex validation: weaker, reinvents RFC logic.
- Case-sensitive emails: rejected — spec requires normalization.

## R6: Ownership of incoming messages (webhooks/simulate)

**Decision**: In Week 3, `POST /messages` (simulate) and the webhook
route REQUIRE an authenticated session; the message's `user_id` is the
authenticated account. Explicit documented decision per constitution
§What Must Be Protected ("none may be silently left open").

**Rationale**: For the FYP demo, messages are simulated by the logged-in
user, so ownership is unambiguous and no channel-identity mapping is
needed yet. True multi-channel inbound mapping (WhatsApp number → user)
is future scope when real integrations land.

**Alternatives considered**:
- Per-user webhook secrets in URL: reasonable production pattern, but
  adds secret management with zero demo value now.
- Unauthenticated webhooks with a default user: violates isolation
  rules; rejected outright.

## R7: Legacy single-user data

**Decision**: One-off script `backend/scripts/assign_legacy_data.py`
that sets `user_id` on all ownerless `messages`/`tasks` docs to a given
email's account. Run once after registering the first real account (or
skip and delete legacy docs — developer's choice, both allowed by spec
Assumptions).

**Rationale**: Spec assumption says legacy data is assigned to the first
account or cleared; a script makes this a 30-second decision instead of
manual Mongo shell edits. Ownerless docs are invisible to all queries
once scoping ships (every query filters by `user_id`), so there is no
leak risk either way.

**Alternatives considered**:
- Auto-assign to first registered user inside register endpoint:
  hidden magic in a hot path; explicit script is clearer.
- Leave ownerless forever: dead data; confusing during demos.

## R8: Backend test tooling

**Decision**: `pytest` + `httpx` (FastAPI TestClient) with a dedicated
test database (`communication_ai_test`), fixture-created via the same
Motor client; unique-index creation invoked in test setup.

**Rationale**: Constitution requires unit tests for business logic and
integration tests for API endpoints. TestClient needs httpx installed.
A separate test DB keeps the demo database pristine and makes isolation
tests deterministic (register A and B, assert cross-access = 404).

**Alternatives considered**:
- mongomock: does not faithfully reproduce Motor's async behavior or
  index semantics; real ephemeral Mongo is more honest.
- No tests: violates constitution Quality Bar.
