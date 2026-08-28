# Tasks: Real WhatsApp Webhook (Day 23)

**Input**: Design documents from `specs/014-whatsapp-webhook/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/webhook-api.md
**Tests**: Included — the plan (Step 8-9) specifies a pytest matrix; the spec
mandates testable user scenarios. Tests are written FIRST per story and must
FAIL before implementation.
**Organization**: Tasks are grouped by user story to enable independent
implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1-US5)
- Include exact file paths in descriptions

## Contract → User Story Mapping

| Endpoint | Served by |
|---|---|
| `GET /webhooks/whatsapp` (verification challenge) | US2 |
| `POST /webhooks/whatsapp` (signature + structure) | US2 |
| `POST /webhooks/whatsapp` (parse, normalize, store, fast ack) | US1 |
| `POST /webhooks/simulate` (authed simulate parity) | US3 |
| Ingest dedup behavior | US4 |
| Owner resolution (`connections` + phone number filter) | US5 |

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Secrets required before any code or test runs.

- [x] T001 [P] Add `WHATSAPP_APP_SECRET=<App Secret from Meta portal → App Settings → Basic>` to `backend/.env` (file is gitignored; never commit the value)
- [x] T002 [P] Add an empty `WHATSAPP_APP_SECRET=` key to `backend/.env.example`

**Acceptance Criteria**:
- `backend/.env` contains a real `WHATSAPP_APP_SECRET` value; `backend/.env.example` has the empty key; `git status` shows neither file tracked.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The shared ingestion path every story depends on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T003 [P] Create shared ingestion service `backend/services/webhook_ingest.py` with `async ingest_message(user_id, source, sender, content, external_message_id=None, message_type="text") -> str`: builds the normalized document (`user_id`, `source`, `sender`, `content`, `external_message_id` optional, `message_type`, `status="unread"`, `state="active"`, `received_at`/`created_at`/`updated_at` = UTC now), inserts into the `messages` collection, catches `DuplicateKeyError` on `external_message_id` and returns the existing document id (no re-insert), schedules `analyze_message(content, message_id, user_id)` from `backend/services/ai/analyzer.py` as a background task, and returns the message id on fresh and duplicate paths
- [x] T004 [P] Add the partial unique index on `messages.external_message_id` to the lifespan in `backend/main.py`: `create_index([("external_message_id", 1)], unique=True, partialFilterExpression={"external_message_id": {"$type": "string"}})`
- [x] T005 [P] Extend `backend/models/message.py`: add optional `external_message_id: Optional[str]` and `received_at: Optional[datetime]` to `MessageResponse` and emit them in `message_doc_to_response` only when present (simulate/legacy docs unaffected)

**Checkpoint**: `ingest_message` stores a normalized document and returns its id; duplicate-key inserts resolve to the existing id; the index exists on startup; serialization round-trips optional fields.

---

## Phase 3: User Story 2 - Incoming Deliveries Are Verified Before Processing (Priority: P1)

**Goal**: Every delivery to `POST /webhooks/whatsapp` is signature-verified
and structurally validated before anything is read or stored; the Day 22 GET
verification challenge keeps working. Nothing unverified or malformed lands
in data.

**Independent Test**: (a) Provider webhook verification challenge passes in the
Meta portal; (b) requests with missing or wrong `X-Hub-Signature-256` are
rejected with 403 and nothing stored; (c) malformed or non-message payloads
are acknowledged without storing or analyzing.

### Tests for User Story 2 (write FIRST; must FAIL before implementation) ⚠️

- [x] T006 [US2] Add test `test_post_rejects_invalid_signature` in `backend/tests/test_webhooks.py`: signed-with-wrong-secret delivery → 403 and zero new documents
- [x] T007 [US2] Add test `test_post_rejects_missing_signature` in `backend/tests/test_webhooks.py`: delivery without `X-Hub-Signature-256` → 403 and zero new documents
- [x] T008 [US2] Add tests `test_verification_challenge_echoes_challenge` and `test_verification_challenge_wrong_token_403` in `backend/tests/test_webhooks.py`: valid challenge echoed as 200 plain text; wrong `hub.verify_token` → 403

### Implementation for User Story 2

- [x] T009 [US2] Add constant-time HMAC-SHA256 helper and wire it into `POST /webhooks/whatsapp` in `backend/routes/webhooks.py`: read raw body, compare `X-Hub-Signature-256` against `WHATSAPP_APP_SECRET`, return 403 before any parsing/storage when missing or mismatched
- [x] T010 [P] [US2] Update `backend/tests/test_auth.py`: add `("GET", "/webhooks/whatsapp")` and `("POST", "/webhooks/whatsapp")` to `PUBLIC_ROUTES`, and change the anonymous webhook assertion from 401 to 403 signature gate (simulate-401 coverage landed in T019)
- [x] T011 [US2] Add a Pydantic model for Meta's delivery envelope (`backend/models/meta_webhook.py`) and validate structure in `backend/routes/webhooks.py`: malformed payloads → 400; non-message events (`field != "messages"` or empty `messages[]`) acknowledged 200 without storing

**Checkpoint**: Signature, structure, and challenge behaviors all pass; the auth audit (`test_auth.py`) is green with the webhook public.

---

## Phase 4: User Story 1 - Real WhatsApp Message Reaches the Dashboard (Priority: P1) 🎯 MVP

**Goal**: A real message to the Business number is parsed, normalized, stored,
analyzed, and visible on the Dashboard with no manual step.

**Independent Test**: Send a message to the Business number; a Dashboard card
appears within 30 seconds with the correct source, sender, content, and AI
fields.

### Tests for User Story 1 (write FIRST; must FAIL before implementation) ⚠️

- [x] T012 [US1] Add test `test_post_ingests_real_text_message` in `backend/tests/test_webhooks.py`: valid signed Meta text payload → 200 and a stored document with `source="whatsapp"`, `sender` from profile name, `content`, and `external_message_id`
- [x] T013 [US1] Add test `test_media_only_message_stored` in `backend/tests/test_webhooks.py`: signed media payload (type `image`) → stored with empty `content` and `message_type="media"`
- [x] T014 [US1] Add test `test_post_batched_multiple_messages` in `backend/tests/test_webhooks.py`: one delivery with several `messages[]` events → every message stored under one acknowledgement
- [x] T015 [US1] Add test `test_post_non_message_event_ignored` in `backend/tests/test_webhooks.py`: a `statuses`/empty-messages delivery → 200 acknowledged, nothing stored

### Implementation for User Story 1

- [x] T016 [US1] Implement Meta payload parsing and normalization in `backend/routes/webhooks.py` inside the verified POST handler: for each `messages[]` event extract `sender` (`contacts[0].profile.name` else `messages[].from`), `content` (`text.body` guarded by `type == "text"` else empty string), `message_type` (`"text"`/`"media"`), `external_message_id` (`messages[].id`); call `ingest_message(..., source="whatsapp")` from `backend/services/webhook_ingest.py` (also added server-side owner resolution + `phone_number_id` filter here so a stored doc always has a valid `user_id`; shared with T030)
- [x] T017 [US1] Return 200 `{"status": "ok"}` immediately after persistence in `backend/routes/webhooks.py` so the AI pipeline (scheduled by `ingest_message`) runs after the response, keeping the delivery acknowledgement fast (< 1s)

**Checkpoint**: A valid signed delivery stores every message with normalized
fields, the AI pipeline populates `ai_analysis`, and the Dashboard renders the
card — the MVP journey works end-to-end.

---

## Phase 5: User Story 3 - Normalized Format and Simulation Parity (Priority: P2)

**Goal**: Real and simulated messages are indistinguishable to the AI and
Dashboard; the simulate feature keeps working with zero regression.

**Independent Test**: Send one simulated and one real message with the same
text; both produce identical Dashboard cards and AI analysis, and the
simulate flow works on its own.

### Tests for User Story 3 (write FIRST; must FAIL before implementation) ⚠️

- [x] T018 [US3] Add test `test_simulate_endpoint_ingests_with_source` in `backend/tests/test_webhooks.py`: authed POST to `/webhooks/simulate` with `{sender, message}` → stored doc with `source="simulate"` and `message_type="text"`
- [x] T019 [US3] Add test `test_simulate_requires_auth` in `backend/tests/test_webhooks.py`: `/webhooks/simulate` without a session → 401
- [x] T020 [US3] Add test `test_simulate_and_real_identical_analysis` in `backend/tests/test_webhooks.py`: simulated and (signed) real messages with identical text produce identical `ai_analysis` (same priority/summary)

### Implementation for User Story 3

- [x] T021 [P] [US3] Add authenticated `POST /webhooks/simulate` in `backend/routes/webhooks.py` (`Depends(get_current_user)`): accept `{sender, message}`, call `ingest_message(user_id, source="simulate", ...)` with the session user, return the stored message response (same shape as `POST /messages`) — also fixed `webhook_ingest.py` to persist `ai_analysis` via a background `_analyze_and_store` task (the previously scheduled analysis result was discarded, so the dashboard would never show AI for webhook messages)
- [x] T022 [P] [US3] Update `components/SimulateMessage.tsx`: change the POST target from `/webhooks/whatsapp` to `/webhooks/simulate` (payload `{sender, message}` unchanged)

**Checkpoint**: Simulated messages reach the Dashboard with source "Simulate"
and pass through the identical AI pipeline; parity tests green.

---

## Phase 6: User Story 4 - Duplicate Deliveries Produce No Duplicate Records (Priority: P2)

**Goal**: Redelivering the same message (same `externalMessageId`) produces
exactly one stored record and one pipeline run.

**Independent Test**: Deliver the same message payload twice; exactly one
record exists and the AI pipeline is not re-run.

### Tests for User Story 4 (write FIRST; must FAIL before implementation) ⚠️

- [x] T023 [US4] Add test `test_post_duplicate_external_id_single_document` in `backend/tests/test_webhooks.py`: same signed payload delivered twice → both 200, exactly one document in the collection
- [x] T024 [US4] Add test `test_duplicate_does_not_reanalyze` in `backend/tests/test_webhooks.py`: spy on `analyze_message` from `backend/services/ai/analyzer.py` and assert it runs once for two deliveries of one `external_message_id`
- [x] T025 [P] [US4] Update the duplicate-guard in `backend/test_attention_pipeline.py`: replace the fake `{sender, message, timestamp}` double-POST with two signed Meta payloads sharing the same `messages[].id` and assert a single document (same response id both times)

### Implementation for User Story 4

- [x] T026 [US4] Complete the duplicate acknowledgement path: in `backend/services/webhook_ingest.py` ensure a `DuplicateKeyError` on `external_message_id` returns the existing message id and does NOT schedule `analyze_message`; in `backend/routes/webhooks.py` confirm duplicates are acknowledged with 200 and logged, never stored twice — verified in place (returns existing id before `add_task`; covered by T023/T024)

**Checkpoint**: US4 tests turn green; dedup holds under redelivery; retry-safe.

---

## Phase 7: User Story 5 - Messages Land Under the Correct User (Priority: P2)

**Goal**: Every webhook message is attributed to the correct owning user
server-side and invisible to every other account.

**Independent Test**: Ingest a message through the webhook; confirm from a
second account it is not visible, and from the owning account it is.

### Tests for User Story 5 (write FIRST; must FAIL before implementation) ⚠️

- [x] T027 [P] [US5] Rework the webhook ownership tests in `backend/tests/test_user_isolation.py` (`test_webhook_message_scoped_to_authenticating_user` / `test_webhook_tasks_scoped_to_authenticating_user`): register user A, create a connected whatsapp connection for A, send a valid signed Meta payload, assert the message is visible to A and invisible to user B
- [x] T028 [US5] Add test `test_post_without_connected_connection_acknowledged` in `backend/tests/test_webhooks.py`: signed valid payload when no whatsapp connection is `connected` → 200 acknowledged and nothing stored
- [x] T029 [US5] Add test `test_post_unknown_phone_number_ignored` in `backend/tests/test_webhooks.py`: signed payload whose `metadata.phone_number_id` differs from `WHATSAPP_PHONE_NUMBER_ID` → 200 acknowledged and nothing stored

### Implementation for User Story 5

- [x] T030 [US5] Implement server-side ownership resolution at the top of the verified POST handler in `backend/routes/webhooks.py`: skip deliveries whose `value.metadata.phone_number_id != WHATSAPP_PHONE_NUMBER_ID`; resolve `user_id` from the `connections` collection (`provider="whatsapp"`, `status="connected"`) via the existing connection store in `backend/services/connection.py`; when no owner resolves, acknowledge 200 and store nothing; pass the resolved `user_id` into `ingest_message` — implemented earlier in T016 (US1 required a `user_id`); verified here by T028/T029 + T027

**Checkpoint**: US5 tests green; ownership is payload-independent and other
users never see webhook messages.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Verification, regression safety, and constitution compliance
across all stories.

- [x] T031 [P] Run the full backend suite: execute `python -m pytest tests/ -q` in `backend/` and fix any regressions (all green) — 89 passed / 0 failed on the final code
- [x] T032 [P] Run the standalone scripts `backend/test_ai_analysis.py` and `backend/test_attention_pipeline.py` against the running backend and confirm they pass — attention pipeline 10/10 (9 unit + signed-payload duplicate-guard integration against live :8000); ai_analysis 3/3 (one transient Groq flake on the "normal message" sample recovered on retry; run with `PYTHONUTF8=1` on this console for emoji)
- [ ] T033 Execute the manual real-message validation from `specs/014-whatsapp-webhook/quickstart.md`: ngrok up, portal callback re-verified, real WhatsApp message → Dashboard card within 30s; signed-body dedup check in MongoDB; tampered-signature curl → 403; in-app simulate still works — PARTIAL: tampered-signature 403 and signed-body dedup verified against the live server; the real-phone send needs the user's Meta portal + a live ngrok tunnel + their phone (blocked on user)
- [x] T034 Re-check the Day 23 constitution compliance list in `.specify/memory/constitution.md` against the final implementation (signature-first, dedup by `external_message_id`, fast ack before async analysis, server-side ownership, media stored not dropped, simulation parity, no auto-send) — all 6 normalized-format rules + 6 security rules + 5 "MUST NOT" + quality bar verified; source-agnostic grep clean

**Acceptance Criteria**:
- Full pytest suite green; standalone scripts green; manual real-message run
  completes all quickstart steps; constitution Day 23 items all comply.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — **BLOCKS all user stories**
- **User Story 2 (Phase 3)**: Depends on Foundational
- **User Story 1 (Phase 4)**: Depends on US2 (Phase 3) — the verified POST handler is completed there
- **User Story 3/4/5 (Phases 5-7)**: Depends on Foundational; US4 builds on the dedup logic in `ingest_message` (T003); US5 uses the existing connection service
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **US2 (P1)**: After Foundational — no dependency on other stories
- **US1 (P1)**: After US2 — needs signature + structure gate in place
- **US3 (P2)**: After Foundational — can parallel US1/US2 (different files)
- **US4 (P2)**: After Foundational — can parallel US1/US2
- **US5 (P2)**: After Foundational — can parallel US1/US2

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Services before endpoints; core implementation before integration
- Story complete and independently testable before the next priority

### Parallel Opportunities

- Setup: T001, T002 run in parallel
- Foundational: T003, T004, T005 run in parallel
- US2: T009 + T010 run in parallel (webhooks.py vs test_auth.py)
- US3: T021 + T022 run in parallel (webhooks.py vs SimulateMessage.tsx)
- US4: T023 + T024 + T025 run in parallel (test_webhooks.py split vs test_attention_pipeline.py)
- US5: T027 (test_user_isolation.py) runs parallel to T028/T029 (test_webhooks.py)
- Polish: T031, T032 run in parallel
- Different user stories can be worked in parallel by different team members
  after Foundational completes

---

## Parallel Example: User Story 3

```bash
# Launch the two implementation tasks together (different files, no deps):
Task: "Add authenticated POST /webhooks/simulate in backend/routes/webhooks.py"
Task: "Update components/SimulateMessage.tsx to POST /webhooks/simulate"
```

## Parallel Example: Foundational

```bash
# Launch the three foundational tasks together (different files, no deps):
Task: "Create backend/services/webhook_ingest.py"
Task: "Add partial unique index in backend/main.py"
Task: "Extend backend/models/message.py"
```

---

## Implementation Strategy

### MVP First (US2 + US1)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 2 (security gate)
4. Complete Phase 4: User Story 1 (ingestion journey)
5. **STOP and VALIDATE**: real message → Dashboard within 30s (SC-001, SC-007)
6. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → foundation ready
2. US2 → verified ingestion is safe
3. US1 → real message reaches Dashboard (MVP!)
4. US3 → simulation parity proven, zero regression
5. US4 → duplicate-safe, retry-proof
6. US5 → correct user attribution everywhere
7. Polish → full suite green + manual real-message pass

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: US2 → US1 (MVP end-to-end)
   - Developer B: US3 (simulate parity + frontend pointer)
   - Developer C: US5 (ownership; shares webhooks.py with A — coordinate)
   - US4 after T003 lands (dedup in ingest service)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps each task to a user story for traceability
- Each user story is independently completable and testable
- Tests per story are written first and verified failing before implementation
- Commit after each task or logical group
- Stop at any checkpoint to validate the story independently
- Coordination note: T009/T011/T016/T017 (US2/US1) edit the same
  `backend/routes/webhooks.py` — do NOT parallelize within the file; run US2
  fully before US1
- Avoid: vague tasks, same-file parallel conflicts, cross-story dependencies
  that break independence