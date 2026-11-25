# 09 — Security & Privacy

> What Sift does to protect accounts and data, and where the limits are. Written to be honest — a viva examiner will probe the weak spots, so they are listed here too.

---

## 1. Security summary (at a glance)

| Area | Mechanism | Status |
|------|-----------|--------|
| Passwords | bcrypt hashing | ✅ |
| Sessions | HS256 JWT in httpOnly cookie | ✅ |
| Password reset | SHA-256-hashed, single-use, 30-min token | ✅ |
| Multi-tenant isolation | `user_id` scoping on every query | ✅ |
| OAuth token storage | AES encryption | ✅ |
| WhatsApp webhook | HMAC-SHA256 signature, constant-time compare | ✅ |
| OAuth CSRF | Signed short-lived `state` JWT | ✅ |
| AI failure safety | Pending + retry, no silent wrong answers | ✅ |
| Secrets | Backend-only env vars, never sent to browser | ✅ |
| Transport | HTTPS (Vercel) + Secure cookies | ✅ |
| Rate limiting | Partial (password-reset cooldown only) | 🟡 |
| Account deletion | Manual by email | 🟡 |
| Gmail scope verification | Not completed | ❌ |

---

## 2. Authentication & sessions

### Passwords
- Hashed with **bcrypt** (`services/security.py`). Plaintext is never stored or logged.
- Minimum 8 characters (enforced client-side; reset also caps at 72 — bcrypt's limit).

### Sessions
- A **JWT (HS256)** is issued on login/register and stored in the cookie `cai_token`.
- Cookie is **httpOnly** (JavaScript cannot read it), **Secure** (HTTPS only) in production, and **SameSite** configurable (`COOKIE_SAMESITE`; `None` forces `Secure`).
- Expiry: **7 days** (`TOKEN_EXPIRY_DAYS`).
- `decode_token` **rejects any token that carries a `purpose` claim** — this prevents a password-reset token or a WebSocket token from ever being used as a session.

### Logout
- `POST /auth/logout` clears the cookie; the Next route also clears it even if the backend is unreachable.
- **Limitation:** JWTs are stateless — a copied token stays valid until expiry. There is no server-side revocation list.

---

## 3. Password reset security

- A random token is generated; **only its SHA-256 hash is stored**.
- Token is **single-use** and expires in **30 minutes** (`RESET_TOKEN_TTL_MINUTES`).
- A **60-second cooldown** prevents email flooding; a second request within the window reuses the original token and sends no new email.
- The API always returns a **generic response**, so an attacker can't tell whether an email is registered (no account enumeration).
- Delivery is via Brevo; the API key stays on the backend.

---

## 4. Multi-tenant data isolation

This is the single most important security property.

- The owner id **always** comes from `get_current_user` (the session), never from the request body or query string.
- Every Mongo query and aggregation is scoped by `user_id`; aggregations put `user_id` as the **first `$match`**.
- Cross-user access returns **404** (not 403), so attackers cannot probe which ids exist.
- Verified by the security test suite:
  - Cross-user `GET`/`DELETE` → 404.
  - Analytics never aggregates across users.
  - Lists never include another user's documents.
  - The same `external_message_id` for two users is treated independently.

---

## 5. OAuth and third-party security

### Gmail
- Only `gmail.readonly`.
- OAuth `state` is a signed, 10-minute, user-bound JWT → prevents CSRF and cross-user token attachment.
- Access and refresh tokens are **AES-encrypted** before storage.
- Disconnect **revokes at Google first**, then deletes locally.
- The callback is public by necessity but safe because identity is proven by the signed state.

### WhatsApp webhook
- The raw request body is verified against the **`X-Hub-Signature-256`** HMAC (SHA-256) using `WHATSAPP_APP_SECRET`.
- Comparison is **constant-time**.
- Missing/empty/malformed signature → **403**.
- Verification-challenge handshake uses `WHATSAPP_VERIFY_TOKEN`.
- Key rotation is safe (signature is recomputed from the current secret).

### WebSocket
- Auth via the session cookie on the handshake.
- A **dev-only** `?token=` path exists (gated by `WS_ALLOW_QUERY_TOKEN`), using a 120-second `purpose="ws"` token; it is off in production.
- Fan-out is strictly per-user.

---

## 6. Secret management

- All API keys live in **backend environment variables** and are never exposed via `NEXT_PUBLIC_*`.
- `JWT_SECRET` and `ENCRYPTION_KEY` are required; the code raises if `JWT_SECRET` is missing.
- Frontend only ever sees `NEXT_PUBLIC_API_BASE` (a path, not a secret) and optional WS config.
- These docs intentionally contain **no** real keys, tokens, or personal data.

---

## 7. AI-specific safety

- **No silent wrong answers:** a failed analysis is stored as `status="pending"` and shown as "Pending", not as "Normal 0%".
- **Retry sweep** re-runs failed analyses, user-scoped and idempotent.
- **Circuit breaker** stops hammering the AI provider during a quota lockout.
- **Context safety:** only **verbatim** context updates from a provable source are accepted ("0 tolerance for unlabelled influence").
- **Assistant safety:**
  - LLM output for intent detection is restricted to a **whitelist** of info-intent keys.
  - Conversational history injected into prompts is **text-only** — no DB data, no user ids, no other users.
  - Destructive assistant actions require a **signed, 2-minute confirmation token**.
  - The assistant **never** touches the message AI pipeline.
- **Prompt-injection posture:** user content can influence the AI's *outputs* (that's the point), but cannot cause privileged actions — all actions are deterministic and confirmed.

---

## 8. Privacy posture

| Topic | What Sift does |
|-------|----------------|
| Data collected | Account info; message content/metadata from connected sources; AI analysis results. |
| Why | To classify, summarise, and extract tasks from messages. |
| Who processes it | Google (OAuth/Gmail), Groq (LLM inference), Brevo (reset emails), MongoDB Atlas (storage), Vercel (hosting), Meta (WhatsApp webhook). |
| Message content sent to AI? | **Yes** — message content and metadata are sent to Groq for analysis. This is disclosed in the Privacy Policy. |
| Google data use | Only to fetch and display the user's mail; not sold or shared beyond processing. |
| Trackers/ads | **None.** No third-party analytics scripts, no advertising. |
| Cookies | One functional auth cookie (`cai_token`) + a theme preference in localStorage. |
| Retention | No automated expiry in code; Atlas-configured. **Unresolved in legal docs.** |
| User rights | Access/correction via the app; deletion by emailing the contact address. |
| Children | Not intended for children (see `15_FINDINGS_AND_GAPS.md` — age threshold is a placeholder). |

The Privacy Policy (`app/privacy/page.tsx`) and Terms (`app/terms/page.tsx`) both carry an explicit **"review notes"** callout listing the facts that still need legal confirmation.

---

## 9. Known weaknesses & limitations (be honest in the viva)

1. **No rate limiting** on login/register (only password-reset has a cooldown). Brute-force protection is absent.
2. **Stateless JWTs** can't be revoked before expiry (no logout-everywhere).
3. **No email verification** on sign-up.
4. **Gmail restricted-scope verification not done** — not production-approved for public users.
5. **In-memory assistant context** is lost on restart and not shared across instances.
6. **In-process background loops** — a single backend instance is assumed; WebSocket fan-out won't cross instances.
7. **No automated retention/backup policy** in code.
8. **Temporary `BulkTestButton`** ships a test endpoint surface.
9. **Security headers** (CSP, HSTS, etc.) are not explicitly configured in the app.
10. **No runtime penetration test** was performed; security claims are code-verified only.

---

## 10. Compliance-adjacent notes

- The Privacy Policy references GDPR-style user rights, but the app's actual data subject request process is "email us".
- If Sift were made public with Gmail access, it would likely need: Google verification + CASA, a documented DPA with subprocessors, a defined retention schedule, and possibly a DPIA.
- None of these are implemented; they are listed as future work.
