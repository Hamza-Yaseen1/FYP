# 06 — AI & "Agentic" System

> How the AI actually works in Sift — honestly. This is the document to read before any viva where an examiner asks "so is it really agentic?". Short answer: it is **deterministic routing + a single LLM call**, dressed with an explainable "routing record". It is a good, defensible design — but it is **not** a multi-agent autonomous system, and the docs must not claim it is.

---

## 1. The honest summary

| Claim | Reality |
|-------|---------|
| "Multi-agent AI" | ❌ No. There is **one** LLM call. The five "agents" (priority, summary, task extraction, deadline detection, recommended action) are **logical outputs of a single call**, selected by rule-based routing. |
| "Autonomous" | ❌ No. Every AI action is triggered by an incoming message or a user command. Nothing runs on its own beyond a retry sweep. |
| "AI decides what to do" | 🟡 Partly. A **deterministic rule engine** decides *which* outputs are needed; the LLM only fills them in. |
| "Explainable" | ✅ Yes. A `routing` record is stored on every message explaining what was requested, what ran, what was skipped, and whether an LLM call was made. |
| "Works when AI is down" | ✅ Yes. Failures become `pending`, are retried, and the rest of the app keeps working. |

**How to describe it accurately:** *"A rule-based orchestration layer routes each message to a single structured LLM call, with deterministic fallbacks, explainable routing metadata, and graceful degradation."*

---

## 2. The five "agents" (really: five output fields)

Defined in `backend/services/ai/routing.py` (`AGENT_IDS`):

| Agent id | What it produces |
|----------|------------------|
| `priority` | Urgent / Important / Normal / Low + confidence |
| `summary` | A 1–2 sentence summary (<30 words) |
| `task_extraction` | A list of actionable tasks |
| `deadline_detection` | Dates/times associated with tasks |
| `recommended_action` | A single imperative next step |

They are called "agents" because the original design imagined separate agents; in the implementation they are **sections of one prompt/response**.

---

## 3. The pipeline — `services/ai/orchestrate.py`

`process_message` is the **single entry point**. Everything else is forbidden from calling `analyze_message` directly.

```
process_message(message)
│
├─ 1. Is the message trivial or empty of content?
│      → YES: return deterministic defaults, llm_call_used=false, ZERO LLM calls
│      → (a "skipped" stub for no-content/media)
│
├─ 2. decide_routing(message)          [pure, rule-based]
│      → which of the 5 agents are needed?
│      → if none: same deterministic default path as step 1
│
├─ 3. analyze_message(message, routing, context)
│      → build ONE prompt with only the needed sections
│      → ONE Groq call, JSON response
│      → parse → AIAnalysis
│      → on any failure: _analyze_with_fallback → status="pending"
│
├─ 4. _gate_outputs
│      → clear any outputs whose agent was NOT requested
│
└─ 5. attach `routing` record
       → always, on every path, including failures
```

### Why route at all?
- **Cost/latency:** a short "thanks!" message needs no summary or task extraction.
- **Quality:** forcing irrelevant sections invites hallucination.
- **Explainability:** the routing record tells the user (and the examiner) why the AI did what it did.

### Routing rules (`routing.py`)
- Pure function — no I/O, fully testable.
- `TASK_TRIGGER_KEYWORDS` are **verb-first** ("send", "please", "review", "schedule"…) to reduce false positives.
- `TIME_EXPRESSION_KEYWORDS` reuse `NEAR_TERM_KEYWORDS` (tonight/today/tomorrow/asap/right now/immediately).
- **Fail toward completeness**: if unsure, run more agents rather than fewer (missing a task is worse than an extra summary).

---

## 4. The provider — `services/ai/providers/groq.py`

Only Groq is used. `providers/__init__.py` exports the OpenAI provider too, but the factory never selects it (`providers/openai.py` is dead code — see `15_FINDINGS_AND_GAPS.md`).

Key behaviours:

| Behaviour | Detail |
|-----------|--------|
| Model | `GROQ_MODEL`, default `qwen/qwen3.8-27b` |
| Fallback model | `GROQ_FALLBACK_MODEL`, default `openai/gpt-oss-20b` (one-shot rescue for 413) |
| Output budget | `GROQ_MAX_OUTPUT_TOKENS`, default 400 |
| Reasoning | disabled (`reasoning_effort="none"`) so the whole budget goes to the answer |
| Format | `response_format={"type": "json_object"}` |
| Retries | `GROQ_RETRY_ATTEMPTS=2`, backoff `GROQ_INITIAL_RETRY_DELAY=0.3` → `GROQ_MAX_RETRY_WAIT=1.0` |
| Circuit breaker | daily-quota 429 → cooldown `GROQ_COOLDOWN_SECONDS=600` |
| Concurrency | `GROQ_MAX_CONCURRENT=2` |
| Timeout | `GROQ_TIMEOUT=30` |
| Private `chat()` | Used **only** by the assistant (JARVIS), when a key is configured |

**Important operational note:** the default Qwen reasoning model can burn the entire output budget on hidden reasoning and trip a free-tier rate limit — which is exactly why `reasoning_effort="none"`, a JSON format, and a low token cap are set. A failed analysis surfaces in the UI as `pending`, not as a wrong answer.

---

## 5. Prompts — `services/ai/prompts/`

Plain text files, loaded at runtime:

| File | Enforces |
|------|----------|
| `priority.txt` | The 4 priority levels + the task-extraction schema |
| `tasks.txt` | Deadline discipline — **never invent a date** that isn't in the text |
| `summary.txt` | 1–2 sentences, under 30 words |
| `actions.txt` | A single imperative; must match the message's language (includes Arabic examples) |

The prompts are deliberately strict to keep output structured and to reduce hallucination.

---

## 6. The `AIAnalysis` result and the `routing` record

Stored on each message (`backend/models/message.py`):

```
ai_analysis: {
  status: "completed" | "pending" | "failed",
  provider: "groq" | "unknown",
  priority, confidence, explanation,
  summary,
  recommended_actions: [...],
  tasks_extracted: [...],
  deadlines: [...],
  needs_attention: bool,
  attention_reason: str,
  reviewed / verified: bool,
  routing: {
    agents_requested: [...],
    agents_run: [...],
    skipped: [...],
    llm_call_used: bool,
    reasons: [...]
  }
}
```

The `routing` subdocument is the project's strongest "agentic" evidence: it proves the system reasons about *what* to do, not just *how*.

---

## 7. "Needs your attention" — deterministic, not AI — `services/ai/attention.py`

This is deliberately **not** left to the LLM:

- **Rule 1 (R1):** the message contains a task **and** a near-term deadline → needs attention.
- **Rule 2 (R2):** the message is **urgent** and contains a task → needs attention.
- `NEAR_TERM_KEYWORDS` = tonight, today, tomorrow, asap, right now, immediately.

The reason is stored (`attention_reason`) and shown in the UI as "Why it matters". Determinism here means the user can predict and trust it.

---

## 8. Thread context — `services/ai/context.py`

Messages in the same deterministic thread can inform each other's analysis.

```
fetch_thread_context(message)   → up to 5 prior same-user messages (excludes current)
build_context_block(messages)   → renders a CONTEXT block for the prompt
   (includes a "(THIS message being analyzed)" marker for the current message)
validate_context_updates(...)   → accepts ONLY verbatim values from a provable source
   (an earlier thread message, or the current message)
apply_context_updates(...)      → $push-only, user-scoped
```

Two guardrails make this safe:
1. **Only verbatim values** are accepted — the model cannot paraphrase itself into a "fact".
2. **Enrichment never blocks ingestion** — if context fails, the message is still stored and analysed.

The design goal is stated in the code: *"0 tolerance for unlabelled influence."*

---

## 9. Token budgeting — `services/ai/token_budget.py`

- Estimates tokens at roughly **4 characters per token** (no tokeniser dependency).
- `budget_message` keeps the head of a long message (preserving the `Subject:` line) and marks truncation with `TRUNCATION_MARKER`.
- `budget_context_messages` limits how much thread history is injected.
- All limits are env-tunable; short messages pass through **byte-identically** (so behaviour doesn't change for the common case).

---

## 10. Failure handling & recovery

```
AI call fails
  → ai_analysis.status = "pending"        (visible in UI, not silent)
  → services/retry_pending.py sweep (every 60s)
        → re-enters process_message (NEVER analyze_message)
        → user-scoped $set, idempotent, sequential
        → stops after RETRY_MAX_CONSECUTIVE_FAILURES
```

- Terminal failures (e.g. `TOO_LARGE_EXPLANATION`) are **not** retried — they'd fail forever.
- The Groq circuit breaker prevents hammering the API during a daily-quota lockout.

---

## 11. The assistant's own AI (Kestrel / JARVIS)

The assistant is a **separate system** from message analysis. It has five phases, applied in order, deterministic-first.

```
POST /jarvis/chat
  │
  ├─ Phase 4  detect_message_intent   (message-content questions)  — jarvis_messages.py
  ├─ Phase 2  actions                 (create/complete/delete task, search, …) — jarvis_actions.py
  ├─ Phase 3  detect_intent           (navigation + real-data info) — jarvis_intents.py
  ├─ Phase 1  route_command           (greeting / help / nav / info / unknown)
  └─ Phase 5  _handle_chat            (Groq conversation, or deterministic fallback)
```

Key properties:
- **Ownership rules** keep earlier phases byte-identical: e.g. Phase 4 declines greetings, "unread", task words, attention, dashboard, draft/reply, "messages from \<sender\>" (so Phase 2 keeps those).
- **The LLM is used sparingly:**
  - Phase 3 `llm_info_intent` labels an *unknown* command, but only to a **whitelist** of info-intent keys — never parameters, DB, or navigation.
  - Phase 4 summarize uses Groq on a **digest of the user's own messages** only.
  - Phase 5 `_handle_chat` answers general questions via `GroqProvider.chat()` **only if a key is configured**; otherwise a fixed `CONVERSATION_UNAVAILABLE_REPLY`.
- **Context memory** (`_CONTEXTS`): last 8 turns per user, in memory, text-only — no DB data, no user ids, no other users, ever injected into prompts.
- **Follow-ups:** `resolve_message_follow_up` maps "what about those?" / "summarize them" to whitelisted message intents — it can never emit an action or navigation, so context cannot bypass the deterministic system.
- **Actions are gated by confirmation:** destructive actions return a signed 2-minute confirmation token; the frontend must replay with `confirmed=true`.

---

## 12. What is genuinely impressive here (viva material)

1. **The single-entry discipline** — one function for message AI, one for the assistant; routes can't cheat.
2. **Explainability** — the `routing` record is real evidence of reasoning.
3. **Deterministic safety rails** — attention, thread-linking, navigation, and ownership rules are all rule-based and tested.
4. **Graceful degradation** — pending + retry + circuit breaker means the product survives an AI outage.
5. **Context safety** — verbatim-only updates and whitelist-only LLM outputs prevent prompt-injection-style contamination.

## 13. What to concede gracefully

- It is **not** multi-agent; it is single-call with routing.
- Context memory is in-process (lost on restart).
- Model quality and language coverage are limited by the chosen Groq model.
- The "agents" naming is aspirational.

(More discrepancies and gaps: `15_FINDINGS_AND_GAPS.md`.)
