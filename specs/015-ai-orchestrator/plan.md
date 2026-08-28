# Implementation Plan: AI Orchestrator (Day 24)

**Branch**: `015-ai-orchestrator` | **Date**: 2026-08-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/015-ai-orchestrator/spec.md`

## Summary

Add a single, rule-based **AI Orchestrator** between message ingestion and the
existing five agents (Priority, Summary, Task Extraction, Deadline Detection,
Recommended Action). For each new message the Orchestrator decides whether
analysis is needed, which agents contribute, whether an AI call is required,
and the execution order — then stores one combined result plus an explainable
`routing` record. The Dashboard is untouched.

```text
Message → ingest (Day 23) → Orchestrator: what do we need to know?
  → decide agents (pure rules, 0 LLM)
  → trivial/skipped: deterministic defaults, 0 AI calls
  → otherwise: 1 combined AI call (existing single-call prompt)
  → gate outputs by routing decision → attention (unchanged rules)
  → ai_analysis + routing → MongoDB → Dashboard (unchanged)
```

The key design choice is **routing = selection, not extra work**: the
Orchestrator preserves the constitution's single-AI-call constraint by
deciding which outputs are produced/kept (and which stored `tasks` are
persisted), never by spawning per-agent calls. Trivial messages skip the LLM
entirely. Everything is pure, testable, and confined to two new modules plus
small call-site changes.

## Technical Context

**Language/Version**: Python 3.13
**Primary Dependencies**: pytests, `unicodedata` (stdlib) for script
detection, `re` (stdlib) for keyword signals — **no new runtime
dependencies** (stock: FastAPI, motor, groq, pydantic)
**Storage**: MongoDB `messages` collection — `ai_analysis` gains a
`routing` subdocument; no schema migration (Pydantic `MessageResponse`
passes `ai_analysis` through unchanged)
**Testing**: pytest + httpx TestClient (existing suite) — new unit tests for
`routing.py` and a new `test_orchestrator.py`; no live-LLM dependency (mocked
`GroqProvider`)
**Target Platform**: Local development (FastAPI backend, Next.js frontend)
**Project Type**: Web application (frontend + backend)
**Performance Goals**: Total time arrival → stored result stays ≤ 10s;
trivial messages complete with ZERO AI calls and well under that budget
**Constraints**: No additional LLM round-trips per message (constitution
Complete AI Pipeline rule); Priority always runs; routing decisions MUST be
recorded (explainability); Dashboard contract unchanged; user isolation
unchanged
**Scale/Scope**: Single demo user; five fixed agents; rule-based routing only

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle / Rule | Status | Notes |
|---|---|---|
| I. Simplicity First | ✅ PASS | One routing module (pure functions) + one thin orchestrator wrapper; no agent classes, no framework |
| II. Vertical Slices | ✅ PASS | Complete slice: ingest → orchestrator → agents → stored result → dashboard card |
| III. AI is Assistive | ✅ PASS | Every decision recorded in a `routing` note (skip reasons, triggers, LLM used) — nothing hidden |
| IV. User Control | ✅ PASS | Same commits: output stays advisory; dashboard interaction unchanged |
| V. Security and Privacy | ✅ PASS | No new PII handling; routing operates on already-owned messages; isolation untouched |
| VI. Clean Code | ✅ PASS | Routing = pure functions; reuses `analyze_message`, `evaluate_attention`, existing prompts |
| VII. Progressive Enhancement | ✅ PASS | Skipped/trivial messages still render (stub `ai_analysis`); LLM failure fallback preserved |
| Day 18 User Isolation | ✅ PASS | Orchestrator receives `user_id` server-side; never derives or crosses user boundaries |
| Day 23 Webhook Rules | ✅ PASS | Ingestion path unchanged; only the analysis call behind `_analyze_and_store` is replaced |
| Complete AI Pipeline | ✅ PASS | Single LLM call preserved; fixed order kept (priority first, recommended action last) among *selected* agents |
| Day 24 Orchestrator | ✅ PASS | This plan implements the new section: rule-based first, minimal subset, trivial skip, explainable routing |

**No violations. No complexity tracking needed.**

## Project Structure

### Documentation (this feature)

```text
specs/015-ai-orchestrator/
├── plan.md              # This file
├── spec.md              # Feature spec (/sp.specify output)
├── research.md          # Phase 0: routing strategy + gating decisions
├── data-model.md        # Phase 1: ai_analysis + routing record shape
├── quickstart.md        # Phase 1: Day 24 runbook
├── contracts/           # Phase 1: stored-analysis contract + unchanged endpoints
│   └── ai-analysis-contract.md
└── tasks.md             # Phase 2: NOT created by /sp.plan
```

### Source Code (repository root)

```text
backend/
├── models/
│   └── message.py                   # UPDATE — new RoutingRecord model; AIAnalysis.routing field
├── services/
│   ├── ai/
│   │   ├── routing.py               # NEW — pure signal detection + decide_routing()
│   │   ├── orchestrate.py           # NEW — process_message() entry point
│   │   ├── analyzer.py              # UPDATE — add run_tasks param; task insert gated
│   │   └── __init__.py              # UPDATE — export orchestrator.process_message
│   └── webhook_ingest.py            # UPDATE — call orchestrator instead of analyze_message
├── routes/
│   └── messages.py                  # UPDATE — POST /messages calls orchestrator
└── tests/
    ├── test_orchestrator.py         # NEW — routing, gating, trivial-skip, single-call
    └── test_webhooks.py             # UPDATE — background task persists routing record

frontend/
└──  (no changes — Dashboard reads stored ai_analysis; routing is additive)
```

**Structure Decision**: Web application layout. All Day 24 logic stays inside
`backend/services/ai/` beside the existing agents. New code is two modules
(`routing.py`, `orchestrate.py`); existing entry points (`webhook_ingest`,
`routes/messages.py`) get one-line call swaps. Zero frontend changes.

## Technical Approach

1. **Rule-based routing first.** A new pure module `routing.py` decides for a
   message: needs analysis? which agents? needs LLM? It uses cheap signals:
   content length, exact-match trivial phrases, task-trigger keywords,
   time-expression keywords, and script detection (`unicodedata`) to catch
   non-Latin (Arabic) content that must default to full analysis. Zero I/O,
   zero LLM — fully unit-testable.
2. **Trivial messages skip the LLM.** Greetings/acknowledgements ("ok",
   "hi", "thanks", ...) produce a deterministic result (priority `normal`,
   empty tasks/deadlines, honest summary-or-nothing, `recommended_action="")`
   in **zero** AI calls. Status `completed`, provider `rule-based`.
3. **Analyzed messages keep ONE call.** Non-trivial messages reuse the
   existing `GroqProvider.analyze` single-call prompt exactly as today —
   the Orchestrator adds no round-trips. Routing determines which outputs are
   **kept** (`_gate_outputs`) and whether extracted tasks are **persisted**
   (`run_tasks` flag into `analyze_message`).
4. **Output gating after the call.** If Task Extraction was not selected,
   `tasks_extracted` is cleared and no task documents are inserted. If
   Deadline Detection was not selected, `deadlines` is cleared. If Recommended
   Action was not selected, `recommended_action="")`. Priority and Summary are
   kept per routing. Attention (`evaluate_attention`, unchanged) runs on the
   **gated** analysis so flags reflect what is actually stored.
5. **One orchestration layer.** All AI entry points — the ingested-message
   background task and `POST /messages` — call `orchestrate.process_message`.
   Nothing else invokes `analyze_message` directly
   (`analyze_message` becomes an internal execution step used by the
   Orchestrator).
6. **Explainable routing record.** Every result carries
   `ai_analysis.routing` with `agents_run`, `agents_skipped`, `skip_reason`,
   `triggers`, `llm_call_used`, `decided_at`. Skipped (no analysis) vs failed
   (`status: "pending"`) are distinguishable. The Dashboard ignores the extra
   field.

### How the Orchestrator decides which agents run

| Message profile | Example | Action |
|---|---|---|
| No analyzable content | `""`, media-only | No analysis; stub `ai_analysis` with `status: "skipped"` |
| Trivial phrase | "ok", "hi", "thanks" | No LLM; deterministic defaults; `status: "completed"` |
| Action, no time expression | "Please call me" | LLM; Task Extraction on, Deadline off, Recommended on |
| Time expression, no action | "Meeting tomorrow" | LLM; Deadline on, Task Extraction off |
| Action + time expression | "Send the slides tonight" | LLM; full treatment (all five) |
| Long FYI, no triggers | peer-to-peer story | LLM; Priority + Summary on, others off |
| Arabic / mixed script | "أرسل الملفات" | Full analysis default (rules untrusted) |
| Anything ambiguous | — | Full analysis default (fail toward completeness) |

## Implementation Steps (in order)

### Step 1 — Create `backend/services/ai/routing.py`

New pure module (stdlib only):

- [ ] Signal constants: `TASK_TRIGGER_KEYWORDS` (send, review, submit,
      confirm, prepare, call, reply, update, fix, finish, share, book, pay,
      ...), `TIME_EXPRESSION_KEYWORDS` (tonight, today, tomorrow, asap,
      immediately, right now, this week, by [day], next week, next month,
      ..., reusing `attention.NEAR_TERM_KEYWORDS` where they overlap),
      `TRIVIAL_PHRASES` (ok, okay, hi, hello, hey, yes, no, yeah, thanks,
      thank you, ty, sure, done, bye, got it, sounds good, k, fine, ...)
- [ ] `def has_trigger(content, keywords) -> list[str]` — lowercased substring
      matches; returns the matched triggers
- [ ] `def has_non_latin_script(content) -> bool` — any char whose
      `unicodedata` category suggests Arabic/Cyrillic/etc.; forces full default
- [ ] `def looks_trivial(content, task_triggers, time_triggers) -> bool` —
      whitespace-normalized exact match in `TRIVIAL_PHRASES`, or very short
      (`≤ 20 chars`) with NO task/time triggers
- [ ] `@dataclass RoutingDecision`: `needs_analysis`, `needs_llm`,
      `run_summary`, `run_task_extraction`, `run_deadline_detection`,
      `run_recommended_action`, `reason`, `triggers`
- [ ] `def decide_routing(content, message_type="text") -> RoutingDecision`
      implementing the table above; ambiguous → all-on full default

**Checkpoint**: `decide_routing` is pure and importable; quick REPL cases
match the table.

### Step 2 — Extend the response model + gate the analyzer

Modify `backend/models/message.py`:

- [ ] Add `RoutingRecord` BaseModel: `agents_run: list[str]`,
      `agents_skipped: list[str]`, `skip_reason: str`,
      `triggers: list[str]`, `llm_call_used: bool`,
      `decided_at: datetime` (reuse `analysis_helpers.utc_now()` style)
- [ ] Declare `routing: Optional[RoutingRecord] = None` on `AIAnalysis`
      (Pydantic 2 drops undeclared keys on `AIAnalysis(**doc)`, so without
      this field `routing` would silently vanish from API responses)

Modify `backend/services/ai/analyzer.py`:

- [ ] Add `run_tasks: bool = True` parameter to `analyze_message(...)`; wrap
      the `tasks_collection.insert_many` block in `if run_tasks and
      result.tasks_extracted:` (a gateway so skipped Task Extraction never
      persists task documents)
- [ ] Add `_gate_outputs(analysis, routing) -> dict` — clears
      `tasks_extracted`, `deadlines`, `recommended_action` (and `summary`
      when `run_summary` false) per `RoutingDecision`
- [ ] Keep `evaluate_attention` applied AFTER gating so flags reflect the
      stored state
- [ ] Update the completion log line to include the routing decision

**Checkpoint**: Existing tests (`test_task_extraction.py`,
`test_attention_pipeline.py`) still pass with default `run_tasks=True` and a
no-op routing.

### Step 3 — Create `backend/services/ai/orchestrate.py`

New entry point:

- [ ] `def _deterministic_defaults(routing, message_type) -> dict` — trivial
      result (priority `normal`, confidence `0.5`, honest explanation, summary
      = content or `None`, empty tasks/deadlines/recs, provider
      `"rule-based"`, `status: "completed"`); skipped stub (priority
      `normal`, `status: "skipped"`)
- [ ] `async def process_message(content, message_id=None, user_id=None,
      message_type="text") -> dict`:
  - [ ] `routing = decide_routing(content, message_type)`
      - [ ] `not needs_analysis` → `_deterministic_defaults(routing, ...)`
      - [ ] `not needs_llm` → `_deterministic_defaults(routing, ...)`
      - [ ] else → `analysis = await analyze_message(content, message_id,
        user_id, run_tasks=routing.run_task_extraction)` then
        `analysis = _gate_outputs(analysis, routing)`
  - [ ] Attach `analysis["routing"] = {...agents_run, agents_skipped,
        skip_reason, triggers, llm_call_used, decided_at}` (agents_skipped
        derived from the five agents minus `agents_run`)
  - [ ] Return the final dict (never raises; `analyze_message` already
        degrades to `status: "pending"`)

**Checkpoint**: Manually exercising `process_message` with a stubbed provider
yields: trivial → zero provider calls; rich → exactly one; `routing` present
in both.

### Step 4 — Redirect ingestion + manual create to the Orchestrator

- [ ] `backend/services/webhook_ingest.py` — `_analyze_and_store` calls
      `orchestrate.process_message(content, message_id, user_id)` and
      persists the returned dict (unchanged persistence block)
- [ ] `backend/routes/messages.py` — `create_message` calls
      `orchestrate.process_message(payload.content, message_id, user_id)`
- [ ] `backend/services/ai/__init__.py` — export
      `process_message` from orchestrate (keep `analyze_message` export for
      existing tests)

**Checkpoint**: `POST /messages` and both webhook paths now store
`ai_analysis.routing`; `grep -rn "analyze_message"` shows only the
orchestrator and tests.

### Step 5 — Add `backend/tests/test_orchestrator.py`

- [ ] Routing unit tests (pure, table-driven):
  - [ ] trivial phrase → `needs_analysis=True, needs_llm=False`,
        task off, deadline off
  - [ ] "Please call me" → task on, deadline off, recommended on
  - [ ] "The meeting is tomorrow" → deadline on, task off
  - [ ] "Send the slides tonight" → all five on
  - [ ] long FYI, no triggers → priority+summary only
  - [ ] Arabic content → full default (all on)
  - [ ] empty / whitespace / media-only → `needs_analysis=False`
- [ ] Orchestrator tests (mocked provider, count calls):
  - [ ] trivial → `llm_call_used=False`; provider `analyze` never awaited
  - [ ] rich message → exactly one provider call
  - [ ] gating zeros non-selected outputs; attention reflects gated state
  - [ ] task persistence skipped when `run_task_extraction=False`
        (assert zero inserts into `tasks_collection`)
  - [ ] `routing` record present with correct `agents_run`/`agents_skipped`
  - [ ] provider failure → `status: "pending"` + routing marks
        `llm_call_used=True`, distinguishable from a skip

### Step 6 — Integration coverage + regression

- [ ] `backend/tests/test_webhooks.py` — assert background analysis persists
      `ai_analysis.routing` for an ingested simulate/whatsapp message
- [ ] `backend/tests/test_messages.py` — `POST /messages` response includes
      `ai_analysis.routing`; endpoint still returns 201 with existing shape
- [ ] `backend/test_task_extraction.py`, `backend/test_attention_pipeline.py`
      — unchanged behavior with default full routing (regression guard)

### Step 7 — Run the full suite + manual dashboard pass

- [ ] `cd backend && python -m pytest tests/ -q` — all green
- [ ] Standalone scripts (`test_ai_analysis.py`, `test_attention_pipeline.py`)
      still pass
- [ ] Manual Dashboard pass per quickstart.md — simulated + trivial message
      both render; cards identical to the previous day's UI

## Testing Plan

**Automated (pytest)** — the matrix in Step 5/6 covers: routing purity across
the decision table, zero-call trivial path, single-call enforcement, output
gating, task-persistence gating, routing-record integrity, failure-vs-skip
distinction, and no regressions in ingestion, attention, task extraction, or
the `POST /messages` shape.

**Provider mocking** — never hit the real LLM in tests: monkeypatch
`GroqProvider.analyze` (or `analyze_message`'s provider) with a canned
`AIAnalysisResult`, and count invocations to prove the call budget.

**Manual end-to-end (no code)**: run the backend, use the simulate form for
(i) `hi` → card renders, zero AI cost, `routing` shows skip reason
`trivial`; (ii) `Send me the slides tonight.` → full five-field analysis with
all agents in `agents_run`; (iii) a long FYI message → summary + priority only.
Verify each in MongoDB and on the Dashboard, and confirm the "NEEDS ATTENTION"
flag still fires only per the unchanged attention rules.

## Definition of Done

A feature is DONE when:

1. ✅ 100% of incoming messages route through `orchestrate.process_message` —
   grep confirms no other caller of `analyze_message` (spec SC-001/FR-013)
2. ✅ `decide_routing` is a pure function passing the full decision-table
   unit suite (spec SC-002)
3. ✅ Every analyzed message has priority; every processed message stores a
   `routing` record naming agents run/skipped + reason (spec SC-003/FR-009)
4. ✅ Trivial messages complete with ZERO AI calls and appear correctly on the
   Dashboard (spec SC-007/FR-002)
5. ✅ Analyzed messages cost exactly ONE AI call — no extra round-trips added
   (spec SC-004/FR-011)
6. ✅ Skipped agents store documented fallbacks; no invented tasks/deadlines/
   recommendations (spec SC-006)
7. ✅ Dashboard renders stored results only and is byte-compatible with the
   previous day (no frontend changes) (spec SC-005/FR-012)
8. ✅ Task documents are NOT created for messages where Task Extraction was
   skipped (spec FR-005)
9. ✅ Existing suite passes (`python -m pytest tests/ -q`) plus the new
   `test_orchestrator.py` (spec SC-008)
10. ✅ Simulated and real ingestion both persist `ai_analysis.routing` with
    user isolation unchanged (spec FR-014)

## Complexity Tracking

No violations. No complexity tracking needed.