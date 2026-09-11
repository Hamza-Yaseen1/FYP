---

description: "Task list for feature implementation"
---

# Tasks: Cross-Platform Dashboard

**Input**: Design documents from `/specs/018-cross-platform-dashboard/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Testing tasks are included (user requested Testing as a group). Backend is read-only — testing there is a regression guard only. Frontend follows the repo's established convention: `tsc` type-check + manual browser verification (no separate test harness).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. Categories (Backend / Frontend / UI / Testing) are labeled inline in each task description.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Include exact file paths in descriptions
- Each task ends with an **AC:** acceptance criterion

## Path Conventions

- **Next.js app (frontend)**: `app/`, `components/`, `lib/` at repository root
- **Backend**: `backend/` (FastAPI + MongoDB) — **NO CHANGES in this feature** (verified in contracts/messages.md)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm environment and orient on the feature scope

- [ ] T001 Confirm branch `018-cross-platform-dashboard` is checked out and both dev servers run (Next.js on :3000, FastAPI on :8000) with a logged-in session. AC: dashboard loads without console errors.
- [ ] T002 [P] Read `specs/018-cross-platform-dashboard/spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/messages.md`; confirm backend/ and the `messages` schema require zero changes. AC: note the "backend untouched" decision in the PR description.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared piece every priority group + badge needs before ANY user story can render

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 Extend `lib/priority.ts` with full priority metadata (label, color mapping, sort order) covering `urgent`, `important`, `normal`, `low`, `pending`. AC: helpers exist for all five values and existing `PriorityBadge` / Inbox imports still resolve.

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Unified Priority-Grouped Dashboard (Priority: P1) 🎯 MVP

**Goal**: The `/dashboard` page shows all of the user's messages in one view, grouped URGENT → IMPORTANT → NORMAL → LOW, newest first inside each group, empty groups hidden.

**Independent Test**: Simulate a WhatsApp message and send a Gmail email with different priorities — both appear side-by-side in the correct priority groups inside a single view.

**Backend check**: None needed. `GET /messages` already returns user-scoped messages with full `ai_analysis` (contracts/messages.md).

### Implementation for User Story 1

- [ ] T004 [P] [US1] Frontend — Create `components/PrioritySection.tsx` (props: `priority`, `label`, `messages`, `onDelete`) rendering a `triage-label` header with per-group count and a stacked `PlatformMessageCard` list; returns `null` when the messages array is empty. AC: empty groups render no header.
- [ ] T005 [US1] Frontend — Create `components/PlatformMessageCard.tsx` core: `PriorityBadge` (reuse `components/PriorityBadge.tsx`), main title from `ai_analysis.tasks_extracted[0].description`, `Source • Sender` label (`source` uppercase pill + icon: `MessageCircle` for whatsapp, `Mail` for gmail), relative time via `lib/use-time-ago.ts`, delete action like `components/MessageList.tsx`. AC: card renders for a whatsapp and a gmail message with all four core fields.
- [ ] T006 [US1] Frontend — Create `components/PriorityDashboard.tsx`: fetch `GET /messages` via `lib/api.ts` `apiFetch`, group by `ai_analysis.priority` into urgent/important/normal/low, sort each group by `created_at` descending, render fixed-order non-empty `PrioritySection`s, show `components/LoadingSkeleton.tsx` while loading. AC: grouped payload renders in the exact order URGENT, IMPORTANT, NORMAL, LOW, newest first per group.
- [ ] T007 [US1] Frontend — Rework `app/(dashboard)/dashboard/page.tsx`: replace the "Recent messages" block with `<PriorityDashboard refreshKey={refreshKey}/>`; keep greeting, summary cards, `NeedsAttentionSection`, and `SimulateMessage`; keep `onSent` refresh wiring. AC: simulating a message refreshes the grouped view.
- [ ] T008 [US1] Testing — Run `npx tsc --noEmit` and fix any type errors in the new `app/(dashboard)/dashboard/page.tsx`, `components/PriorityDashboard.tsx`, `components/PrioritySection.tsx`, `components/PlatformMessageCard.tsx`. AC: type check passes for the changed files.
- [ ] T009 [US1] Testing — Manual verify: simulate WhatsApp + Gmail messages with different priorities (urgent/important/normal/low); confirm one unified view, correct groups, hidden empty groups, newest-first ordering. AC: matches the goal diagram (URGENT 🟡 IMPORTANT 🟢 NORMAL).

**Checkpoint**: At this point, User Story 1 delivers the MVP — a fully functional priority-grouped dashboard.

---

## Phase 4: User Story 2 - Informative Message Cards (Priority: P2)

**Goal**: Cards are complete and scannable: optional deadline, recommended action, Gmail subject, summary/content fallback title, truncation; missing optional fields omitted cleanly.

**Independent Test**: Render a card for a message with stored deadline + recommended action (both appear), then a message lacking them (clean omission — no "null"/"undefined"/blank gaps).

### Implementation for User Story 2

- [ ] T010 [US2] UI — Extend `components/PlatformMessageCard.tsx` with optional deadline (`ai_analysis.tasks_extracted[0].deadline`, original wording e.g. "Tonight") and recommended-action box (reuse the styled box from `components/MessageList.tsx` lines 219-226). AC: both render only when present in stored data.
- [ ] T011 [US2] UI — Extend `components/PlatformMessageCard.tsx` title logic: show Gmail `subject` line ("Re: subject") when present; fall back title to `ai_analysis.summary` then `content` preview; truncate long titles with `line-clamp` + ellipsis. AC: a message with no task uses summary/preview; gmail subject visible; long content is truncated.
- [ ] T012 [US2] Testing — Manual verify cards: message with deadline + recommended action shows both; message missing optional fields omits them cleanly; long content truncates. AC: zero "null"/"undefined"/blank-gap renders.

**Checkpoint**: User Stories 1 AND 2 both working and independently testable.

---

## Phase 5: User Story 3 - Needs Your Attention Integration (Priority: P2)

**Goal**: Flagged messages stay visible and truthful in the dashboard — badge + "Why it matters" on the card, with the existing attention section still above the groups.

**Independent Test**: Create a message meeting the attention criteria; its card shows the badge and a truthful reason; `/attention` still works.

### Implementation for User Story 3

- [ ] T013 [US3] UI — Extend `components/PlatformMessageCard.tsx` to render a "Needs attention" badge and a "Why it matters" line (`ai_analysis.attention_reason`) when `ai_analysis.needs_attention` is true, matching `components/NeedsAttentionCard.tsx` styling (ember border/badge). AC: flagged cards show badge + truthful reason; unflagged cards render nothing extra.
- [ ] T014 [P] [US3] Test — Verify `components/NeedsAttentionSection.tsx` still loads on the reworked dashboard above the priority groups (no code change expected). AC: flagged messages appear in the attention section without regression.
- [ ] T015 [US3] Testing — Manual verify: flagged card in dashboard shows badge + "Why it matters"; `/attention` page unchanged and functional. AC: attention truthfulness holds — reason names the real trigger.

**Checkpoint**: User Stories 1-3 working and independently testable.

---

## Phase 6: User Story 4 - User Isolation and Graceful States (Priority: P3)

**Goal**: Dashboard shows only the current user's messages; clean empty state; pending/failed analysis never breaks the layout (Pending tail).

**Independent Test**: Two-user check + zero-message account + a pending-analysis message.

### Implementation for User Story 4

- [ ] T016 [US4] Frontend — Add the Pending tail to `components/PriorityDashboard.tsx`: messages with `priority: "pending"` or missing `ai_analysis` render in a final "Pending analysis" group (lower emphasis, pending badge) after LOW; never merged into classified groups. AC: pending messages don't shift classified groups or break ordering.
- [ ] T017 [US4] UI — Add empty-state handling to `components/PriorityDashboard.tsx`: when no messages exist render the existing "No messages" empty state (reuse `components/EmptyState.tsx`) instead of blank sections. AC: a zero-message account shows a friendly empty state.
- [ ] T018 [P] [US4] Testing — Manual verify isolation: register/log in as a second user; confirm each dashboard shows only that user's messages via both UI and direct API calls (including guessed ids). AC: zero cross-user data visible.
- [ ] T019 [US4] Testing — Manual verify graceful states: zero-message account shows empty state; a message with pending/skipped analysis lands in the Pending tail without breaking the layout. AC: dashboard never blocks or breaks on missing analysis.

**Checkpoint**: All user stories fully functional.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Regression safety and consistency sweep before merge

- [ ] T020 [P] Testing — Run the full backend pytest suite in `backend/` (~197 tests, 600s shell timeout) to confirm zero regressions (no backend code changed). AC: full suite passes.
- [ ] T021 [P] Testing — Run `npx tsc --noEmit` (or `npm run build`) over the whole app. AC: type check/build passes with no new errors.
- [ ] T022 Verify the feature against `specs/018-cross-platform-dashboard/quickstart.md` on desktop + mobile widths and light + dark themes; confirm no source pill/icons, spacing, or card rendering regressions. AC: all quickstart verification steps pass.
- [ ] T023 [P] Docs — Amend the constitution's Day 27 Cross-Platform Dashboard section in `.specify/memory/constitution.md` to include the LOW group (user-requested four-group layout), bump version and last-amended date. AC: constitution groups match the shipped dashboard; Sync Impact Report updated.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational completion
  - US1 (P1) first; US2/US3 build on the card file from US1; US4 last
- **Polish (Final Phase)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: After Foundational. No dependencies on other stories.
- **User Story 2 (P2)**: After US1 — extends `components/PlatformMessageCard.tsx` created in US1.
- **User Story 3 (P2)**: After US2 — extends the same card file further (sequential by file, not by value).
- **User Story 4 (P3)**: After US1; refines `components/PriorityDashboard.tsx`.

### Within Each User Story

- Same-file edits are sequential: `PlatformMessageCard.tsx` is written in US1 (T005), extended in US2 (T010, T011), extended again in US3 (T013). `PriorityDashboard.tsx` refined in US4 (T016, T017). Do NOT run these in parallel.
- Component creation before integration (T004/T005 before T006 before T007).
- Manual verification after implementation (per-story Testing tasks).

### Parallel Opportunities

- `T002` (Setup) independent of `T001`.
- `T004` (`PrioritySection.tsx`) and component scaffolding in US1 can be authored together with `T005` (`PlatformMessageCard.tsx`) — separate files.
- `T014` (attention section regression check) is independent of `T013`.
- `T018` (isolation verification) independent of `T016`/`T017`.
- Polish: `T020`, `T021`, `T023` all independent — run together.

---

## Parallel Example: User Story 1

```bash
# Launch the two new-file components together (T004, T005):
Task: "Create PrioritySection component in components/PrioritySection.tsx"
Task: "Create PlatformMessageCard component in components/PlatformMessageCard.tsx"

# After both land, wire them up sequentially (T006 → T007), then verify (T008 → T009)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (`lib/priority.ts`)
3. Complete Phase 3: User Story 1 (PriorityDashboard + PrioritySection + PlatformMessageCard + page rework)
4. **STOP and VALIDATE**: The dashboard groups whatsapp + gmail by priority — the core feature is demoable
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → foundation ready
2. US1 → grouped dashboard (MVP)
3. US2 → informative cards (deadline, subject, recommended action, truncation)
4. US3 → "Needs Your Attention" integration
5. US4 → isolation + empty/pending states
6. Polish → full regression + constitution amendment

---

## Notes

- **Backend is intentionally untouched** — see `contracts/messages.md`; all `GET /messages` behavior stays the same.
- `[P]` tasks = different files, no dependencies. Same-file tasks are sequential by construction.
- [USx] label maps task to its user story for traceability.
- Each user story is independently completable and testable.
- Verify types matter: run `npx tsc --noEmit` after each story phase.
- Commit after each task or logical group; stop at any checkpoint to validate the story independently.
- **Constitution follow-up (T023)**: the shipped dashboard uses four priority groups including LOW; the constitution's Day 27 section currently names three — amend before merge.