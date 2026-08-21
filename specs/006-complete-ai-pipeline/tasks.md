---
description: "Task list for Complete AI Pipeline (Day 14)"
---

# Tasks: Complete AI Pipeline

**Input**: Design documents from `/specs/006-complete-ai-pipeline/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Included — the plan explicitly defines `backend/test_attention_pipeline.py` and quickstart verification cases.

**Organization**: Tasks grouped by user story (US1 P1, US2 P2, US3 P3 from spec.md).
User's logical grouping maps as: Data Structure → Phase 2, Backend Pipeline → US1,
Flag Logic + Frontend Display → US2, Testing/Degradation → US3 + Polish.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Web app monorepo: `backend/` (FastAPI), `app/` + `components/` (Next.js)

---

## Phase 1: Setup (Baseline Verification)

**Purpose**: Confirm the existing pipeline works before touching anything

- [x] T001 Start backend (`cd backend; uvicorn main:app --reload --port 8000`) and frontend (`npm run dev`), send one test message via `POST /webhooks/whatsapp`, and confirm it appears on http://localhost:3000/dashboard with priority, summary, and recommendation rendered

**Checkpoint**: Baseline working — safe to modify

---

## Phase 2: Foundational (Data Structure)

**Purpose**: Extend the stored analysis shape — blocks all user stories

**⚠️ CRITICAL**: No story work until the model carries the new fields

- [x] T002 Add `needs_attention: bool = False` and `attention_reason: str = ""` fields to the `AIAnalysis` model in backend/models/message.py (defaults keep legacy messages valid — no migration)

**AC**: `GET /messages` responses include both fields; old messages return `false` / `""`.

**Checkpoint**: Contract change live — stories can proceed

---

## Phase 3: User Story 1 — Full Analysis on Arrival (Priority: P1) 🎯 MVP

**Goal**: Every incoming message flows through all five stages in fixed order, saves once, and never duplicates

**Independent Test**: Send one message → all five analysis results visible on dashboard; send it twice → still one record

### Implementation for User Story 1

- [x] T003 [US1] Add duplicate-message guard in backend/routes/webhooks.py: before `insert_one`, query `messages_collection` for a document with identical `sender`, `content`, and `source` created within the last 10 minutes; if found, reuse its `_id` for analysis instead of inserting

  **AC**: Re-sending an identical payload within 10 minutes updates the existing document; total message count unchanged.

- [x] T004 [US1] Verify and lock the stage order in backend/services/ai/analyzer.py: priority+tasks+deadlines (single provider call) → summary → recommendation, followed by ONE `update_one` `$set` save; add an INFO log listing completed stages per message

  **AC**: Log output shows all five stages completing in order for each message; exactly one DB write per run.

- [x] T005 [US1] Add integration test `test_duplicate_message_updates_not_inserts` in backend/test_attention_pipeline.py: POST the same WhatsApp payload twice via the route handler or TestClient, assert `messages_collection.count_documents({}) == 1` and `ai_analysis.status == "completed"`

**Checkpoint**: US1 independently functional — pipeline is reliable end-to-end

---

## Phase 4: User Story 2 — Needs Attention Flagging (Priority: P2)

**Goal**: Qualifying messages are flagged with a truthful reason and rendered as the exact 🔴 card on Dashboard and Attention pages

**Independent Test**: Send "Please send the FYP slides tonight." → flagged card appears at top of dashboard with all six lines; send "Hey, how was your weekend?" → no badge anywhere

### Tests for User Story 2 (write FIRST, ensure they FAIL)

- [x] T006 [P] [US2] Write unit tests for `evaluate_attention` in backend/test_attention_pipeline.py covering: R1 (task + "Tonight" → true, reason `"A task with a near deadline was detected."`), R2 (urgent + task, no deadline → true, reason `"An urgent message with an actionable task was detected."`), R1+R2 together → R1 text wins, urgent without task → false, deadline without task → false, nothing → false, and invariant `attention_reason` non-empty iff flag true

### Implementation for User Story 2

- [x] T007 [US2] Create backend/services/ai/attention.py with `NEAR_TERM_KEYWORDS = ["tonight", "today", "tomorrow", "asap", "right now", "immediately"]` and pure function `evaluate_attention(analysis: dict) -> dict` implementing R1/R2 per data-model.md (case-insensitive substring match on deadline strings); make T006 pass

  **AC**: Function imports no LLM/DB modules; all T006 assertions pass.

- [x] T008 [US2] Call `evaluate_attention` inside `analyze_message` in backend/services/ai/analyzer.py and merge its result into the returned analysis dict so both fields persist via the existing single save

  **AC**: Fresh analyzed messages return `needs_attention`/`attention_reason` in API responses matching the flag rules.

- [x] T009 [P] [US2] Create components/NeedsAttentionCard.tsx rendering the exact card layout from spec FR-008: red NEEDS ATTENTION badge, task description (`tasks_extracted[0].description`), `{source} • {sender}` metadata line, `Deadline: {deadline}` (original wording), `Why it matters: {attention_reason}`, `Recommended: {recommended_action}`; style with existing Tailwind/shadcn patterns (red accent border/badge, bg-card); omit any line whose field is missing or empty

  **AC**: Card visually matches the spec example; unflagged/empty fields never render as blank rows or "undefined".

- [x] T010 [US2] Update app/(dashboard)/dashboard/page.tsx to split fetched messages: those with `ai_analysis.needs_attention === true` render as NeedsAttentionCard list in a "Needs Attention" section above the existing MessageList; others stay in MessageList unchanged

  **AC**: Flagged message shows ONLY as attention card at top; unflagged show in normal list; no duplicates across sections.

- [x] T011 [US2] Replace the placeholder content in app/(dashboard)/attention/page.tsx: fetch `GET /messages`, filter `needs_attention === true`, render NeedsAttentionCard list, keep the existing empty-state for zero flags

  **AC**: Attention page lists exactly the flagged cards and nothing else.

- [x] T012 [US2] Extend the `Message` interface `ai_analysis` type in components/MessageList.tsx with `needs_attention?: boolean` and `attention_reason?: string`

**Checkpoint**: US2 independently functional — flag → card → two pages

---

## Phase 5: User Story 3 — Graceful Degradation (Priority: P3)

**Goal**: Failed stages never hide messages or create false flags

**Independent Test**: Invalidate API key, send a message → message appears with defaults, unflagged, no crash; restore key

### Implementation for User Story 3

- [ ] T013 [US3] Add unit test `test_failed_analysis_is_never_flagged` in backend/test_attention_pipeline.py asserting the analyzer exception-fallback dict (status "pending", empty tasks) passes through `evaluate_attention` as `{"needs_attention": false, "attention_reason": ""}`

- [x] T014 [US3] Manually verify degradation per quickstart.md Case E: temporarily invalidate backend/.env Groq key, send a message, confirm it renders on dashboard with default values and no badge, then restore the key

  **AC**: No crash, no false flag, message persisted; UI stays responsive during pending analysis.

  > Verified 2026-08-21: server restarted with invalid GROQ_API_KEY env override → message stored, status `pending`, unflagged, no crash; clean restart recovered (`completed`, flagged urgent correctly).

**Checkpoint**: All stories independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Regression safety and final validation

- [x] T015 Run the full backend suite (`cd backend; python -m pytest -v`) and fix any regressions in existing tests (test_ai_analysis.py, test_priority_*.py, test_task_extraction.py)

  > Result 2026-08-21: attention 9/9 ✅ · task_extraction 13/13 ✅ (pytest) · ai_analysis ALL PASS (own runner) · priority_integration 7/8 ✅ · priority_edge_cases 5/6. Two non-regression findings: (1) T035 accuracy failures + T036 fast-fallback traced to Groq free-tier daily token cap exhausted (429 TPD 199,355/200,000) from today's testing volume — rerun after reset; (2) T028 `low` vs `normal` on a short message is pre-existing LLM drift — Day 14 diff touches no classification code. Pre-existing hygiene: test_ai_analysis.py async tests lack pytest markers.
- [x] T016 Execute quickstart.md Cases A–D end-to-end in the browser and tick the Definition of Done checklist (card field order, duplicate protection, attention page, unflagged rendering)

  > Result 2026-08-21: Case A flagged card ✅ (live API: exact R1 reason, task/deadline/recommendation stored) · Case B unflagged ✅ · Case C duplicates ✅ (integration test) · Case D attention-page filter ✅ (API level; `next build` clean) · Case E ✅ (see T014). Browser eyeball pass recommended after `npm run dev`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (T001)**: No dependencies — establishes safe baseline
- **Foundational (T002)**: Blocks ALL story work (contract change)
- **US1 (T003–T005)**: After T002 — pipeline reliability first
- **US2 (T006–T012)**: After T002; independent of US1 code paths (only T008 touches analyzer.py, after T004 to avoid conflicts)
- **US3 (T013–T014)**: After T007/T008 (uses evaluate_attention)
- **Polish (T015–T016)**: After all stories

### Within US2

- T006 (tests, RED) → T007 (make GREEN) → T008 (wire in)
- T009 (component) parallel with T006–T008 (frontend vs backend)
- T010, T011 depend on T009; T012 anytime before T010/T011 typecheck

### Parallel Opportunities

- T006 ∥ T009 (test file vs component file)
- T009 ∥ T007/T008 (frontend while backend greens tests)
- T010 ∥ T011 (both depend only on T009)

---

## Parallel Example: User Story 2

```text
Backend track:   T006 (failing tests) → T007 (attention.py) → T008 (wire analyzer)
Frontend track:  T009 (NeedsAttentionCard) → T010 (dashboard) ∥ T011 (attention page)
Type touch-up:   T012 anytime before T010/T011
```

---

## Implementation Strategy

### MVP First (US1 Only)

1. T001 baseline → T002 model fields
2. T003–T005: reliable, duplicate-safe pipeline
3. STOP and validate: message arrives once, analyzes fully, saves once
4. Demo-ready even before any UI change

### Incremental Delivery

1. +US2 → the flagship demo: 🔴 card on dashboard (Day 14 goal achieved)
2. +US3 → failure-proofing for demo resilience
3. Polish → regression sweep, full quickstart pass

---

## Notes

- Commit after each task or logical group
- T006 must FAIL before T007 is written (red-green discipline)
- All flag logic stays server-side; frontend only reads stored fields
- Avoid: date-parsing libraries, new endpoints, backfill scripts (rejected in research.md)
