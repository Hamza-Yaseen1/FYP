# Contract: AI Context Block + Validated `context_updates`

**Feature**: 016-agent-memory | **Date**: 2026-08-29 | **Phase**: 1 (Design)

Defines (a) how bounded same-thread context enters the single LLM call, (b)
the optional `context_updates` the model may emit, and (c) the validation +
application rules that make enrichment provable and explainable.

## 1. Context Injections (one call, never a new one)

**When**: only on the Orchestrator's analyze branch (`needs_analysis` AND
`needs_llm`) and only when the current message has a `threadId`.

**What**: up to the 5 most recent same-user messages in the thread, excluding
the message being analyzed, sorted by `received_at` desc. Each is given a
short **handle** = last 7 chars of its `_id`, plus `sender`, `content`,
`received_at`.

**How**: rendered into the existing `ANALYSIS_PROMPT` as
`CONTEXT — PREVIOUS MESSAGES IN THIS CONVERSATION`, only when non-empty
(`GroqProvider` uses `.replace` — brace-safe). The block MUST be absent when
no context exists, i.e. the prompt is byte-identical to Day 24 for standalone
messages → zero regression.

```text
CONTEXT — PREVIOUS MESSAGES IN THIS CONVERSATION (from the same sender, same channel):
[abc1234] ali (2026-08-29T12:00:00Z): Can you send the report?

[def5678] (THIS message being analyzed — usable as a context_updates source handle)

RULES:
- Use context ONLY to supply a missing deadline/urgency to the CURRENT message
  or to report how an EARLIER message's analysis should change.
- NEVER override a fact explicitly stated IN THE CURRENT MESSAGE
  (a stated deadline always wins).
- The optional "context_updates" key targets EARLIER messages in this same
  conversation using their handles from the CONTEXT block above.
- "source_message_id" MUST be the handle of an EARLIER context message OR the
  current message's own handle (labeled above) — and the "value" must appear
  verbatim in that source message's content.
- NEVER invent values that do not appear in the linked messages.
```

**Cost**: still exactly ONE provider call per analyzed message. The provider
invocation is counted in tests to prove it (SC-006).

## 2. `context_updates` Output (optional)

The model MAY add one key to its single JSON response:

```json
"context_updates": [
  {
    "target_message_id": "abc1234",   // handle of an EARLIER thread message
    "field": "deadline",              // "deadline" | "priority" | "note"
    "value": "before the meeting",    // MUST appear verbatim in the source message
    "source_message_id": "def5678",   // handle of an earlier context message OR
                                      // the current message's handle (labeled
                                      // in the CONTEXT block)
    "reason": "plain-language why"    // required, names the linked message
  }
]
```

`AIAnalysisResult.context_updates` carries the raw list through the provider;
`analyze_message` forwards it in the returned dict under `context_updates`.

## 3. Validation (0 tolerance for unlabelled/fabricated influence)

`services/ai/context.py::validate_context_updates` drops any entry where ANY
of these hold:

| Check | Reject when |
|---|---|
| Target membership | `target_message_id` handle does not map to a message in THIS thread fetch |
| Self-target | target handle == the message currently being analyzed |
| Disallowed field | `field` ∉ {`deadline`, `priority`, `note`} |
| Source membership | `source_message_id` handle does not map to a thread message NOR to the current message's handle |
| Literal provenance | `value` is not a verbatim substring of the source message's (or current message's) `content` |

Rejected entries are logged and dropped — they never reach storage. This is
the enforcement of "every inferred enrichment MUST be recorded with an
explanation naming the linked message(s)" and "nothing is written that the
linked messages do not actually support".

## 4. Application (explainable revision, outward only)

For each VALID entry, `apply_context_updates` executes:

```js
messages.update_one(
  { "_id": target_id, "user_id": <current user> },
  { "$push": { "ai_analysis.context_updates": {
      "field": field, "value": value,
      "source_message_id": source_id,   // real _id (not the handle)
      "reason": reason, "applied_at": now
  } } }
)
```

Guarantees:

- Target is guaranteed in-thread and in-user by validation ⇒ the write cannot
  reach another user's or another thread's documents.
- The target's original `ai_analysis` fields are NEVER modified — the update
  is a new, additive, explainable revision ("NEVER silently rewrite prior
  analysis").
- `context_updates` is popped from the CURRENT message's stored analysis
  (sibling write, not self-stored).
- Validation/application errors are caught; they never raise into `process_message`
  and never block analysis completion (FR-012).

## 5. Prompt/Model Invariants

- Explicit user-stated facts in the current message always beat inferred
  context (Day 11 mirror; also enforced because original fields stay intact).
- Context never appears on trivial/skip paths (Day 24 preserved, zero calls).
- `routing`, priority, NEEDS ATTENTION, and Dashboard behavior are unchanged
  for messages without context (Day 24 contract intact).