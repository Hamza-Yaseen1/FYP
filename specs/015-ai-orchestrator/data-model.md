# Data Model: `ai_analysis.routing` Record + Skip Stubs

**Feature**: 015-ai-orchestrator | **Date**: 2026-08-29 | **Phase**: 1

## 1. Scope

Day 24 adds **one optional subdocument** (`ai_analysis.routing`) to the
existing `messages` collection and introduces two extra `ai_analysis.status`
values. No collection is changed, renamed, or migrated; the `messages`
document shape from `specs/014-whatsapp-webhook/data-model.md` (and Day 18's
original) is otherwise untouched. SIMULATE / web / legacy documents remain
valid.

## 2. Stored `ai_analysis` (MongoDB `messages`)

```json
{
  "priority": "normal | urgent | important | pending",
  "confidence": 0.5,
  "explanation": "string | null",
  "summary": "string | null",
  "recommended_action": "",
  "recommended_actions": [],
  "tasks_extracted": [],
  "deadlines": [],
  "needs_attention": false,
  "attention_reason": "",
  "provider": "groq | rule-based",
  "analyzed_at": "datetime UTC",
  "status": "completed | pending | skipped",

  "routing": {
    "agents_run": ["priority", "summary", "task_extraction",
                   "deadline_detection", "recommended_action"],
    "agents_skipped": [],
    "skip_reason": "",
    "triggers": ["send", "tonight"],
    "llm_call_used": true,
    "decided_at": "datetime UTC"
  }
}
```

### Field notes

- `agents_run` / agents_skipped use the fixed agent ids `priority`,
  `summary`, `task_extraction`, `deadline_detection`,
  `recommended_action`. `priority` is ALWAYS in `agents_run` when the message
  was analyzed (Priority never skipped). For skipped messages both lists are
  empty and `skip_reason` says why (e.g. `no analyzable content`).
- `agents_skipped` = five agent ids minus `agents_run` (computed by the
  Orchestrator from `RoutingDecision`), so run-vs-skipped is explicit.
- `triggers` records the matched rule signals (task keywords, time
  expressions, `trivial`, `non_latin_script`) so the decision is explainable.
- `llm_call_used`: `true` for analyzed messages; `false` for trivial. For a
  failed run, `status="pending"` AND `llm_call_used=true` — distinguishable
  from a deliberate skip (constitution explainability / spec FR-009).
- `provider`: `"rule-based"` for trivial/skipped deterministic results;
  `"groq"` for analyzed ones (existing value: `groq`).
- `status` values now: `"completed"` (analyzed or trivial), `"pending"`
  (provider failure, existing fallback), `"skipped"` (no analyzable content).

### Skipped (no analyzable content) stub

Stored so the Dashboard inbox and `get_filter_counts` keep working:

```json
{
  "priority": "normal",
  "confidence": 0.5,
  "summary": null,
  "tasks_extracted": [],
  "deadlines": [],
  "recommended_action": "",
  "provider": "rule-based",
  "status": "skipped",
  "routing": {
    "agents_run": [],
    "agents_skipped": [],
    "skip_reason": "no analyzable content",
    "triggers": [],
    "llm_call_used": false,
    "decided_at": "datetime UTC"
  }
}
```

## 3. Response Surface (API only, not stored)

`AIAnalysis` (`backend/models/message.py`) gains ONE declared, defaulted
field:

```python
class RoutingRecord(BaseModel):
    agents_run: list[str]
    agents_skipped: list[str]
    skip_reason: str = ""
    triggers: list[str] = []
    llm_call_used: bool = False
    decided_at: datetime

class AIAnalysis(BaseModel):
    # ...existing fields unchanged...
    routing: Optional[RoutingRecord] = None   # NEW
```

- **Why a declared field**: `message_doc_to_response` builds
  `AIAnalysis(**doc["ai_analysis"])`; Pydantic 2 (in use, v2.12.5) ignores
  undeclared keys by default, so without this field `routing` would not
  appear in `MessageResponse.ai_analysis`. Declared + optional + defaulted →
  additive, backward compatible, and the frontend ignores it.
- `routing` is emitted only for documents that carry it (analyzed/trivial/
  skipped all carry one; legacy `pending`-only documents serialize
  `routing: null`).

## 4. Tasks Collection (unchanged, but gated)

The `tasks` collection keeps its Day 18 shape. Day 24 only changes WHEN task
documents are created: an insert happens solely when the Orchestrator set
`run_task_extraction=True` (i.e. `task_extraction ∈ agents_run`). Task docs
from messages whose Task Extraction was skipped are never written (spec
FR-005 / SC-006).

## 5. Indexes

None. Routing rides inside `ai_analysis`; no query across `routing.*` is
performed, and `get_filter_counts` continues to index on the existing
`ai_analysis.priority`. No new indexes.

## 6. Hard Requirements

- Do NOT migrate existing documents; `routing` is optional, absent on all
  legacy rows until a re-analysis writes it (none are re-processed).
- `routing.agents_run` must always include `priority` when the message was
  analyzed — Priority never skipped (constitution Day 24).
- Any stored `status="skipped"` row MUST have a matching `routing.skip_reason`
  and `llm_call_used=false`; any `status="pending"` row MUST have
  `llm_call_used=true` — the two failure modes must stay distinguishable.