# Implementation Plan: Complete AI Pipeline

**Branch**: `006-complete-ai-pipeline` | **Date**: 2026-08-21 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/006-complete-ai-pipeline/spec.md`

## Summary

Connect the five working AI capabilities (Priority, Summary, Task
Extraction, Deadline Detection, Recommended Action) into one smooth
end-to-end flow and surface the result as a clear 🔴 NEEDS ATTENTION card
on the Dashboard. The pipeline entry point already exists (webhook /
POST /messages → `analyze_message()` → MongoDB update); Day 14 adds: (1) a
pure-function attention evaluation (no extra LLM call) that computes
`needs_attention` + `attention_reason` per constitution rules R1/R2,
(2) webhook duplicate protection for idempotent reprocessing, and (3) a
`NeedsAttentionCard` frontend component rendered on the Dashboard and the
Attention page from stored data only.

## Technical Context

**Language/Version**: Python 3.11+ (FastAPI backend), TypeScript 5.x with Next.js App Router (frontend)
**Primary Dependencies**: FastAPI, Motor (async MongoDB), Pydantic, Groq SDK; Next.js, Tailwind CSS, shadcn/ui
**Storage**: MongoDB (`messages`, `tasks` collections via `database.py`)
**Testing**: pytest (backend — existing tests in `backend/test_*.py`), manual browser verification (frontend)
**Target Platform**: localhost dev (backend :8000, frontend :3000)
**Project Type**: Web application (monorepo: `app/` + `components/` + `lib/` frontend, `backend/` API)
**Performance Goals**: Full pipeline ≤ 10s per message including LLM call; non-LLM endpoints < 500ms
**Constraints**: No new dependencies; no new LLM round-trips; UI never blocks on analysis
**Scale/Scope**: Single-user FYP demo; ≤ 100 messages in list views

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Evidence |
|------|--------|----------|
| I. Simplicity First | ✅ PASS | Attention flag is a ~20-line pure function over already-stored analysis; zero new dependencies; no date-parsing library |
| II. Vertical Slices | ✅ PASS | Slice delivers message → flagged card visible on dashboard end-to-end |
| III. AI is Assistive | ✅ PASS | Every flag carries a truthful "Why it matters" reason derived from stored signals |
| IV. User Control | ✅ PASS | Flag is advisory; no auto-actions; existing delete/dismiss behavior unchanged |
| V. Security & Privacy | ✅ PASS | No new secrets, endpoints, or data exposure; response fields are user's own data |
| VI. Clean Code | ✅ PASS | Python module + TSX component follow existing conventions (PEP 8, ESLint) |
| VII. Progressive Enhancement | ✅ PASS | Per-stage fallbacks preserved; card renders with missing optional fields omitted |

No violations — Complexity Tracking not needed.

## Project Structure

### Documentation (this feature)

```text
specs/006-complete-ai-pipeline/
├── spec.md              # Feature specification (/sp.specify)
├── plan.md              # This file (/sp.plan)
├── research.md          # Phase 0 output — decisions & rationale
├── data-model.md        # Phase 1 output — entities & fields
├── contracts/
│   └── messages-api.md  # Phase 1 output — API shape changes
├── quickstart.md        # Phase 1 output — run & verify guide
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code (repository root)

```text
backend/
├── models/
│   └── message.py                  # UPDATE: AIAnalysis += needs_attention, attention_reason
├── services/
│   └── ai/
│       ├── analyzer.py             # UPDATE: run evaluate_attention() after analysis
│       └── attention.py            # NEW: pure attention-evaluation logic (R1/R2)
├── routes/
│   └── webhooks.py                 # UPDATE: duplicate-message guard before insert
└── test_attention_pipeline.py      # NEW: unit + integration tests

app/(dashboard)/
├── dashboard/page.tsx              # UPDATE: Needs Attention section above message list
└── attention/page.tsx              # UPDATE: replace placeholder with real flagged cards

components/
└── NeedsAttentionCard.tsx          # NEW: exact card layout from spec
components/MessageList.tsx         # UPDATE: extend Message interface type
```

**Structure Decision**: Existing monorepo layout retained. Backend changes
concentrate in `services/ai/` (evaluation logic isolated in its own module
for unit-testability); frontend changes concentrate in one new component
reused by two pages.

## Implementation Phases

1. **Backend flag**: `attention.py` (R1/R2 evaluation) + `AIAnalysis`
   fields + wire into `analyzer.py`
2. **Idempotency**: webhook duplicate guard (same sender+content+source
   within 10 min → update existing doc instead of insert)
3. **Frontend card**: `NeedsAttentionCard.tsx`; render flagged messages on
   Dashboard page and Attention page (client-side filter of stored data)
4. **Tests + verification**: pytest suite; manual end-to-end per quickstart.md

## Complexity Tracking

> Not needed — no constitution violations to justify.
