# API Contract: Authentication (007-user-auth)

Base URL: `http://localhost:8000` | All bodies JSON. Cookie name:
`cai_token` (httpOnly, SameSite=Lax, 7 days). Session cookie required on
all endpoints except the three marked **public**.

## POST /auth/register  (public)

Create an account and establish a session.

**Request**
```json
{ "name": "Hamza Yaseen", "email": "Hamza@Example.com", "password": "s3cretpass" }
```
Server normalizes email to lowercase before storage/uniqueness check.

**Responses**

| Status | When | Body |
|--------|------|------|
| 201 | Created | `UserResponse` + `Set-Cookie: cai_token=…` |
| 409 | Email already registered | `{ "detail": "An account with this email already exists." }` |
| 422 | Validation failed (empty name, bad email format, password < 8 or > 72 chars) | FastAPI detail with per-field messages |
| 500 | Hashing/storage failure | `{ "detail": "Registration failed." }` — no internals |

**201 body**
```json
{
  "id": "665f1a…",
  "name": "Hamza Yaseen",
  "email": "hamza@example.com",
  "created_at": "2026-08-21T10:00:00Z"
}
```
`password_hash` MUST never appear in any response.

## POST /auth/login  (public)

**Request**
```json
{ "email": "hamza@example.com", "password": "s3cretpass" }
```

| Status | When | Body |
|--------|------|------|
| 200 | Credentials valid | `UserResponse` + session cookie |
| 401 | Unknown email OR wrong password — identical response either way | `{ "detail": "Invalid email or password." }` |
| 422 | Malformed payload | FastAPI detail |

## POST /auth/logout

Clear the session cookie.

| Status | Body |
|--------|------|
| 204 | — (`Set-Cookie: cai_token=""; Max-Age=0`) |

## GET /auth/me

Current user's identity from the session cookie alone.

| Status | When | Body |
|--------|------|------|
| 200 | Valid session | `UserResponse` |
| 401 | Missing/expired/invalid/tampered cookie | `{ "detail": "Not authenticated." }` |

## Changes to existing endpoints

All of `/messages`, `/tasks`, webhook/simulate routes now:

1. **Require** a valid session → `401 { "detail": "Not authenticated." }`
   when absent/invalid.
2. **Stamp** `user_id` server-side on every created document.
3. **Scope** every read/update/delete to the authenticated `user_id`;
   documents belonging to other users respond `404` as if nonexistent.

Response shapes are otherwise unchanged from the current API.

## Error model notes

- 401 = no/invalid credentials; 404 = valid credentials, resource not
  owned (never 403 — do not confirm existence); 409 = duplicate email;
  422 = malformed input.
- No stack traces, hashes, tokens, or other users' identifiers in any
  error body.

## Public route allowlist (audited T029)

Exactly three routes are reachable without a session; every other
route under `/auth`, `/messages`, `/tasks`, `/webhooks`, and
`/health` requires `Depends(get_current_user)` (enforced by the
automated audit test `TestAuthCoverage`):

| Method | Path |
|--------|------|
| POST | `/auth/register` |
| POST | `/auth/login` |
| GET | `/health` |

Note: logout is cookie-clearing only (FR-008 scope: "in that
browser"). Stateless JWTs remain cryptographically valid until expiry
if copied out of the browser before logout; revocation is explicitly
out of scope for this feature.
