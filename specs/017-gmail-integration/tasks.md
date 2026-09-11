# Tasks: Day 26 Gmail Integration

**Input**: Design documents from `/specs/017-gmail-integration/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/gmail-oauth-api.md

**Tests**: Included — the user request explicitly lists a "Testing" group, so
each user story phase starts with its tests (written FIRST; must FAIL before
implementation per the template workflow).

**Organization**: Tasks are grouped by user story to enable independent
implementation and testing of each story. Manual Google Cloud setup is
isolated in Phase 1 and marked `(MANUAL)`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions
- `(MANUAL)` = done by a human in the Google Cloud Console, never code

## Grouping Map (per user request)

| Requested group | Where it lives |
|---|---|
| Google Setup | Phase 1 (T001–T002 MANUAL, T003–T004 env/deps) |
| Backend | Phase 2 + backend tasks in US1/US2/US3 |
| Frontend | Frontend tasks in US1/US2/US3 |
| Email Ingestion | Phase 4 (US2) tasks T017–T023 |
| Testing | One test sub-phase per user story (T009–T010, T017–T018, T025) + Phase 6 validation |

## Path Conventions (confirmed in repo)

- Frontend = repo-root Next.js app: `app/`, `components/`, `lib/`
- Backend = `backend/`: `routes/`, `services/`, `models/`, `utils/`, `tests/`
- Single `backend/tests/` suite; run with `pytest` from `backend/`

---

## Phase 1: Setup (Google Cloud MANUAL + env)

**Purpose**: Create the Google OAuth client, wire env vars, add the runtime dep.
**Sub-group**: Google Setup

- [ ] T001 `(MANUAL)` In Google Cloud Console: enable the **Gmail API**, then
  configure the **OAuth consent screen** (User type: External or Test; app
  name "Communication AI FYP"; add your demo Gmail to Test users; add scope
  `https://www.googleapis.com/auth/gmail.readonly`)
  - **Accept**: Consent screen saved with the read-only scope only (no send/modify scopes; spec FR-002, Security rule 2).
- [ ] T002 `(MANUAL)` In Google Cloud Console: **Credentials → Create OAuth
  client ID → Web application** with Authorized redirect URI
  `http://localhost:8000/connections/gmail/callback`; copy Client ID + Secret
  - **Accept**: Redirect URI matches `GOOGLE_REDIRECT_URI` exactly (quickstart.md §Step 1); secret never committed to git.
- [x] T003 Add Google OAuth vars to `backend/.env.example` (documented placeholders)
  and `backend/.env` (real values): `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`,
  `GOOGLE_REDIRECT_URI`, `FRONTEND_URL=http://localhost:3000`,
  `GMAIL_POLL_INTERVAL_SECONDS=30` (contracts §6)
  - **Accept**: Backend starts with all vars resolvable (no `None` OAuth config); FRONTEND_URL already present in CORS.
- [x] T004 [P] Add `httpx` to `backend/requirements.txt` and install it
  (`pip install httpx`)
  - **Accept**: `python -c "import httpx"` succeeds; no other deps added.

**Checkpoint**: Google OAuth client exists; backend can load the Google config.

---

## Phase 2: Foundational (Blocking Prerequisites — Backend shared)

**Purpose**: Token/connection model fields, connection service ops, ingest
extension, and the gmail provider guard that ALL three user stories build on.
**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T005 [P] Extend `backend/models/connection.py`: add optional
  `token_expires_at`, `last_fetched_at`, `gmail_email` to `ConnectionInDB`
  and surface `gmail_email` in the public response mapping (tokens stay
  response-excluded; data-model.md §2, §6)
- [x] T006 [P] Extend `backend/services/connection.py`: add
  `upsert_gmail_connection(user_id, access_token, refresh_token, token_expires_at, gmail_email)`,
  `update_gmail_tokens(connection_id, user_id, ...)`,
  `set_connection_error(connection_id, user_id)`; all user-scoped
  (data-model.md §2, §7)
- [x] T007 [P] Extend `backend/services/webhook_ingest.py::ingest_message`:
  add `subject: Optional[str] = None` (stored when present) and, when
  `background_tasks is None`, spawn `asyncio.create_task(_analyze_and_store, ...)`
  keeping refs in a module-level set (data-model.md §4; research §6)
- [x] T008 [P] Guard `provider: "gmail"` in `backend/routes/connections.py`
  `POST /connections` → `400 {"detail": "Use the Gmail connect flow"}` so no
  mock-token Gmail rows are ever created (data-model.md §2 "Provider guard")

**Checkpoint**: Foundation ready — WhatsApp behavior unchanged (SC-008), all
three user stories can now start.

---

## Phase 3: User Story 1 - Connect Gmail via Google OAuth (Priority: P1) 🎯 MVP

**Goal**: A logged-in user clicks "Connect Gmail", is sent to Google's
consent screen (read-only scope), grants access, and returns to a Gmail
connection with status "Connected". Tokens are stored encrypted, backend-only.

**Independent Test**: Click "Connect Gmail" → approve on Google's screen →
Connections page shows Gmail "Connected". Denying/cancelling leaves the status
unchanged and shows a friendly message (spec US1 + Acceptance Scenarios).

**Manual dependency**: Phase 1 (Google OAuth client) MUST be complete.

### Tests for User Story 1 (write FIRST; must FAIL before implementation)

- [x] T009 [P] [US1] Contract tests in `backend/tests/test_gmail_oauth.py`:
  `GET /connections/gmail/auth-url` requires auth (401) and returns
  `{"auth_url"}`; `POST /connections` for gmail → 400; callback with valid
  `code+state` redirects to `FRONTEND_URL/connections?gmail=connected`;
  callback with `error`/bad state redirects to `?gmail=error`
  - **Accept**: Mock Google token endpoint via monkeypatched `httpx.AsyncClient`; no real network.
- [x] T010 [P] [US1] Unit tests in `backend/tests/test_gmail_oauth.py`:
  `build_authorization_url` includes `scope=gmail.readonly`,
  `access_type=offline`, `prompt=consent`, signed `state`;
  `verify_state` accepts a valid signed state for the right user and rejects
  wrong `purpose`/expired/forged tokens
  - **Accept**: Never await motor under `asyncio.run` (repo rule) — use the TestClient loop or a fake collection.

### Implementation for User Story 1

- [x] T011 [US1] Create `backend/services/gmail.py` with OAuth helpers:
  `build_authorization_url(user_id)` (state = HS256 JWT via PyJWT/`JWT_SECRET`
  with `purpose="gmail_oauth"`, `sub=user_id`, 10-min `exp`), `verify_state(state)`,
  `exchange_code(code)` (POST `oauth2.googleapis.com/token`) (research §1–§2)
- [x] T012 [US1] Implement `backend/routes/gmail.py` router
  (prefix `/connections/gmail`): `GET /auth-url` with
  `Depends(get_current_user)` → `{"auth_url": ...}` (contracts §1)
- [x] T013 [US1] Implement `GET /connections/gmail/callback` in
  `backend/routes/gmail.py`: verify `state`, handle `error` param, `exchange_code`,
  re-encrypt tokens via `utils/encryption.encrypt`, upsert connection with
  `gmail_email` (best-effort tokeninfo), then `302` to
  `{FRONTEND_URL}/connections?gmail=connected` or `?gmail=error` (contracts §2)
  - **Accept**: `refresh_token` returned by exchange is REQUIRED — missing ⇒ connection `error`; browser always ends on the Connections page.
- [x] T014 [P] [US1] Add `getGmailAuthUrl(): Promise<{ auth_url: string }>` to
  `lib/api/connections.ts` (apiFetch `GET /connections/gmail/auth-url`,
  credentials include) (contracts §7)
- [x] T015 [US1] Update `components/connections/ConnectionCard.tsx`: gmail
  Connect → call `getGmailAuthUrl()` → `window.location.assign(authUrl)` with
  a "Redirecting to Google..." disabled state; keep the WhatsApp POST path
  unchanged (contracts §7)
- [x] T016 [P] [US1] Add connect-result banner to
  `app/(dashboard)/connections/page.tsx`: read `useSearchParams()` —
  `?gmail=connected` ⇒ success banner, `?gmail=error` ⇒ friendly error (never
  raw Google errors), banner clears on navigation (spec edge cases)

**Checkpoint**: User Story 1 fully functional and testable alone. SC-001
(connect < 2 min), SC-004 (zero tokens user-visible), teacher demo reachable.

---

## Phase 4: User Story 2 - Receive New Emails as Normalized Messages (Priority: P2)

**Goal**: From this point on, new emails are fetched automatically (simple
asyncio poller, no Pub/Sub), converted to the canonical format, run through
the existing AI pipeline, and shown as dashboard cards with an optional
subject line — indistinguishable in treatment from WhatsApp.

**Independent Test**: Send a real email to the connected Gmail → appears on
the dashboard as a card with `source: gmail`, correct sender/content/subject,
and AI analysis within 5 minutes; a duplicated detection creates no extra
card (spec US2).

### Tests for User Story 2 (write FIRST; must FAIL before implementation)

- [x] T017 [P] [US2] Unit tests for `normalize_email` in
  `backend/tests/test_gmail_ingest.py`: plain-text body, HTML-only body (markup
  not stored), empty/no-text body → `content == ""`, attachment parts ignored,
  sender display-name vs bare-address fallback, `external_message_id` = Gmail id,
  `subject` optional (spec format rules 3, 2, 5)
- [x] T018 [P] [US2] Integration test in `backend/tests/test_gmail_ingest.py`:
  `poll_connected_gmail` (or its fetch seam with a monkeypatched httpx) calls
  `ingest_message(source="gmail", ...)`, produces a stored message with
  `ai_analysis`, duplicate `external_message_id` returns the SAME message id
  (no second AI run), and `last_fetched_at` watermark advances (data-model §2, §4)

### Implementation for User Story 2 (Email Ingestion)

- [x] T019 [US2] Implement `normalize_email(raw_gmail: dict)` in
  `backend/services/gmail.py`: stdlib `email` MIME parse — text/plain body,
  HTML fallback stripped to visible text, empty → `""`, attachments skipped,
  sender/subject/`external_message_id`/received_at mapping (research §7)
- [x] T020 [US2] Implement `ensure_access_token(connection)` + Gmail API calls
  in `backend/services/gmail.py`: list (`q=after:<epoch>&maxResults=20`) and
  get (`format=raw`); refresh via `refresh_token` when `token_expires_at`
  past/missing or 401, re-encrypt + persist; `invalid_grant` → connection
  `error` (research §3, §4)
- [x] T021 [US2] Implement `poll_connected_gmail()` in `backend/services/gmail.py`:
  iterate `{provider:"gmail", status:"connected"}`, use
  `last_fetched_at` (default `connected_at − 1h`) as the `after` epoch,
  `ingest_message(source="gmail", subject=..., background_tasks=None)` per
  email, update the watermark after success; per-user failures isolated
  (contracts §5)
- [x] T022 [US2] Wire the poller into `backend/main.py` lifespan: start a
  single `asyncio` task looping every `GMAIL_POLL_INTERVAL_SECONDS`, cancel on
  shutdown (contracts §5; research §5)
- [x] T023 [US2] Expose optional `subject` in the message response path
  (`backend/routes/messages.py` / `backend/models/message.py`) so the
  frontend can read it (additive; absent for WhatsApp/simulate) (data-model §3, §6)

### Implementation for User Story 2 (Frontend)

- [x] T024 [P] [US2] Add `subject?: string` to the `Message` interface and
  render a subject line in `MessageCard` in `app/(dashboard)/inbox/page.tsx`
  only when present (spec format rule 7)

**Checkpoint**: User Story 2 independently testable. SC-002 (≤ 5 min), SC-003
(zero duplicates), 100% of new emails appear, WhatsApp cards unaffected.

---

## Phase 5: User Story 3 - Manage Connection Status and Disconnect (Priority: P3)

**Goal**: The Connections page shows Connected / Disconnected / Error with
working Disconnect (revokes Google access + deletes stored tokens) and a
reconnect path; a Google-side revocation surfaces as an error state with a
reconnect CTA — the connection never crashes or silently dies.

**Independent Test**: Disconnect a connected Gmail → status "Disconnected", no
new emails afterwards, reconnecting requires a fresh Google grant; revoking in
Google settings flips the UI to an error state with a reconnect action
(spec US3).

### Tests for User Story 3 (write FIRST; must FAIL before implementation)

- [x] T025 [P] [US3] Contract tests in `backend/tests/test_gmail_manage.py`:
  `DELETE /connections/{id}` for a connected gmail connection with owner token
  returns 204 and (mock-verified) triggers Google revoke then removes the doc;
  404 for other user's id and for unknown id — identical bodies (spec FR-011, FR-012/SC-005)

### Implementation for User Story 3

- [x] T026 [US3] Extend `ConnectionService.delete_connection` in
  `backend/services/connection.py`: when the target provider is `gmail`, load
  the doc with tokens and call Google revoke (best-effort, logged) before the
  user-scoped delete (contracts §3; data-model §2 transitions)
- [x] T027 [US3] Add `revoke_app(refresh_token)` + the poller failure→error
  plumbing (`set_connection_error` on `invalid_grant`) to
  `backend/services/gmail.py` (research §3, §9 risk "revoked in settings")
- [x] T028 [US3] Update `components/connections/ConnectionCard.tsx`: render an
  explicit error state for gmail (`status === "error"`) with a Reconnect CTA
  that re-runs the OAuth redirect (T014/T015 reuse)

**Checkpoint**: User Story 3 independently testable. SC-007 (revoke + delete
< 1 min, no new emails), error state recovery works.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Regression safety, docs, and a security pass across all stories.

- [x] T029 Validate SC-008 no-regression: run `pytest` (backend suite) +
  `npx vitest run` (frontend) — full suite green, WhatsApp/webhook/simulate tests pass
- [x] T030 [P] Validate `specs/017-gmail-integration/quickstart.md` end-to-end:
  two-test-user isolation check (SC-005 — User A/B see only their own
  connection and messages via UI and direct API), reconnect-after-disconnect scenario
- [x] T031 Add a Day 26 manual note to `AGENTS.md` (`<!-- MANUAL ADDITIONS START -->`
  section, 015/016 pattern): OAuth-state design, poller + env vars, ingest
  `subject` + self-spawned analysis, test rules (no `asyncio.run` under motor)
- [x] T032 [P] Security harden pass (SC-004): grep routes/services/tests for
  token leakage (logs, responses, `@Depends` responses, URL params); confirm
  BOTH tokens go through `encrypt()`; confirm `state` is purpose-scoped +
  expiring; confirm `gmail.readonly` never expands; add missing assertions to
  T009/T010/T025 as needed

**Checkpoint**: Feature complete and regression-free; demo-ready.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No code dependencies; T001–T002 are manual, T003–T004 can start once T001/T002 exist. BLOCKS US1's live test.
- **Foundational (Phase 2)**: Depends on T004 installed deps. BLOCKS all user stories (model/service/ingest contract changes first).
- **US1 (Phase 3)**: Depends on Phases 1 + 2. Independent of US2/US3.
- **US2 (Phase 4)**: Depends on US1 (a real connected mailbox is required for
  live verification; the poller also reads the US1-created connection doc).
- **US3 (Phase 5)**: Depends on US1 (needs a connected gmail row). US3 does
  not require US2 to be complete.
- **Polish (Phase 6)**: Depends on the stories you choose to ship.

### User Story Dependency Graph

```text
Phase 1 (Google setup) ──▶ Phase 2 (foundation) ──┬─▶ US1 (connect) ──▶ US2 (receive)
   (manual + env)              (backend shared)   └─▶ US1 ───────────▶ US3 (manage)
```

- **US1**: After Foundation — no cross-story dependency. MVP.
- **US2**: After US1 (needs a real connected account + connection doc).
- **US3**: After US1 (needs a connected gmail doc); testable without US2.

### Within Each User Story

- Tests written FIRST and confirmed FAILING before implementation.
- Backend service → router → frontend, in that order.
- Story checkpoint validated before moving to the next priority.

### Parallel Opportunities

- Phase 1: T004 runs alongside the manual console work (T001–T003 pull in its dep only at install time).
- Phase 2: T005–T008 all touch different files → 4-way parallel.
- US1: T009 & T010 (both in `test_gmail_oauth.py` — same file, keep together or split), T014/T016 parallel; T011→T012→T013 sequential (service → urls → callback).
- US2: T017/T018 (same new test file), T019→T020→T021→T022 sequential (pipeline), T023/T024 parallel after T019.
- US3: T025 (test) then T026→T027 (service/gmail helpers) then T028 (frontend).
- Polish: T029/T030/T032 parallel; T031 after code settles.

---

## Parallel Example: User Story 1

```plaintext
Launch together (different files):
  Task: "Implement GET /connections/gmail/auth-url + /callback in backend/routes/gmail.py"  (after T011)
  Task: "Add getGmailAuthUrl() to lib/api/connections.ts"
  Task: "Update ConnectionCard gmail Connect → redirect in components/connections/ConnectionCard.tsx"
  Task: "Add ?gmail=connected|error banner to app/(dashboard)/connections/page.tsx"
```

T011 (`backend/services/gmail.py`) must land first — the router and both
frontend call sites depend on it.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 (Google Cloud MANUAL + env) and Phase 2 (foundation).
2. Implement US1 tests (T009–T010, failing) → T011–T016.
3. **STOP and VALIDATE**: click through OAuth; confirm Connected; confirm no
   tokens in any response (SC-001, SC-004). Demo-able account linking.
4. Ship/demo if ready — Gmail appear on the Connections page as Connected.

### Incremental Delivery

1. Foundation ready (Phases 1–2) — existing suite still green (SC-008).
2. Add US1 → validate → demo (MVP: Connect).
3. Add US2 → validate with a real email → demo (core value: emails become
   analyzed message cards).
4. Add US3 → validate revoke/reconnect/error → demo (user control, Principle IV).
5. Polish (T029–T032) → full demo.

### Parallel Team Strategy

1. One person completes Phase 1 MANUAL + env while another does T004 + Phase 2 shared tasks.
2. After Foundation: Developer A takes US1; nothing else can proceed on Gmail until connect works.
3. After US1: Developer B (US2) and Developer C (US3) can run in parallel.

---

## Notes

- Follow the checklist format for every task; `[P]` = different files, no
  dependencies; `[US#]` maps to the spec user story for traceability.
- Test tasks MUST be written and FAIL before their implementation tasks.
- Commit after each task or logical checkpoint (per existing repo convention —
  do NOT auto-commit unless asked).
- Manual tasks are not automatable; the implementer MUST confirm Phase 1 is
  done before starting US1.
- Reuse the repo's test conventions: prefer the TestClient loop / fake
  collections over `asyncio.run` under Motor; monkeypatch `httpx.AsyncClient`
  for all Google calls.

