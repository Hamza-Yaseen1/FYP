# Research: Real WhatsApp Webhook Ingestion

**Feature**: 014-whatsapp-webhook
**Date**: 2026-08-28
**Phase**: 0 (Research)

## 1. Problem Definition

Day 22 delivered webhook *verification* (GET challenge-response) but the POST
handler still expects the fake simulated payload `{sender, message,
timestamp}` and authenticates via the browser JWT cookie. A real WhatsApp
message cannot work against that endpoint because:

| Concern | Meta reality | Current backend |
|---|---|---|
| Authentication | No cookies allowed; delivery is signed with `X-Hub-Signature-256` (App Secret) | Requires JWT via `get_current_user` → would 401 every real delivery |
| Payload shape | Deeply nested `entry[].changes[].value.messages[]` | Flat `{sender, message}` |
| Message ID | Provider-supplied `wamid.*` for dedup | No provider ID stored |
| Timestamp | Unix epoch seconds | ISO string |
| Message types | text, image, audio, document, video, sticker... | text only |
| Retries | Meta redelivers acknowledged-only-as-200; duplicates possible | Time-window fuzzy dedup |

## 2. How Meta Delivers Messages

1. The business number receives a WhatsApp message from a customer.
2. Meta POSTs the whole webhook body to the subscribed callback URL
   (`/webhooks/whatsapp`), signed with `X-Hub-Signature-256`.
3. The body has a fixed skeleton (documented fully in
   `specs/013-whatsapp-business/research.md` §7):
   `object` → `entry[]` → `changes[]` → `value` → `metadata`,
   `contacts[]`, `messages[]` or `statuses[]`. Events without `messages[]`
   (status updates, `field != "messages"`) must be acknowledged but are
   irrelevant to ingestion.
4. If the endpoint does not return 200 quickly, Meta retries with
   exponential backoff for up to 24h. **Respond-fast is therefore a correctness
   requirement, not an optimization.**
5. Each inbound message `message.id` (e.g. `wamid.HBgz…`) is globally unique —
   the correct idempotency key.

## 3. Decisions

### 3.1 Signature-first validation

**Decision**: Verify `X-Hub-Signature-256` before reading anything else; 403
on missing/invalid.

```python
expected = hmac.new(APP_SECRET.encode(), raw_body, hashlib.sha256).hexdigest()
provided = request.headers.get("X-Hub-Signature-256", "").removeprefix("sha256=")
hmac.compare_digest(expected, provided)  # constant-time
```

- Requires `WHATSAPP_APP_SECRET` — a NEW env var (the 013 setup collected the
  Phone Number ID, WABA ID, Access Token, and Verify Token but not the App
  Secret). Found in Meta portal → App Settings → Basic.
- **Alternatives rejected**:
  - JWT: Meta cannot send cookies (constitution Day 22 / Day 23).
  - IP allowlist: Meta's ranges change; signature is the documented mechanism.
  - Trusting `verify_token`: that secret is for the GET handshake only; Meta
    does not send it on deliveries.

### 3.2 Parse-then-normalize at a single boundary

**Decision**: One Pydantic model for the Meta envelope, one shared
`ingest_message()` in `backend/services/webhook_ingest.py`. Route handlers
contain no schema knowledge of channels.

Mapping (Meta field → normalized field):

| Normalized | Meta source | Notes |
|---|---|---|
| `source` | — (constant) | `"whatsapp"` |
| `sender` | `contacts[0].profile.name` fallback `messages[0].from` | Wa display name preferred; wa_id if unnamed |
| `content` | `messages[0].text.body` | Empty string for media types |
| `message_type` | `messages[0].type` | `"text"` if type is `text`; else `"media"` |
| `external_message_id` | `messages[0].id` | Idempotency key |
| `received_at` | — (server now UTC) | We never trust client timestamps; Meta's `timestamp` might equal it, verify on real data |

- `message_type` collapses ALL non-text types to `"media"` per spec FR-007 and
  SC-006. Media content is not downloaded in this feature.
- Only `message.text.body` is read; a bare `text.body` access never happens
  inside ingestion (defensive accessor returns `""` for `type != "text"`).

### 3.3 Idempotence via partial unique index

**Decision**: Unique index on `messages.external_message_id` filtered to
string values; catch `DuplicateKeyError` → return the existing message id and
skip re-insertion/re-analysis.

**Why the index over a query-first check**: Index enforces uniqueness
atomically even under concurrent redeliveries. The existing
`DUPLICATE_WINDOW = timedelta(minutes=10)` heuristic in `webhooks.py` is a
content hash of `(sender, message)` with a time window — it is replaced for
WhatsApp because `wamid` is the authoritative key. The partial filter
(`{external_message_id: {$type: "string"}}`) lets legacy/simulate documents
(no such field) coexist without violating uniqueness.

### 3.4 Own-an-empty document: ownership from the connection

**Decision**: `user_id` is resolved server-side from the `connections`
collection (`provider == "whatsapp"`, `status == "connected"`). Additionally,
deliveries whose `metadata.phone_number_id != WHATSAPP_PHONE_NUMBER_ID` are
ignored (they are for another number). If no connected WhatsApp connection
exists, acknowledge the delivery and store nothing.

Why connections, not the payload: the payload carries no owner identity, and
resolving from `from` (wa_id) would require a contacts registry we do not
maintain. The connections collection is the app's own mapping (Day 19
architecture) and keeps payload-driven identity impossible.

**Consequence for tests**: ownership tests register a user, create a connected
whatsapp connection, then send a signed Meta payload — the pre-existing
tests that treated the webhook as "the authenticating user's endpoint" must be
rewritten accordingly.

### 3.5 Background AI pipeline

**Decision**: Return 200 immediately after insert; run
`analyze_message(content, message_id, user_id)` as a FastAPI background task.

- TestClient runs background tasks synchronously after the response, so
  pytest can assert `ai_analysis` is eventually populated.
- Existing `test_ai_analysis.py` expects AI results by polling `/messages` —
  unchanged, because the pipeline itself is untouched.
- If AI is slow, the Dashboard already renders pending analysis
  (Progressive Enhancement, plan §Constitution Check VII).

### 3.6 Simulation must not break

**Decision**: Real payloads are signature-gated with no auth, so the old
authed simulate flow **cannot** keep calling `/webhooks/whatsapp`. A new
authenticated `POST /webhooks/simulate` calls the same `ingest_message()` with
`source="simulate"`, preserving spec US3 parity and the frontend UX with a
one-line change in `SimulateMessage.tsx`.

## 4. Code Inventory (things Day 23 touches)

| Path | Change |
|---|---|
| `backend/routes/webhooks.py` | Keep GET verify; rework POST (sig → parse → ingest); add POST /simulate |
| `backend/services/webhook_ingest.py` | New shared ingestion service |
| `backend/models/message.py` | Add optional `external_message_id`, `received_at` to response |
| `backend/main.py` | Create partial unique index in lifespan |
| `backend/.env`, `backend/.env.example` | Add `WHATSAPP_APP_SECRET` |
| `components/SimulateMessage.tsx` | POST → `/webhooks/simulate` |
| `backend/tests/test_webhooks.py` | New test module |
| `backend/tests/test_auth.py` | `PUBLIC_ROUTES` + 401 assertion → simulate |
| `backend/tests/test_user_isolation.py` | Ownership via connected whatsapp connection |
| `backend/test_attention_pipeline.py` | Dup-guard against signed Meta payload |

## 5. Key Risks / Mitigations

| Risk | Mitigation |
|---|---|
| Missing `WHATSAPP_APP_SECRET` blocks real testing | Env-lint at startup? No — fail soft: signature path returns 403 and logs a dev hint if secret unset |
| Media payloads crash the parser | `message_type` guard; extra unknown fields ignored by Pydantic |
| Meta retries hammer the endpoint | Atomic dedup by `external_message_id` |
| Old tests assume authed flat-POST webhook | Explicit test migration planned (Step 8) |
| ngrok URL changes break the portal subscription | quickstart re-verifies the callback URL before real test |
| `whatsapp_number` env still used by any old path | Kept; unused-by-ingestion, no removal to avoid regressions |

## 6. Open Questions → Handled at Build Time (no blockers)

- Exact shape of media payloads on this demo account: build-time verification
  against live `test` messages; parser tolerates unknowns either way.
- Whether Meta's `timestamp` aligns with server time: we store server UTC
  (`received_at`) regardless — no dependency.

## Summary of Decisions

| Area | Decision | Key Reason |
|---|---|---|
| Auth on delivery | HMAC-SHA256 `X-Hub-Signature-256` verify first | Meta can't send cookies; prevents spoofing |
| New env var | `WHATSAPP_APP_SECRET` | Required to verify signatures |
| Payload handling | Pydantic envelope → shared normalize fn | Source-agnostic ingestion boundary |
| Dedup key | `external_message_id` + partial unique index | Uniqueness under concurrent redelivery |
| Ownership | Server-side from connected whatsapp connection | Payload carries no trusted identity |
| Timing | 200 first, AI in background | Meta retries non-200; keeps ≤10s budget off request path |
| Simulation | New authed `POST /webhooks/simulate` | Keep simulated flow on the same normalized path |
| Media | `message_type="media"`, content empty | Spec FR-007 / SC-006; no download in scope |