# Research: Complete AI Pipeline

**Feature**: 006-complete-ai-pipeline | **Date**: 2026-08-21

## R1: How to compute `needs_attention` without extra LLM cost?

**Decision**: Pure Python function over the already-completed analysis
result. Rules mirror constitution v1.3.0:
- R1: `tasks_extracted` non-empty AND any deadline matches near-term
  keywords (`tonight`, `today`, `tomorrow`, `asap`, `right now`,
  `immediately`)
- R2: `priority == "urgent"` AND `tasks_extracted` non-empty

**Rationale**: All signals needed for the flag are already produced by the
existing single analysis pass. A keyword check on deadline wording is
sufficient because the Task Extraction/Deadline guidance already mandates
preserving original expressions ("Tonight" stays "Tonight"). Full date
parsing would add complexity and failure modes for zero FYP benefit.

**Alternatives considered**:
- Second LLM call to judge attention → rejected: violates single-call
  principle, adds latency/cost/failure surface.
- Date parsing library (dateparser etc.) → rejected: new dependency,
  over-engineered for keyword-shaped deadlines.

## R2: Where should evaluation live?

**Decision**: New module `backend/services/ai/attention.py` exposing
`evaluate_attention(analysis: dict) -> dict`. Called once inside
`analyzer.analyze_message()` before returning; results stored inside
`ai_analysis`.

**Rationale**: Isolated pure function = trivially unit-testable with no
DB/LLM mocks. Keeping it out of `analyzer.py` preserves the analyzer's
single responsibility (orchestrating LLM calls).

**Alternatives considered**: Inline in analyzer.py → rejected: mixes
orchestration with business rules, harder to test. Compute in frontend →
rejected: violates "persist once, read many" — flag must be a stored fact.

## R3: How to guarantee idempotent reprocessing (FR-011)?

**Decision**: Two-part answer.
1. Same-document re-analysis is already safe: pipeline writes via
   `update_one({"_id": ...}, {"$set": {"ai_analysis": ...}})` — an update,
   never an insert.
2. Duplicate deliveries (webhook retry / simulated double-send): before
   insert, query for an existing doc with identical `sender` + `content` +
   `source` created within the last 10 minutes; if found, re-run analysis
   on THAT document instead of inserting a new one.

**Rationale**: Covers both duplicate paths with one small guard. The
10-minute window prevents false merging of genuinely repeated messages
("send it again please") while absorbing webhook retries.

**Alternatives considered**: Unique index on content hash → rejected:
blocks legitimate repeated messages forever. No dedup → rejected: spec
FR-011 and SC-004 require zero duplicates.

## R4: How does the Attention page get flagged items?

**Decision**: Reuse existing `GET /messages` and filter client-side on
`ai_analysis.needs_attention === true`.

**Rationale**: List endpoints already cap at 100 docs — well within FYP
scale; filtering 100 objects in the browser is instant. Zero backend
changes for this page = Simplicity First. Dashboard still reads stored
data only (constitution: persist once, read many).

**Alternatives considered**: New `GET /messages?needs_attention=true`
endpoint or MongoDB index → deferred: justified only if message volume
grows beyond list caps.

## R5: Card placement on Dashboard?

**Decision**: Flagged messages render as full `NeedsAttentionCard`s in a
"Needs Attention" section at the top of the Dashboard page; remaining
messages render in the existing `MessageList` below. The Attention page
shows the same card component for flagged items only.

**Rationale**: Matches spec FR-008 fixed field order and the user's exact
example card. One component reused by two pages avoids divergence.

**Alternatives considered**: Badge-only inside MessageList rows →
rejected: user explicitly requested the prominent card format; badge
already exists for tasks/priority.

## R6: What about legacy messages without the new fields?

**Decision**: Treat missing fields as defaults (`needs_attention: false`,
`attention_reason: ""`). Pydantic model defaults handle this on read;
no migration script.

**Rationale**: Existing analyzed messages simply appear unflagged until
re-analyzed. Backfilling is unnecessary for FYP demo data.

**Alternatives considered**: One-time backfill script → rejected: no
requirement demands historical flags; adds throwaway code.
