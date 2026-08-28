# Research: AI Orchestrator (Day 24)

**Feature**: 015-ai-orchestrator
**Date**: 2026-08-29
**Phase**: 0 (Research)

## 1. Problem Definition

Day 18–21 built five AI "agents" that all run inside ONE combined LLM call for
every new message: Priority, Summary, Task Extraction, Deadline Detection, and
Recommended Action. Every message pays the full cost, and the stored result
always materializes all five outputs. Day 24 adds a rule-based orchestrator
that first decides which of those agents even matter for a given message, then
executes the **smallest sufficient subset** while producing one combined
result the Dashboard can render unchanged.

Constraints (constitution, v1.12.0 Day 24 section):

| Constraint | Meaning |
|---|---|
| Single call | The five agents still share ONE LLM call — routing adds no round-trips |
| Priority never skipped | Every analyzed message gets a priority |
| Explainable | `routing` record saved per message with run/skip + reason |
| Trivial = cheap | Greetings/acknowledgements must skip the LLM entirely |
| Rule-based first | Deterministic rules, not another model, drive routing |
| Fail toward completeness | Anything ambiguous → full analysis |
| One layer | No scattered/direct calls outside the Orchestrator |

## 2. Key Architectural Facts (from code)

- `backend/services/ai/analyzer.py::analyze_message(content, message_id,
  user_id)` is the single-call pipeline: one `GroqProvider.analyze()` request
  → `AIAnalysisResult` (priority, confidence, explanation, summary,
  tasks_extracted, deadlines, recommended_action, recommended_actions) →
  `evaluate_attention(analysis)` adds `needs_attention`/`attention_reason` →
  tasks inserted via `tasks_collection`.
- `attention.py::evaluate_attention` uses rule-based keyword signals already
  (NEAR_TERM_KEYWORDS) — reusable, not an LLM.
- Analysis is triggered from exactly two places: `webhook_ingest.py`'
  `_analyze_and_store` (background task after webhook/simulate ingests) and
  `routes/messages.py::create_message` (manual `POST /messages`).
- Storage: `ai_analysis` is stored on the `messages` document; response models
  (`models/message.py::MessageResponse`) carry `ai_analysis` through
  `AIAnalysis(**doc)`. Pydantic 2 ignores undeclared keys, so exposing the
  record requires declaring `routing` on `AIAnalysis` (additive, defaulted —
  Dashboard reads only fields it already knows).
- No existing routing/orchestration concept exists anywhere (confirmed by
  grep).

## 3. Decisions

### 3.1 Routing is selection, not per-agent work

**Decision**: The Orchestrator never calls providers per agent. It selects
which outputs are **kept** (gating after one call) and whether extracted tasks
are **persisted** (a `run_tasks` flag into `analyze_message`). A skipped agent
thus costs nothing beyond clearing fields — it never spawns traffic.

**Alternatives rejected**:
- **Per-agent calls (real orchestrator frameworks)**: multiply LLM cost —
  banned by the single-call rule.
- **Hint-parameter into the prompt (function calling / per-agent prompt
  variants)**: changes the shared prompt and risks degrading the combined
  result; gating after the existing call is lower-risk and keeps SC-004
  (zero added calls) provable by counting provider invocations.
- **Pure post-processing with no task-persistence gate**: tasks would still
  be written to MongoDB when Task Extraction is off — a correctness issue,
  so persistence gating is required in addition to field gating.

### 3.2 Rule-based signals

**Decision**: Routing uses four cheap rule families, all pure functions (no
I/O, no LLM, `re` + `unicodedata` only):

1. **Content absent** (`message_type == "media"` or `content` blank after
   strip) → `needs_analysis=False` → skip, stub result.
2. **Trivial detection** — whitespace-normalized exact match against
   `TRIVIAL_PHRASES` ("ok", "hi", "thanks", "sounds good", ...), OR a very
   short message (≤ 20 chars) with no task/time trigger → run but `needs_llm=False`.
3. **Task trigger** — lowercase keyword substring set: send, call, review,
   submit, prepare, confirm, update, reply, fix, finish, share, book, pay,
   remind, follow-up, let me know, ... → Task Extraction + Recommended Action on.
4. **Time expression** — tonight, today, tomorrow, asap, immediately, right
   now, this week, next week, next month, by <weekday>, EOD, ... (reusing
   `attention.NEAR_TERM_KEYWORDS` overlap) → Deadline Detection on.
5. **Script detection** — any character outside Latin (Arabic/Cyrillic etc.
   via `unicodedata`) → FULL default (`TRIGGER` to run everything) because
   keyword sets are tuned for English and untrusted otherwise.

**Why exact/phrase rules, not frequencies**: the vocabulary is small and the
demo corpus is tiny; a transcript like "أرسل الملفات" (Arabic) must not be
misrouted by substring luck. Failing toward full analysis is the safe default
and matches the spec's edge cases (EC-06, EC-09).

### 3.3 Trivial messages produce deterministic defaults

**Decision**: When `needs_llm=False` the Orchestrator builds the result
without any provider call: priority `normal`, confidence `0.5`, explanation
"Trivial message — deep analysis skipped by orchestrator.", summary = content
(when non-empty; `None` otherwise), empty tasks/deadlines/actions,
`provider="rule-based"`, `status="completed"`. The Dashboard renders this
exactly like today's completed card — no UI change.

### 3.4 Relation to the Attention rules

**Decision**: `evaluate_attention` keeps running on the **gated** analysis
(i.e. after skipped outputs are cleared). Attention flags must reflect what is
actually stored — otherwise a "follow up today" phrase stripped of its
deadline could still flag the thread. Because attention is already rule-based
and reuses the near-term keyword list, Deadline Detection and Attention
signals stay consistent without extra code.

### 3.5 Failure vs skip must be distinguishable

**Decision**: Three `ai_analysis.status` values are now possible:
`"completed"` (analyzed or trivial), `"pending"` (LLM failed; existing
fallback preserved), `"skipped"` (no analyzable content). `routing` also
records `llm_call_used=True` for the pending case, so a UI/inspection can tell
a deliberate skip from a failed analysis (spec FR-009).

### 3.6 One entry point

**Decision**: `orchestrate.process_message(content, message_id, user_id,
message_type)` is the ONLY caller of the AI pipeline. `analyze_message`
remains exported for tests but gains `run_tasks`; both ingestion sinks
(`_analyze_and_store`, `create_message`) redirect to the Orchestrator.
Grep-verifiable: no other `analyze_message` call sites exist post-change.

## 4. Code Inventory (what Day 24 touches)

| Path | Change |
|---|---|
| `backend/services/ai/routing.py` (NEW) | Pure signals + `decide_routing()` |
| `backend/services/ai/orchestrate.py` (NEW) | `process_message()` entry + deterministic defaults + gating + routing record |
| `backend/services/ai/analyzer.py` | `run_tasks` param; task insert gated; `_gate_outputs()`; attention after gating |
| `backend/services/ai/__init__.py` | Export `process_message` |
| `backend/services/webhook_ingest.py` | Background task calls Orchestrator |
| `backend/routes/messages.py` | `create_message` calls Orchestrator |
| `backend/models/message.py` | NEW `RoutingRecord` model; `AIAnalysis.routing` declared field (Pydantic 2 otherwise drops it) |
| `backend/tests/test_orchestrator.py` (NEW) | Decision table + call-count + gating + persistence-gate tests |
| `backend/tests/test_webhooks.py`, `backend/tests/test_messages.py` | Assert `ai_analysis.routing` present |
| `backend/test_task_extraction.py`, `backend/test_attention_pipeline.py` | Regression (full default routing) |
| `docs/AGENTS.md` / `AGENTS.md` | Agent context refresh (auto) |
| frontend | NO changes |

## 5. Key Risks / Mitigations

| Risk | Mitigation |
|---|---|
| Over-eager trivial skip misroutes a real request (e.g. a 2-char order) | Exact-match phrase list + short-length rule only fires when NO triggers present; ambiguous → full analysis |
| Arabic/long-message input lands in the wrong bucket | `unicodedata` script check forces full default |
| Task docs written when Task Extraction was skipped | `run_tasks` gate at the persistence site, not post-filtering |
| LLM failure masked as a skip (or vice versa) | `status: "pending"` + `routing.llm_call_used=True` distinguishes |
| Adding `routing` breaks the Dashboard | Response models pass `ai_analysis` through; field is additive; manual dashboard pass at Step 7 |
| Rule drift vs `attention.NEAR_TERM_KEYWORDS` | Time-signal set recomputed from the same list where they overlap |
| No live LLM in CI | Mocked `GroqProvider.analyze` with invocation counter |

## 6. Open Questions → Handled at Build Time (no blockers)

- Whether a genuine WhatsApp short order ("1  please") should be trivial-
  skipped — resolved by rule: short-but-with-digit/task-heuristic? NO: keep ≤20
  chars + no triggers = trivial; a real order usually contains a trigger
  ("send", "order", "please get"); manual dashboard pass validates the sample.
- Exact tail of `TRIVIAL_PHRASES` for the demo corpus — build-time tuning; the
  decision table tests pin the behavior regardless of vocabulary drift.

## Summary of Decisions

| Area | Decision | Key Reason |
|---|---|---|
| Architecture | Selection+single-call (rule-based orchestrator wrap) | Single-call constraint & SC-004 |
| Way to decide | Pure rule signals: absent/trivial/task/time/script | Testable, cheap, fuzzy-safe |
| Agent execution | One combined call; gate kept outputs + gate task persistence | Never multiplies calls; no orphan tasks |
| Trivial path | Deterministic defaults, 0 calls, status completed | Cheap + Dashboard-compatible |
| Attention | Applied after gating | Flags reflect stored state |
| Failure handling | `pending` + `llm_call_used=True` ≠ `skipped` | Explainability (FR-009) |
| Entry | Orchestrator is the only AI caller | One layer rule, grep-checkable |
| Frontend | None | Additive `routing` field only |