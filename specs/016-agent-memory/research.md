# Research: Agent Memory / Context (Day 25)

**Feature**: 016-agent-memory
**Date**: 2026-08-29
**Phase**: 0 (Research)

## 1. Problem Definition

Every message is currently analyzed in isolation. Day 25 lets the system
associate messages that clearly belong to one exchange and use that
association when analyzing them. The feature is deliberately **lightweight
memory, not a memory system**: a deterministic link rule, two additive
identity fields, and a bounded context note inside the existing single AI
call. It must never guess a link, never build a memory framework (no vector
store/embeddings/RAG), never cross users, and never change the Dashboard.

Constraints (constitution, v1.13.0 Day 25 section):

| Constraint | Meaning |
|---|---|
| Deterministic link only | Same user + source + sender + ≤60-min window; never AI-grouped |
| Server-set identity | `messageId` always; `threadId`/`conversationId` only when linked |
| Bounded context | ≤ 5 most recent same-user thread messages, inside the existing single call |
| Explainable enrichment | Context changes are validated and stored with a reason naming the linked message(s) |
| User facts win | Explicitly stated values beat inferred context (Day 11 mirror) |
| Idle by default | No link → analysis identical to today, zero extra cost |
| Isolation absolute | A thread never spans users |
| No memory framework | No vector store, embeddings, RAG, or conversation DB |
| Never block ingestion | Link/context failure → message handled standalone |

## 2. Key Architectural Facts (from code)

- `backend/services/webhook_ingest.py::ingest_message(user_id, source,
  sender, content, external_message_id, message_type, background_tasks)`
  builds the normalized doc and inserts it; duplicate deliveries return the
  existing id and **do not** re-run analysis. The AI pipeline runs in
  `_analyze_and_store(content, message_id, user_id)` (background task).
- `backend/routes/messages.py::create_message` (POST /messages) inserts the
  doc, then calls `process_message(content, message_id=str(_id), user_id)`
  synchronously and stores the returned `ai_analysis`.
- `backend/services/ai/orchestrate.py::process_message(content, message_id,
  user_id, message_type)` (Day 24) is the single AI entry point: `decide_routing`
  → trivial/skip paths produce deterministic defaults with ZERO calls;
  otherwise exactly one `analyze_message` call (`_analyze_with_fallback`),
  then a `routing` record is attached. Never raises.
- `backend/services/ai/analyzer.py::analyze_message(content, message_id,
  user_id, run_tasks, routing)` calls `provider.analyze(message_content)`
  once; `evaluate_attention` runs on the gated output. All storage is on the
  `messages` document; tasks go to `tasks_collection`.
- `GroqProvider.analyze(message)` (providers/groq.py) renders
  `ANALYSIS_PROMPT.replace("{message}", ...)` — `.replace`, not `.format`,
  because message content may contain braces. One LLM round-trip. Parity
  provider `openai.py` implements the same `BaseLLMProvider.analyze`.
- Indexes are declared in `backend/main.py` `lifespan` (users unique email,
  per-user `{user_id, created_at}`, text search, unique external_message_id,
  tasks, connections). New per-user thread/conversation indexes belong there.
- `MessageResponse` / `message_doc_to_response` (models/message.py) pass
  `ai_analysis` through `AIAnalysis(**doc)` — Pydantic 2 drops undeclared
  keys, so new `ai_analysis` sub-fields must be declared to surface (same
  lesson as Day 24's `routing`). `_id` is not exposed as `messageId` today
  (`id` is), so the constitution's `messageId` must be stored explicitly to
  keep the compliance check greppable.
- No thread/context concept exists anywhere (confirmed by grep). Circling:
  `received_at` is the arrival timestamp backing the constitution's
  `receivedAt`; `state: "active"` marks non-deleted documents.

## 3. Decisions

### 3.1 Link resolution happens at ingest, before insert — one indexed query

**Decision**: `services/threads.py::resolve_and_stamp(user_id, source,
sender, received_at)` runs inside both entry points (`ingest_message` and
`create_message`) before the message is inserted. It returns the link ids;
the caller stores them in the new doc. The query is one
`find_one({"user_id", "source", "sender": normalized, "state": "active",
"received_at": {"$gte": now - window}}, sort received_at desc)` — a
per-user `{user_id, threadId, received_at}` or `{user_id, received_at}`
index keeps it cheap, and it is the **only** extra read a linked message
pays (standalone messages pay the same query and find nothing).

**Alternatives rejected**:
- **Analyze-time linking via LLM**: banned — links must be deterministic and
  free (constitution Core Principle #1, quality bar cost).
- **`external_message_id`-based threads**: that id identifies deliveries, not
  conversations; it is provider-specific and absent for manual messages.
- **Retroactive full-history backfill**: out of scope; only the anchor
  stamp (a single, conservative, in-rule update) is allowed.

### 3.2 `threadId` = anchor message `_id`; `conversationId` = `threadId`

**Decision**: A thread is born on its **second** message. The candidate the
new message links to becomes the **anchor**: `threadId = str(anchor["_id"])`
(stable, deterministic, human-verifiable, never invented), stamped onto the
anchor and inherited by the new message. `conversationId` mirrors
`threadId` whenever a thread exists and is never otherwise set (constitution
Stored-Field Rules 2–3). A lone first message keeps `threadId = null`
(no speculation). Chain A→B→C works because the window is measured from the
thread's *latest* message, satisfying "close in time to the previous message
in the thread" for B→C even if A→C exceeds 60 minutes.

**Parallel strands**: with two candidate strands from one sender, the rule
links to the **most recent consecutive** arrival. This matches real chat
conversation shape and avoids interleaving heuristics; the spec's edge case
explicitly accepts default-to-consecutive over wrong-link.

**Alternatives rejected**:
- UUID `threadId` minted per message: breaks the determinism and adds a
  hidden state source; anchor id is self-verifying in MongoDB.
- `threadId = first(thread).messageId` with a separate threads collection:
  a threads collection is a second store with no behavioral benefit at
  single-user FYP scope (Simplicity First).

### 3.3 Field naming and index realization

**Decision**: Store the constitution's names literally — `messageId`,
`threadId`, `conversationId` — on the `messages` document. `_id` never
suffices for `messageId` because the API exposes it as `id` and the
compliance checklist wants a greppable field. The two mandated indexes use
the existing `received_at` column as the arrival timescale
(`{user_id, conversationId, received_at}` and `{user_id, threadId,
received_at}`); duplicating arrival time into a `receivedAt` copy would
violate Simplicity First. Documented in this research + data-model.

### 3.4 Context rides the existing single call — different prompt, same budget

**Decision**: `analyze_message` gains `context_messages` (formatted list of
≤5 same-user thread messages) forwarded to
`provider.analyze(message_content, context=context)`. The provider renders a
`CONTEXT — PREVIOUS MESSAGES IN THIS CONVERSATION` block into
`ANALYSIS_PROMPT` **only when context is present** (`.replace`, brace-safe),
with rules: may enrich a missing deadline/urgency; MUST NOT override an
explicit statement in the current message; may emit `context_updates`
referencing context-message handles; never invent values absent from the
linked messages. `context=None` leaves the prompt byte-identical → zero
regression for standalone messages (SC-005) and zero added round-trips on
every path (SC-006). Context is gathered only on the Orchestrator's analyze
branch (trivial/skip paths never touch it), preserving Day 24's cost model.

**Alternatives rejected**:
- A second "context call": doubles LLM cost — banned.
- Separate per-agent context (vector store of past analyses): the no-memory-
  framework rule + cost.
- Always-render an empty context section: changes the prompt for standalone
  messages → breaks the regression guard.

### 3.5 Context effects are validated and applied outward — never silently

**Decision**: `services/ai/context.py` owns three pure/thin steps:
`validate_context_updates` drops any suggestion whose target/source handle
is not a real message in THIS thread, whose target is the message currently
being analyzed, whose `field` is outside `{deadline, priority, note}`, or
whose literal `value` does not appear in the source message's content. Valid
updates are applied with `apply_context_updates` via
`update_one({"_id": target, "user_id": user}, {"$push":
{"ai_analysis.context_updates": {field, value, source_message_id, reason,
applied_at}}})` — a new, explainable revision on the **earlier** message.
Original analysis fields are never overwritten (US4: "original wording is
never silently overwritten"). The current message's own `context_updates`
key is popped before its analysis is stored (it is applied outward, not
self-stored). All writes are user-scoped → a context effect can never touch
another user's or another thread's messages.

**Security note**: `_handle_to_id` maps only against the fetched thread
messages (which are already scoped by `user_id` + `threadId`), so a forged
handle cannot reach an arbitrary document.

### 3.6 Failure handling

**Decision**: Linking and context are **never** in the critical path of
analysis success. `resolve_and_stamp` runs before insert; if it raises, the
exception is caught at the call site and the message is stored standalone
(log line; `process_message` unaffected). Context fetch/validate/apply are
wrapped in their own try/except inside the Orchestrator's analyze branch —
provider failure, missing thread, or DB hiccup degrades to today's `pending`
fallback with link metadata intact (FR-012 / Progressive Enhancement).

## 4. Code Inventory (what Day 25 touches)

| Path | Change |
|---|---|
| `backend/services/threads.py` (NEW) | `LINK_WINDOW_MINUTES`, `normalize_sender`, `resolve_and_stamp` |
| `backend/services/ai/context.py` (NEW) | `fetch_thread_context`, `build_context_block`, `validate_context_updates`, `_handle_to_id`, `apply_context_updates` |
| `backend/services/ai/orchestrate.py` | `thread_id` param; gather+inject context; validate+apply; pop `context_updates` |
| `backend/services/ai/analyzer.py` | `context_messages` param → provider; `context_updates` passthrough |
| `backend/services/ai/providers/base.py` | `analyze(message, context=None)`; `AIAnalysisResult.context_updates` |
| `backend/services/ai/providers/groq.py` | `CONTEXT` prompt block + parse `context_updates` |
| `backend/services/ai/providers/openai.py` | signature parity, best-effort `context_updates` |
| `backend/services/webhook_ingest.py` | resolve+store ids; background task passes `thread_id` |
| `backend/routes/messages.py` | `create_message` resolve+store ids; pass `thread_id` |
| `backend/models/message.py` | `ContextUpdate`; `MessageResponse` + 3 fields; doc mapping |
| `backend/main.py` | two per-user thread/conversation indexes |
| `backend/tests/test_threads.py` (NEW) | link rule + 30-pair labeled set + isolation |
| `backend/tests/test_context_ai.py` (NEW) | prompt injection, validation, single-call, failures |
| `backend/tests/test_messages.py`, `test_webhooks.py` | identity fields; linked-pair enrichment; regression |
| `docs/AGENTS.md` / `AGENTS.md` | Agent context refresh (auto via update-agent-context.ps1) |
| frontend | NO changes |

## 5. Key Risks / Mitigations

| Risk | Mitigation |
|---|---|
| False link groups a real, unrelated message (precision) | Deterministic rule + 30-pair labeled suite with ≤5% false-link bar |
| Missed link (recall) fails the follow-up use case | ≥80% recall bar on same-sender in-window pairs; anchor-chain rule keeps A→B→C links |
| Context prompt drifts / changes standalone output | `CONTEXT` block rendered only when context present; byte-compat test when None |
| Model emits unlabelled/fabricated `context_updates` | Backend validation against real thread messages (target membership + literal value check); "0 tolerance for unlabelled influence" via drop + log |
| Enrichment overwrites an earlier message silently | Outward `$push` revisions only; original fields untouched; reason always names the source message |
| Context overrides a user-stated deadline | Prompt rule (explicit statements win) + backend keeps original fields (`context_updates` is additive) |
| Thread violates isolation (two users, same channel) | Every query/update is `user_id`-scoped; two-user isolation test |
| Link query slows standalone ingest | Same single indexed query every message already pays to find its thread; no extra cost when none matches |
| MongoDB stamp/handle race on duplicate delivery | Anchor stamp uses guarded `update_one` scoped to `(user_id, _id)`; DuplicateKey path already returns before linking |
| No live LLM in CI | Mocked `GroqProvider.analyze` with invocation counter |

## 6. Open Questions → Handled at Build Time (no blockers)

- Whether a *first* in-window pair should use anchor `_id` vs a prefixed id —
  resolved: anchor `_id` raw string (self-verifying; no prefix invented).
- Exact render shape of the `CONTEXT` block and the `context_updates` JSON —
  build-time; both live behind `context.py` and the provider parser so the
  prompt contract test pins them.
- Whether the window's 60-minute default needs tuning for the demo corpus —
  env-overridable (`LINK_WINDOW_MINUTES`), architecture unaffected.

## Summary of Decisions

| Area | Decision | Key Reason |
|---|---|---|
| When to link | At ingest, one indexed query, before insert | Deterministic, free, no AI grouping |
| Identity fields | `messageId` = `_id` (stored literally); `threadId` = anchor `_id`; `conversationId` = `threadId` | Greppable compliance; never invented; stable |
| Thread shape | Snowball via latest-message window (A→B→C stays linked) | Matches constitution Core Principle #1 |
| Context | ≤5 recent msgs inside existing single call | Zero added round-trips (SC-006) |
| Enrichment | Validate against thread, then `$push` explainable revision | "0 tolerance unlabelled"; original wording preserved |
| Failure | Catch everywhere; link/context never blocks ingestion | Progressive Enhancement (FR-012) |
| Frontend | None | Additive fields only (FR-013) |
| Memory framework | None (no vector store/embeddings/RAG) | Constitution rule + SC-008 |

## NEEDS CLARIFICATION Check

Resolved from the constitution (v1.13.0 Day 25 section) and the spec — there
are **no** open `NEEDS CLARIFICATION` items requiring the user: the link
window, the context cap, the identity fields, the indexes, the validation
bar, and the quality metrics are all fixed by the ratified text. Phase 1 can
proceed.