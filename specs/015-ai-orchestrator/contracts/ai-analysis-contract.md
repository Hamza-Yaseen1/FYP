# Analysis Contract: Combined Result + Routing Record

**Feature**: 015-ai-orchestrator | **Date**: 2026-08-29 | **Phase**: 1 (Design)

Day 24 introduces **no new HTTP endpoints**. It changes the *shape* of the
stored/returned `ai_analysis` (adds `routing`, two extra `status` values) and
the *routing* of the analysis pipeline behind the two existing triggers. This
document pins those contracts so the frontend and tests can rely on them.

## 1. Endpoints Involved (all UNCHANGED in path/auth)

| Endpoint | Trigger | Analysis scheduling |
|---|---|---|
| `POST /messages` (JWT) | Manual/simulated message create | Orchestrator runs synchronously; response contains `ai_analysis` incl. `routing` |
| `POST /webhooks/simulate` (JWT) | Piggy-backs on `ingest_message` | Background task → `ai_analysis` eventual (poll `/messages`) |
| `POST /webhooks/whatsapp` (HMAC) | Real Meta delivery | Background task → `ai_analysis` eventual |
| `GET /messages`, `GET /messages/feed` | Dashboard read | Response `MessageResponse.ai_analysis: AIAnalysis?` includes `routing` when present |

Auth, status codes, payloads, and response envelopes are exactly as authored in
`specs/014-whatsapp-webhook/contracts/webhook-api.md` and Day 18 — unchanged by
Day 24.

## 2. `ai_analysis` Contract (what "combined result" means)

Every processed message gets EXACTLY ONE stored `ai_analysis` produced by the
Orchestrator. `AIAnalysis` fields stay as today; only two things change:

1. `status` now ∈ `{"completed", "pending", "skipped"}`:
   - `completed` — analyzed (LLM) OR trivial (rule-based), usable result.
   - `pending` — LLM/provider failure; existing fallback fields; UI already
     renders this.
   - `skipped` — no analyzable content (blank / media-only); stub priority
     `normal` so inbox counts stay correct.
2. New optional `routing: RoutingRecord`:

```json
"routing": {
  "agents_run": ["priority", "summary"],
  "agents_skipped": ["task_extraction", "deadline_detection", "recommended_action"],
  "skip_reason": "",
  "triggers": [],
  "llm_call_used": true,
  "decided_at": "2026-08-29T12:00:00Z"
}
```

Invariants:
- `priority ∈ agents_run` and `agents_run ∪ agents_skipped = {the five ids}`
  when the message was analyzed (both lists empty for skipped).
- `llm_call_used` distinguishes real failures (`pending` + `true`) from
  deliberate skips (`skipped`/trivial + `false`).
- Non-selected agents persist documented fallbacks: `tasks_extracted: []`
  (and NO task documents in `tasks`), `deadlines: []`,
  `recommended_action: ""`. The LLM is never asked to invent them.
- `needs_attention` / `attention_reason` reflect the **gated** analysis
  (computed after skipped outputs are cleared).

## 3. Modeling Rules (behavioral contract)

| Condition | `needs_analysis` | `needs_llm` | Output kept | Tasks persisted | `status` |
|---|---|---|---|---|---|
| no content / media-only | false | false | stub | none | `skipped` |
| trivial phrase / very short no-trigger | true | false | deterministic defaults | none | `completed` |
| action, no time expr | true | true | priority, summary, tasks, recommended_action | yes | `completed` |
| time expr, no action | true | true | priority, summary, deadlines | none | `completed` |
| action + time expr | true | true | all five | yes | `completed` |
| long FYI, no triggers | true | true | priority, summary | none | `completed` |
| non-Latin / ambiguous | true | true | all five (full default) | yes | `completed` |
| provider failure | true | true (attempted) | fallback | none | `pending` |

## 4. Routing specifics

- `decide_routing(content, message_type) -> RoutingDecision` is a **pure**
  function (stdlib only); contract: same input → same decision, no state.
- Signals evaluated: absent content → trivial (exact phrase match, or
  ≤ 20 chars with no triggers) → task keywords → time keywords → non-Latin
  script (`unicodedata`). Any task/time trigger forces `needs_llm=True`.
  Ambiguity and non-Latin default to the FULL set.
- The full set = `priority, summary, task_extraction, deadline_detection,
  recommended_action` — the five pre-existing agents, executed in the
  existing fixed order via the existing single LLM call.

## 5. Guarantees

- **Call budget**: `llm_call_used=false` ⇒ zero provider calls; `true` ⇒
  exactly one Provider analyze call. Never two (test-enforced by invocation
  counting).
- **One orchestration layer**: `orchestrate.process_message` is the only
  caller of the analysis pipeline (grep-verifiable; `analyze_message` stays
  exported for tests but is invoked only from the Orchestrator in production
  code paths).
- **Backward compatibility**: existing response shapes, auth, and status codes
  unchanged; frontend renders stored data only, so it needs no changes.

## 6. Environment Variables

None added by Day 24. Reuses `GROQ_API_KEY`, `GROQ_MODEL` (analysis), and the
existing infra as-is.