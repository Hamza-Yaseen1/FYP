# Data Model: 008-login-route-protection

**Date**: 2026-08-24 | **Schema changes: NONE**

This feature introduces no new collections and no field changes. Existing
entities are documented here as-built because the auth flow consumes them;
the Session Credential is described for the first time in a data-model doc.

## User (exists since 007 — unchanged)

| Field           | Type     | Rules                                                        |
|-----------------|----------|--------------------------------------------------------------|
| `_id`           | ObjectId | Immutable identity; stringified into JWT `sub`               |
| `name`          | string   | Required, trimmed at registration                            |
| `email`         | string   | Required, unique index (`users.email`, created at startup), lowercased |
| `password_hash` | string   | bcrypt hash; NEVER returned, logged, or exposed to the client |
| `created_at`    | datetime | UTC                                                          |

Validation rules enforced server-side via Pydantic models
(`backend/models/user.py`): required fields, email format,
min password length 8. Client mirrors these for UX only; server is
authoritative. No changes planned.

## Session Credential (activated by this feature's flows — no storage)

A signed JWT, never persisted:

| Claim | Value                                        |
|-------|----------------------------------------------|
| `sub` | user id (string)                             |
| `iat` | issued-at UTC                                |
| `exp` | issued-at + 7 days                           |

- Algorithm HS256; secret from `JWT_SECRET` env (startup fails without it).
- Transport: cookie `cai_token` — HttpOnly (script-inaccessible),
  SameSite=Lax, path=/, max-age 7 days. Not stored anywhere else.
- Verification path per request: cookie → signature/expiry check → user
  lookup → 401 on ANY failure (fail closed).
- Logout deletes the cookie; stateless tokens cannot be revoked
  server-side (accepted FYP trade-off; 7-day bound limits exposure).

## Owned Record — Message / Task / Analysis (exist since 007 — unchanged)

Carry `user_id` set server-side at creation from `get_current_user`;
every request-path query filters by it. Cross-user access behaves as
not-found. This feature adds none; isolation is re-verified through the
UI after restyling.

## State Transitions

No entity states change. The only transition map worth recording is the
session lifecycle:

```text
anonymous --register/login--> authenticated (cookie set)
authenticated --refresh/navigate--> authenticated (cookie re-verified)
authenticated --logout / expiry / tamper--> anonymous (cookie cleared or rejected → 401/redirect)
```
