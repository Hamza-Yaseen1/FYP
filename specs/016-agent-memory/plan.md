# Implementation Plan: Agent Memory / Context (Day 25)

**Branch**: `016-agent-memory` | **Date**: 2026-08-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/016-agent-memory/spec.md`

## Summary

Give the system **lightweight context between related messages**. Today every
message is analyzed in isolation; Day 25 lets two clearly-related messages
("Can you send the report?" → "Need it before our meeting.") be recognized as
one exchange, stored with shared identity fields, and analyzed with bounded
same-thread context inside the **existing single AI call** — so a follow-up
message can add a deadline to an earlier message's task, visibly and
explainably.

```text
Ingest (Day 23) → resolve link (deterministic rule, 0 LLM)
  → store messageId / threadId / conversationId (server-set, never invented)
  → Orchestrator (Day 24): analyze path gathers ≤5 recent same-thread msgs
  → ONE combined AI call with a CONTEXT block (no extra round-trip)
  → context_updates validated against the thread, applied to earlier msgs
    with a reason naming the source message
  → ai_analysis (+ context_updates) → MongoDB → Dashboard (unchanged)
```

**Goal of this phase**: make *linked* messages better analyzed without touching
the AI pipeline's cost model, the Dashboard, or the user's other workflows.
Standalone messages must behave exactly as today (zero regression, zero extra
cost). The link is **deterministic and conservative** — the system never
guesses. No vector store, no embeddings, no RAG: this is a rule, two additive
MongoDB fields, and a bounded prompt note.

**Key design choice** — *link first, context second, validate everything*: the
link is resolved at ingest with one indexed query. Context never creates a new
call — it is a `CONTEXT` block rendered into the existing
`ANALYSIS_PROMPT`. Any suggestion from the model that "context changes message
X" is post-validated against the actual thread (target must be in the same
user's thread, the value must literally appear in the source message) before a
plain-language revision is written to the earlier message. Nothing is ever
silently rewritten.

## Technical Context

**Language/Version**: Python 3.13
**Primary Dependencies**: pytests; `re` + `datetime.timedelta` (stdlib) for
the deterministic link rule — **no new runtime dependencies** (stock: FastAPI,
pymongo/motor, groq, pydantic)
**Storage**: MongoDB `messages` collection — three additive identity fields
(`messageId`, `threadId`, `conversationId`) plus an additive
`ai_analysis.context_updates` array on enriched messages; two new per-user
indexes on `{user_id, conversationId, received_at}` and
`{user_id, threadId, received_at}`; no migration (Pydantic
`MessageResponse` + `message_doc_to_response` map the new fields)
**Testing**: pytest + httpx TestClient (existing suite) — new
`test_threads.py` (link rule, 30-pair labeled set, isolation) and
`test_context_ai.py` (prompt injection, validation, single-call count);
mocked `GroqProvider`; never await motor under `asyncio.run`
**Target Platform**: Local development (FastAPI backend, Next.js frontend)
**Project Type**: Web application (frontend + backend)
**Performance Goals**: Standalone messages get **zero** added latency (no link
query runs on their path beyond the one it always pays); linked messages add
exactly ONE indexed link query at ingest + ONE context query at analysis;
arrival → stored result stays within the existing ≤ 10s budget
**Constraints**: Links MUST be deterministic (user + source + sender +
≤ 60-minute window) — never AI-grouper; context capped at the 5 most recent
same-user thread messages; context MUST ride the existing single analysis
call (Complete AI Pipeline rule); user isolation is absolute (Day 18);
linking MUST never block ingestion (Progressive Enhancement); context effects
MUST be validated + explained, and explicit user-stated facts win (Day 11
mirror); the Dashboard reads stored results only — no new rendering path
**Scale/Scope**: Single demo user; deterministic rule-based linking only;
`conversationId` mirrors `threadId`; no backfill of history beyond the rule's
own anchor stamping

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle / Rule | Status | Notes |
|---|---|---|
| I. Simplicity First | ✅ PASS | One link module (`threads.py`) + one context helper (`services/ai/context.py`); no framework, no memory store |
| II. Vertical Slices | ✅ PASS | Complete slice: ingest → link → context → single analysis → validated enrichment → stored → same dashboard cards |
| III. AI is Assistive | ✅ PASS | Every context effect is validated, named, and recorded with a plain-language reason — never a silent rewrite |
| IV. User Control | ✅ PASS | Explicit user-stated facts win over inferred context (Day 11 mirror); enriched cards stay individually owned/queryable/deletable |
| V. Security and Privacy | ✅ PASS | IDs are server-set, never client-supplied; no new PII; threads are scoped to one user |
| VI. Clean Code | ✅ PASS | Deterministic pure link logic + thin DB wrapper; reuses `analyze_message`, `process_message`, the existing prompt |
| VII. Progressive Enhancement | ✅ PASS | No link → analysis proceeds exactly as today; link/context failure never blocks ingestion or produces blank states |
| Day 18 User Isolation | ✅ PASS | Thread/context queries are always filtered by `user_id`; context-update targets must live in the SAME thread |
| Day 23 Webhook Rules | ✅ PASS | Ingestion paths unchanged; only additive identity fields are stored |
| Day 11 Deadline Mirror | ✅ PASS | Context NEVER overrides a stated deadline — prompt rule + backend keeps explicit fields |
| Complete AI Pipeline | ✅ PASS | Context is a block inside the same `analyze` call; zero extra LLM round-trips (provider-call-count test) |
| Day 24 Orchestrator | ✅ PASS | Context availability is an input to the existing Orchestrator; trivial/skip paths untouched; `routing` record unchanged |
| Day 25 Agent Memory / Context | ✅ PASS | Implements the new constitution section: deterministic link, stored fields contract, bounded context, no memory framework, quality bar |

**No violations. No complexity tracking needed.**

## Project Structure

### Documentation (this feature)

```text
specs/016-agent-memory/
├── plan.md              # This file
├── spec.md              # Feature spec (/sp.specify output)
├── research.md          # Phase 0: link rule + context-injection decisions
├── data-model.md        # Phase 1: identity fields + context_updates shape
├── quickstart.md        # Phase 1: Day 25 runbook
├── contracts/           # Phase 1: stored identity + context contracts
│   ├── thread-identity-contract.md
│   └── ai-context-prompt-contract.md
└── tasks.md             # Phase 2: NOT created by /sp.plan
```

### Source Code (repository root)

```text
backend/
├── services/
│   ├── threads.py                   # NEW — deterministic link resolution + anchor stamping
│   ├── ai/
│   │   ├── context.py               # NEW — thread-context fetch, prompt block, validation, apply
│   │   ├── orchestrate.py           # UPDATE — accept thread_id; gather + inject context; apply updates
│   │   ├── analyzer.py              # UPDATE — context_messages param → provider; context_updates passthrough
│   │   └── providers/
│   │       ├── base.py              # UPDATE — analyze(message, context=None); context_updates on result
│   │       ├── groq.py              # UPDATE — CONTEXT block in ANALYSIS_PROMPT; parse context_updates
│   │       └── openai.py            # UPDATE — same signature/parity (single call preserved)
│   └── webhook_ingest.py            # UPDATE — ingest_message resolves + stores ids; task passes thread_id
├── models/
│   └── message.py                   # UPDATE — ContextUpdate; MessageResponse + threadId/conversationId/messageId
├── routes/
│   └── messages.py                  # UPDATE — create_message resolves + stores ids; passes thread_id
├── main.py                          # UPDATE — two new per-user indexes in lifespan
└── tests/
    ├── test_threads.py              # NEW — link rule, 30-pair labeled set, isolation
    ├── test_context_ai.py           # NEW — context prompt, validation, single-call, failures
    ├── test_messages.py             # UPDATE — response carries identity fields; regression
    └── test_webhooks.py             # UPDATE — simulate persists ids + context enrichment

frontend/
└──  (no changes — Dashboard reads stored ai_analysis; identity/context fields are additive)
```

**Structure Decision**: Web application layout. All Day 25 logic lives in
`backend/services/` beside the existing ingestion and AI modules. New code is
two modules (`threads.py`, `services/ai/context.py`); existing entry points
(`webhook_ingest`, `routes/messages.py`) gain a small resolve-and-store step
plus a `thread_id` argument pass-through. Zero frontend changes.

## Technical Approach

### 1. How `threadId` / `conversationId` are assigned (deterministic link)

A new `backend/services/threads.py` owns the rule — pure logic plus one
indexed query. For an incoming message belonging to `(user_id, source,
sender)` arriving at `received_at`:

1. **Window**: `LINK_WINDOW_MINUTES = 60` (env-overridable via
   `LINK_WINDOW_MINUTES`).
2. **Candidate**: `find_one({"user_id", "source", "sender":
   normalize_sender(sender), "state": "active", "received_at": {"$gte":
   received_at - 60min}}, sort received_at desc)`. This is the thread's
   latest message. If none exists → no link.
3. **Inherit or anchor**:
   - candidate has `threadId` → new message inherits it
     (`conversationId = threadId`).
   - candidate has NO `threadId` (it was the thread's first message and stood
     alone) → candidate becomes the **anchor**: `threadId` is defined as
     `str(candidate["_id"])` (stable, human-verifiable, never guessed), and
     the anchor document is stamped with `{threadId, conversationId}` in its
     own `update_one`. The new message stores the same pair.
4. **Store** on the new document: `messageId = str(inserted _id)` (always),
   `threadId` and `conversationId` only when a link exists.
5. **Isolation**: every query carries `user_id`; a thread can never span
   users.

This matches "link on the second in-window message; no threadId is ever
created for a lone message". The window is measured from the thread's latest
message (constitution Core Principle #1), so a chain A→B→C only needs B and C
to be within 60 minutes of each other.

`normalize_sender` lowercases/strips the existing `sender` string — the same
granularity the inbox sender filter already uses. Sender matching stays exact
on the normalized value; it never approximates names.

**Parallel-conversation ambiguity**: when the same sender has multiple active
strands, the "latest in-window message" rule may attach a message to the
*most recent* strand. The spec's edge cases explicitly allow this: ambiguous
cases default to a link on the consecutive arrival (matching real chat
behavior) rather than over-engineering thread interleaving. This is called
out in `research.md` and the data-model.

### 2. How context is passed to the AI (bounded, inside the single call)

1. `process_message` (the Day 24 Orchestrator) learns the message's
   `threadId` from its caller; on the **analyze** path only (trivial/skip
   paths never touch this), it fetches context with
   `context.fetch_thread_context(user_id, thread_id, exclude_message_id,
   limit=5)` — the 5 most recent same-user messages in the thread, excluding
   the message being analyzed, sorted by `received_at` desc.
2. The messages are formatted into a bounded `CONTEXT` block whose ids are
   short handles (`last 7 chars of _id`). `GroqProvider.analyze(message,
   context=None)` renders this block into the existing `ANALYSIS_PROMPT`
   **only when context is present** — with instructions that context may
   enrich missing deadlines/urgency, must never override an explicit
   statement in the current message, and may optionally emit a
   `context_updates` array.
3. Still exactly ONE LLM call. The response is parsed as today
   (`AIAnalysisResult`) plus an optional `context_updates` list.
4. `needs_llm=False` / skipped paths are untouched: `routing`, priority,
   Dashboard output unchanged — Day 24 behavior is preserved for messages
   where the Orchestrator decides context is not worth spending on
   (constitution: "The Orchestrator still decides").

Installation of the block uses `.replace("{context}", ...)` style (like
`{message}` today) so braces never break the prompt.

### 3. How context effects are validated and applied (explainable enrichment)

A provider may return `context_updates` like:

```json
"context_updates": [{
  "target_message_id": "66e1…x7", "field": "deadline",
  "value": "before the meeting", "source_message_id": "a9b2…k4",
  "reason": "Follow-up supplies the deadline for the report task."
}]
```

`context.validate_context_updates` drops anything that is not **provable**:

- target/source ids must be handle-parseable and must exist among the fetched
  thread messages (⇒ same user, same thread),
- `target_message_id` must NOT be the message currently being analyzed,
- `field` must be one of the allowed set (`deadline`, `priority`, `note`),
- the literal `value` must appear as a substring of the referenced source
  message's `content` (nothing invented).

Valid updates are then applied with `context.apply_context_updates`:
`$push` into the **target** message's `ai_analysis.context_updates`:
`{field, value, source_message_id, reason, applied_at}`. The original
analysis fields of the target are never overwritten — the enrichment is a new,
explainable revision (constitution: original wording preserved, reason names
the linked message). Applied on `user_id`-scoped filters only.

### 4. Attacked surfaces / decision table

| Incoming message | Link result | Context to AI | Outcome |
|---|---|---|---|
| Standalone (first / no in-window match) | no thread | none | analyzed exactly as today |
| Trivial / no-content (Day 24) | (link still stored) | none | deterministic defaults, zero LLM |
| Follow-up in window | inherits thread | ≤5 recent msgs | enriched inline + validated context_updates |
| Different sender / channel / >60 min | no thread | none | independent analysis |
| Media-only in a thread | inherits thread | none injected | stored as today, no fake context |
| User states "by Friday" + context says "tonight" | — | prompt rule | explicit statement wins |

## Implementation Steps (in order)

### Step 1 — Create `backend/services/threads.py` (deterministic link)

New module (stdlib + existing collection):

- [ ] `LINK_WINDOW_MINUTES = int(os.getenv("LINK_WINDOW_MINUTES", "60"))`
- [ ] `def normalize_sender(sender) -> str` — cast to `str`, `.strip().lower()`
- [ ] `async def resolve_and_stamp(user_id, source, sender, received_at) -> tuple[str | None, str | None]`
  - [ ] candidate = `find_one({user_id, source, sender: normalized, state: "active",
        received_at: {$gte: received_at - timedelta(minutes=window)}}, sort received_at desc)`
  - [ ] none → `(None, None)`
  - [ ] candidate has `threadId` → `(candidate["threadId"], candidate["threadId"])`
  - [ ] else anchor: `thread_id = str(candidate["_id"])`; `update_one({"_id":
        candidate["_id"], "user_id": user_id}, {"$set": {"threadId": thread_id,
        "conversationId": thread_id}})`; return `(thread_id, thread_id)`
- [ ] Idempotency note: anchor stamp uses a guarded `find_one_and_update` so a
      duplicate delivery cannot double-stamp (single-user FYP scope)

**Checkpoint**: pure/logic cases verified against a fake in-memory
collection; `normalize_sender("  Ali  ") == "ali"`.

### Step 2 — Model fields + indexes (nothing breaks when empty)

Modify `backend/models/message.py`:

- [ ] `class ContextUpdate(BaseModel)`: `field: str`, `value: str`,
      `source_message_id: str`, `reason: str`, `applied_at: datetime`
- [ ] `MessageResponse` gains `messageId: Optional[str]`, `threadId:
      Optional[str]`, `conversationId: Optional[str]` — additive defaults
- [ ] `message_doc_to_response` maps them (`messageId` defaults to
      `str(doc["_id"])`; `threadId`/`conversationId` from `doc.get`)

Modify `backend/main.py` lifespan:

- [ ] `messages_collection.create_index([("user_id", 1),
      ("conversationId", 1), ("received_at", -1)])`
- [ ] `messages_collection.create_index([("user_id", 1), ("threadId", 1),
      ("received_at", -1)])`
      (constitution's `receivedAt` concept is realized by the existing
      `received_at` field — see `research.md`)

**Checkpoint**: existing `test_messages.py` shape unchanged; new fields
return without the fields set back at `None`.

### Step 3 — Resolve and store ids at both ingestion entry points

Modify `backend/services/webhook_ingest.py`:

- [ ] `ingest_message(...)`: before insert, `thread_id, conversation_id =
      await resolve_and_stamp(user_id, source, sender, now)`; add
      `messageId`, and (when linked) `threadId`/`conversationId` to `doc`
- [ ] pass `thread_id` into the background task:
      `background_tasks.add_task(_analyze_and_store, content, message_id,
      user_id, thread_id)`
- [ ] `_analyze_and_store(content, message_id, user_id, thread_id=None)`
      forwards it to `process_message`

Modify `backend/routes/messages.py`:

- [ ] `create_message`: same resolve+store; call
      `process_message(payload.content, message_id=..., user_id=...,
      thread_id=thread_id)`

**Checkpoint**: `POST /messages` and the simulate webhook persist
`messageId` always and `threadId`/`conversationId` only when a link exists;
`hi` as a second message still gets a `threadId` and zero-cost analysis.

### Step 4 — Context into the single call (provider + analyzer)

Modify `backend/services/ai/providers/base.py`:

- [ ] `AIAnalysisResult` gains `context_updates: list[dict] = []`
- [ ] `async analyze(self, message: str, context: list[dict] | None = None)`:
      default keeps the current signature behavior (zero change when
      `context is None`)

Modify `backend/services/ai/providers/groq.py`:

- [ ] Add a `CONTEXT_BLOCK_TEMPLATE` section to `ANALYSIS_PROMPT` rendered
      only when context is present (`.replace("{context}", ...)`, same
      brace-safe pattern as `{message}`)
- [ ] Prompt rules: context may add a missing deadline/urgency; MUST NOT
      override an explicit statement in the current message; MAY emit
      `context_updates` referencing the context message handles; NEVER
      invent values not present in the linked messages
- [ ] Parse `context_updates` out of the JSON (default `[]`); keep
      `normalize_priority`/`clean_response` untouched

Modify `backend/services/ai/providers/openai.py`:

- [ ] Same `analyze(message, context=None)` signature and best-effort
      `context_updates` passthrough (provider-neutral, zero behavior change
      without context)

Modify `backend/services/ai/analyzer.py`:

- [ ] `analyze_message(..., context_messages: list[dict] | None = None)` →
      forward to `provider.analyze(message_content, context=context_messages)`
- [ ] include `context_updates: list(result.context_updates)` in the
      returned analysis dict (consumed by `context.apply...`, never stored
      verbatim on the current message)

**Checkpoint**: mocked provider proves `analyze` is awaited exactly once
with context; `context=None` renders the prompt byte-identical to today.

### Step 5 — Create `backend/services/ai/context.py` (fetch + validate + apply)

New module:

- [ ] `async def fetch_thread_context(user_id, thread_id, exclude_message_id,
      limit=5) -> list[dict]` — `find({user_id, threadId}, sort received_at
      desc)` limit `limit`; filter out `_id == exclude_message_id`; enrich
      each with a short `handle` (`str(_id)[-7:]`) and `sender`/`content`/
      `received_at`
- [ ] `def build_context_block(messages) -> str | None` — bounded text: for
      each, `[handle] <sender> (<received_at iso>): <content>`; `None` when
      empty
- [ ] `def _handle_to_id(handle, messages) -> str | None` — exact-match
      mapping back to a real `_id`
- [ ] `def validate_context_updates(candidates, thread_messages,
      current_message_id) -> list[dict]` — drop entries whose target/source
      handle maps to no real thread message, whose target is the current
      message, whose `field` is not in `{"deadline","priority","note"}`, or
      whose literal `value` does not appear in the source message's `content`
- [ ] `async def apply_context_updates(valid_updates, current_message_id,
      user_id) -> int` — for each, `messages_collection.update_one(
      {"_id": target, "user_id": user_id},
      {"$push": {"ai_analysis.context_updates": {"field", "value",
      "source_message_id", "reason", "applied_at"}}})`; return count applied

**Checkpoint**: forged/self/absent-value candidates are dropped; only
same-thread, same-user targets receive writes.

### Step 6 — Wire the Orchestrator (no new entry points)

Modify `backend/services/ai/orchestrate.py`:

- [ ] `async def process_message(content, message_id=None, user_id=None,
      message_type="text", thread_id=None)` — additive, default None
- [ ] analysis branch only (`routing.needs_llm and routing.needs_analysis`):
      - [ ] `context = await fetch_thread_context(user_id, thread_id,
            exclude_message_id=message_id)` when `thread_id`
      - [ ] `analysis = await _analyze_with_fallback(..., context_messages=context)`
      - [ ] post-call: `valid = validate_context_updates(
            analysis.get("context_updates"), context, message_id)` then
            `await apply_context_updates(valid, message_id, user_id)` inside
            its own try/except (never raises, never blocks)
      - [ ] pop `context_updates` from the current message's stored analysis
            (it is applied outward, not stored here)
- [ ] trivial/skip/routing-record paths unchanged

**Checkpoint**: full chain on the report/meeting example stores
`threadId` on both messages and a validated, reason-bearing
`context_updates` item on the report message; provider is awaited exactly
once.

### Step 7 — `backend/tests/test_threads.py` (link rule + quality bar)

- [ ] Pure unit cases: normalsender, window boundary at exactly 60 min
      (link) and 60:01 (no link), different sender, different channel,
      first message (no thread), anchor stamping (threadId == anchor _id),
      inherit from a stamped thread
- [ ] **Labeled set of 30 pairs** (table-driven, feeds SC-002/SC-003):
      mix of same-sender in-window (≥80% expected linked incl. the required
      related pairs), different sender / channel / out-of-window (all must be
      NOT linked → false-link rate ≤ 5%)
- [ ] Isolation test: two users, same channel/sender/window → separate
      threads, neither thread contains the other user's messages (SC-007)
- [ ] Ambiguity: third message with two candidate strands defaults to the
      latest consecutive arrival (documented decision, not a false claim)

**Checkpoint**: compute and print the false-link % and recall % from the
labeled set — both meet the constitution quality bar.

### Step 8 — `backend/tests/test_context_ai.py` (context + validation)

- [ ] Context block only when context present; `context=None` → prompt
      byte-identical (SC-005 regression guard)
- [ ] Provider invoked exactly ONCE with context (SC-006)
- [ ] `context_updates` round-trip parsed from a mocked provider response
- [ ] Validation drops: unknown target handle, target == current message,
      disallowed field, value absent from source content, unknown source
- [ ] `apply_context_updates` writes only to same-user, same-thread targets
      with a reason naming the source message (SC-004 / FR-009)
- [ ] Trivial path with a thread_id still pays ZERO calls (Day 24 preserved)
- [ ] Provider failure on a linked message → pending fallback, link metadata
      intact (FR-012)

### Step 9 — Integration coverage + regression

- [ ] `backend/tests/test_messages.py` — `POST /messages` response includes
      `messageId`/`threadId`/`conversationId`; standalone identical shape;
      linked pair shares `threadId` and earlier message gains
      `context_updates` (US1)
- [ ] `backend/tests/test_webhooks.py` — simulate ingestion persists the
      three fields; a linked pair enriches the earlier message (US1)
- [ ] Existing single-message + attention + task tests pass unchanged
      (SC-005 no regression)
- [ ] Two-user isolation flow still passes (SC-007)

### Step 10 — Full suite + manual dashboard pass

- [ ] `cd backend && python -m pytest tests/ -q` — all green (300s shell
      timeout)
- [ ] Manually via quickstart.md: (i) standalone message → identical card
      to today; (ii) send "Can you send the report?" then "Need it before
      our meeting." → same thread, earlier task shows an explainable
      deadline update naming the follow-up; (iii) different-sender message →
      independent; confirm MongoDB stores the fields and the Dashboard
      renders identically with no nulls

## Testing Plan

**Automated (pytest)** — the matrix in Steps 7–9 covers: the deterministic
link rule across the decision table, the 30-pair labeled set that directly
measures the constitution's false-link (≤5%) and recall (≥80%) bars,
inter-user isolation, anchor stamping vs inheritance, context-block
presence/absence (byte-compat when None), the single-call guarantee (provider
invocation counted), context-update validation (forged/self/unproven values
dropped), outward application with named reasons, and zero regression on the
existing single-message test set.

**Provider mocking** — never hit the real LLM: monkeypatch
`GroqProvider.analyze` with a canned `AIAnalysisResult` (optionally
containing `context_updates`) and count invocations to prove the call budget.

**Labeled-set discipline** — the 30 pairs live as a table in
`test_threads.py` and double as the compliance evidence for SC-002/SC-003;
each pair states its expected link so the suite is self-verifying.

**Manual end-to-end (no code)**: run the backend, use the simulate form for
the report→meeting sequence, a standalone greeting, and a different-sender
case; verify identity fields and `context_updates` in MongoDB and that every
Dashboard card renders purely from stored results.

## Definition of Done

A feature is DONE when:

1. ✅ 100% of messages store a server-set `messageId`; linked messages store
   `threadId` (= anchor message id) and `conversationId` (= `threadId`);
   unlinked messages store `threadId`/`conversationId` as null
   (spec SC-001 / FR-001/003/004)
2. ✅ Linking is deterministic only — no AI grouping anywhere; the labeled
   30-pair suite reports ≤5% false links and ≥80% recall
   (spec SC-002/003)
3. ✅ Identity fields are set server-side at ingest and never accepted from
   the client (spec FR-005)
4. ✅ Threads never span users; the two-user isolation test passes and no
   context fetch or update can touch another user's messages
   (spec FR-006/014, SC-007)
5. ✅ Context is at most the 5 most recent same-user thread messages and
   rides the existing single analysis call — provider-call-count test reports
   exactly one call on the analyze path (spec FR-007/008, SC-006)
6. ✅ Any context effect is validated against the thread and stored as an
   explainable revision with a reason naming the linked message; original
   wording is never overwritten (spec FR-009, US4)
7. ✅ An explicitly stated user fact wins over inferred context (spec
   FR-010)
8. ✅ Standalone messages produce stored analysis and Dashboard cards
   identical to today; the existing single-message test set passes unchanged
   (spec FR-011/013, SC-005)
9. ✅ Link/context resolution failure never blocks ingestion or analysis —
   the message is stored and analyzed standalone (spec FR-012)
10. ✅ No memory framework exists — no vector store, embeddings, or RAG
    imports/components (code-level grep) (spec FR-015, SC-008)
11. ✅ `routing` records, priority, NEEDS ATTENTION, and all Day 24
    behaviors are unchanged for non-context messages (Day 24 regression)

## Complexity Tracking

No violations. No complexity tracking needed.