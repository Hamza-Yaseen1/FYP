# Data Model: Complete AI Pipeline

**Feature**: 006-complete-ai-pipeline | **Date**: 2026-08-21

## Entity: Message (MongoDB `messages` collection) — EXTENDED

Existing document; `ai_analysis` sub-document gains two fields.

### ai_analysis (sub-document)

| Field | Type | Default | Rules |
|-------|------|---------|-------|
| priority | str | `"pending"` | urgent / important / normal / pending |
| confidence | float | 0.0 | 0.0–1.0 |
| explanation | str \| null | null | From priority agent |
| summary | str \| null | null | Short digest; null on failure |
| recommended_action | str | `""` | Verb-first, ≤15 words; `""` on failure |
| recommended_actions | list[str] | `[]` | Legacy list wrapper |
| tasks_extracted | list[ExtractedTask] | `[]` | See below |
| deadlines | list[str] | `[]` | Original wording preserved |
| **needs_attention** | **bool** | **`false`** | **NEW — set only by R1/R2** |
| **attention_reason** | **str** | **`""`** | **NEW — plain-language trigger; non-empty iff flag true** |
| provider | str | `"unknown"` | LLM provider id |
| analyzed_at | datetime \| null | null | UTC |
| status | str | `"pending"` | completed / pending |

### ExtractedTask (embedded)

| Field | Type | Rules |
|-------|------|-------|
| description | str | User's own words from message |
| deadline | str \| null | Original expression ("Tonight") or null |
| priority_indicator | str \| null | Word present in message or null |
| requires_action | bool | Always true for extracted tasks |

## Entity: Task (MongoDB `tasks` collection) — UNCHANGED

Created by analyzer when tasks are extracted. Fields: description,
deadline, priority_indicator, requires_action, status (`pending`),
source_message_id, source_message_preview, created_at.

## Derived View: Needs Attention Card (frontend only, not stored)

Rendered strictly from a Message's stored fields:

```text
🔴 NEEDS ATTENTION            ← if ai_analysis.needs_attention
{first task description}      ← tasks_extracted[0].description
{source} • {sender}           ← e.g. "whatsapp • Ali"
Deadline: {deadline}          ← first near-term deadline (original wording)
Why it matters: {reason}      ← ai_analysis.attention_reason
Recommended: {action}         ← ai_analysis.recommended_action
```

Omission rules: unflagged → no badge/reason lines; missing deadline →
no Deadline line; empty recommendation → no Recommended line.

## Attention Evaluation State Machine

```
                 ┌─────────────────────────────┐
analysis done ──▶│ evaluate_attention(analysis) │
                 └──────────┬──────────────────┘
              R1: task ∧ near-deadline     R2: urgent ∧ task
                    └────────┬────────┘
                  any true ▶ needs_attention=true,
                            attention_reason=<trigger text>
                  none true▶ needs_attention=false, reason=""
```

Reason strings (exact, plain language):
- R1: `"A task with a near deadline was detected."`
- R2: `"An urgent message with an actionable task was detected."`
- R1+R2 both: R1 text takes precedence (near deadline is the stronger signal).

## Validation Rules

- `attention_reason` MUST be non-empty whenever `needs_attention` is true
  and empty otherwise (enforced in `evaluate_attention`, asserted in tests).
- Flag evaluation MUST NOT call the LLM provider (pure function).
- Near-term keyword set: `tonight, today, tomorrow, asap, right now,
  immediately` (case-insensitive substring match on deadline strings).

## State Transitions (message.status / ai_analysis.status)

Unchanged by this feature: `pending → completed` on successful analysis;
stays `pending` with fallback values on failure (flag then evaluates false).
