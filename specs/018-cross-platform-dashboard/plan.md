# Implementation Plan: Cross-Platform Dashboard

**Branch**: `018-cross-platform-dashboard` | **Date**: 2026-09-11 | **Spec**: [spec.md](../spec.md)
**Input**: Feature specification from `/specs/018-cross-platform-dashboard/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

The user's home screen (`/dashboard`) becomes a unified **Cross-Platform
Dashboard**: every message from WhatsApp, Gmail, and any future channel
appears in one priority-first view, grouped top-to-bottom as **URGENT →
IMPORTANT → NORMAL → LOW**, with each card showing its priority, a main
title (extracted task → summary → content preview), source + sender, and
time — plus optional deadline, subject (Gmail), recommended action, and
"Needs Your Attention" badges.

Technical approach: a **frontend-only vertical slice**. The existing,
already user-scoped `GET /messages` endpoint returns everything needed
(including `ai_analysis`). Grouping and ordering happen client-side, the
same pattern `MessageList` and `NeedsAttentionSection` already use today.
No new backend endpoint, no schema change, no AI changes.

## Technical Context

**Language/Version**: TypeScript 5.x (React/Next.js App Router, `"use client"`); Python 3.13 backend (unchanged)  
**Primary Dependencies**: Next.js, Tailwind CSS v4, shadcn/ui (base-nova), lucide-react, `@/lib/api` (all already in use)  
**Storage**: MongoDB `messages` collection — **read-only reuse**, no schema or migration changes  
**Testing**: Backend pytest suite must stay green (197 tests, 600s timeout); frontend verified via manual browser checks + existing component patterns (no new test harness)  
**Target Platform**: Web — Next.js frontend (`app/`, `components/`, `lib/`) + FastAPI backend (`backend/`)  
**Project Type**: web  
**Performance Goals**: Dashboard loads ≤ 2s for up to 100 messages over localhost; existing Dashboard baseline (< 3s) must not regress  
**Constraints**: No AI calls / no re-classification in the UI (render stored `ai_analysis` only); every request stays `user_id`-scoped; reuse design tokens (`--signal`, `--ember`, `--cool`); keep the `max-w-5xl` container convention  
**Scale/Scope**: Single-user FYP demo — ≤ 200 messages, four priority groups plus a pending tail; no pagination UI in this phase (list limited to 100 by the existing endpoint)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

All gates below pass; no violations to justify.

- **I. Simplicity First** — No new endpoint. Client-side grouping over the
  existing `GET /messages` response is the simplest viable implementation
  and matches today's `MessageList` pattern.
- **II. Vertical Slices** — The dashboard card → group → page chain is one
  end-to-end slice that renders stored data only.
- **III. AI is Assistive, Not Magical** — Cards display stored
  `ai_analysis` verbatim (priority, reason, recommendation); the UI never
  re-scores or invokes agents.
- **IV. User Control** — Read-only view. Delete / priority-override remain
  on the existing pages and are untouched.
- **V. Security and Privacy** — No new secrets, no new endpoints, no
  logging changes.
- **VII. Progressive Enhancement** — Messages with `pending` / `skipped`
  or missing analysis still render (content preview + pending indicator).
- **Day 18 User Isolation** — `GET /messages` is already scoped to the
  authenticated `user_id` server-side; no new query path.
- **Day 23 Normalized Format** — Source label is read from the `source`
  enum (`whatsapp` / `gmail`); no channel-specific payloads in the UI.
- **Day 24 Orchestrator** — Dashboard consumes stored analysis only; zero
  agent invocations from the UI.
- **Day 27 Cross-Platform Dashboard** — One place for all platforms,
  priority-first grouping, clear source labels, current-user-only, simple
  design, empty groups hidden, recency ordering inside groups, no
  UI-side priority computation.
- **Compliance note**: The constitution names three groups; plan and spec
  adopt the user-requested **four** (URGENT, IMPORTANT, NORMAL, **LOW**),
  matching the stored `low` priority value. Amend the constitution's Day 27
  section before the feature ships.

## Project Structure

### Documentation (this feature)

```text
specs/018-cross-platform-dashboard/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
app/(dashboard)/dashboard/
└── page.tsx             # REWORK: renders PriorityDashboard; keeps HealthBadge +
                         # summary cards + NeedsAttentionSection + SimulateMessage

components/
├── PriorityDashboard.tsx    # NEW: fetches GET /messages, groups + sorts client-side
├── PrioritySection.tsx      # NEW: renders one group header + stacked cards
├── PlatformMessageCard.tsx  # NEW: single card (priority, title, source+sender, time,
                             #      optional deadline/subject/recommended action/attention)
├── MessageList.tsx          # UNCHANGED: still used by the Inbox
├── NeedsAttentionSection.tsx# UNCHANGED: stays above the priority groups
├── PriorityBadge.tsx        # REUSED as-is inside cards
├── EmptyState.tsx           # REUSED for the no-messages state
└── ... (other existing components unchanged)

lib/
├── priority.ts              # EXTEND: add color/label metadata for "low" (there:
│                            #       type currently lacks "low"/"pending" in ordering helpers)
└── ... (api.ts, use-time-ago.ts reused)

backend/
└── routes/messages.py       # NO CHANGES (GET /messages / counts already sufficient)
```

**Structure Decision**: Keep the existing Next.js root layout (`app/`,
`components/`, `lib/`) and the FastAPI `backend/`. The feature is a
frontend-only slice: rework `dashboard/page.tsx` and add three focused
components under `components/`. The `backend/` directory is intentionally
untouched — the constitution's Day 27 section requires the dashboard to
render stored data only, and the existing endpoint already returns
user-scoped messages with full `ai_analysis`.

## Implementation Steps

> Ordered, dependency-clean. Each step leaves the app in a runnable state.

1. **Extend `lib/priority.ts`** — add metadata for `low` (and keep a
   `pending` bucket) so labels/colors match the four-group design.
2. **Create `PlatformMessageCard.tsx`** — presentational card reading the
   `Message` + `ai_analysis` shape: priority badge, title (task desc →
   summary → content preview, truncated), `Source • Sender`, relative time,
   and optional deadline / subject / recommended action / attention badge.
   Missing fields are omitted, never rendered as `null`/`undefined`.
3. **Create `PrioritySection.tsx`** — a section header (label + count) and
   a stacked list of cards for one priority group; hidden when empty.
4. **Create `PriorityDashboard.tsx`** — fetch `GET /messages`, derive groups
   by `ai_analysis.priority`, order groups URGENT → IMPORTANT → NORMAL →
   LOW → Pending, order messages inside each group by `created_at` newest
   first; loading skeleton, empty state, and delete-with-confirm (reuse the
   `MessageList` dialog pattern).
5. **Rework `dashboard/page.tsx`** — replace the "Recent messages"
   `MessageList` with `<PriorityDashboard>`, keep the greeting, summary
   cards, `NeedsAttentionSection`, and `SimulateMessage`; wire `refreshKey`
   so simulating a message refreshes the grouped view.
6. **Smoke check** — run the app locally, simulate WhatsApp + Gmail
   messages, confirm grouping/ordering/labels.

## Testing Plan

- **Backend regression**: run the existing pytest suite (197 tests, 600s
  timeout) — nothing in `backend/` changes, so it must stay green.
- **Frontend type/lint sanity**: `next build` (or `tsc --noEmit`) to catch
  type errors in the new components.
- **Manual UI checks** (the repo's established practice for UI changes):
  - Simulate a WhatsApp message and a Gmail email → both appear in the same
    dashboard, in the correct priority group, with `WhatsApp • Sender` /
    `Gmail • Sender` labels.
  - Messages spanning all priorities (urgent/important/normal/low) → groups
    render in the fixed order; empty groups are hidden.
  - A message with `pending` analysis → appears in the Pending tail with a
    pending indicator; layout is not broken.
  - A message missing optional fields → card omits them cleanly.
  - Two-user isolation: log in as two users → each sees only their own
    messages.
  - Dark/light theme and mobile width render correctly.
  - Delete flow on a card updates the view immediately.
  - "Needs Your Attention" section still loads above the groups.

## Definition of Done

1. `/dashboard` shows all of the current user's messages from all sources
   in one priority-grouped view (no per-channel pages).
2. Groups order URGENT → IMPORTANT → NORMAL → LOW (→ Pending tail); empty
   groups hidden; messages within a group newest-first.
3. Every card shows priority, title, source + sender, and time; optional
   fields appear only when present in stored data.
4. `GET /messages` is the only data source — zero UI-side AI calls or
   re-classification, zero backend changes.
5. User isolation holds (two-user check passes); pending/failed analysis
   never breaks the layout.
6. Existing pytest suite passes; `next build`/type-check passes; manual
   verification on desktop + mobile + dark/light theme done.
7. Constitution v1.15.0's Day 27 section amended to include the LOW group.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution violations — this table is intentionally empty. The feature
adds no new services, endpoints, or repositories.