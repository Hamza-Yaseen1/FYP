---
id: phr-tasks-018-2026-09-11-001
stage: tasks
title: "cross-platform-dashboard-tasks"
date: 2026-09-11
feature: 018-cross-platform-dashboard
status: completed
---

# Prompt History Record

## PROMPT_TEXT

Create a clear and actionable task list for Day 27 – Cross-Platform Dashboard.

### Context
- Project: Communication AI
- Messages already come from WhatsApp (simulate) and Gmail
- AI priority analysis is working
- Now we need one unified Dashboard grouped by priority

### Goal:
Show all communications in one place, grouped like this:

🔴 URGENT
🟡 IMPORTANT
🟢 NORMAL

Each card should show:
- Title / summary / task
- Source (WhatsApp or Gmail)
- Sender
- Time
- Optional deadline / recommended action

### Focus Areas:
- Combine messages from all sources
- Group and sort by priority
- Update Dashboard UI for clear priority sections
- Keep existing "Needs Your Attention" working
- Only show current user's messages
- Keep design clean and consistent

### Requirements for the task list:
- Break work into small, clear, executable tasks
- Group tasks logically (Backend, Frontend, UI, Testing)
- Write tasks in action language
- Include acceptance criteria
- Follow Simplicity First principle

Save the file in the appropriate location.

## RESPONSE_TEXT

Wrote `specs/018-cross-platform-dashboard/tasks.md` — 23 tasks in the
template's checklist format `- [ ] T### [P?] [USx] Description ... AC: ...`.

Layout:
- **Phase 1 Setup** (2): T001 env confirm, T002 scope read + backend-untouched decision
- **Phase 2 Foundational** (1): T003 extend `lib/priority.ts` with low/pending metadata
- **Phase 3 US1 (P1, MVP)** (6): T004 PrioritySection, T005 PlatformMessageCard,
  T006 PriorityDashboard, T007 dashboard/page rework, T008 tsc, T009 manual grouping verify
- **Phase 4 US2 (P2)** (3): T010/T011 card optional fields + title fallback/truncation,
  T012 manual card verify
- **Phase 5 US3 (P2)** (3): T013 attention badge + why-it-matters, T014 attention
  section regression check, T015 manual verify
- **Phase 6 US4 (P3)** (4): T016 Pending tail, T017 empty state, T018 isolation
  verify, T019 graceful-states verify
- **Phase 7 Polish** (4): T020 pytest regression (197/600s), T021 tsc/build,
  T022 quickstart verification, T023 constitution LOW-group amendment

Category labels (Frontend / UI / Testing / Docs) embedded per task; backend
declared read-only (contracts/messages.md). Same-file sequencing noted for
PlatformMessageCard (US1→US2→US3) and PriorityDashboard (US4). Parallel
opportunities: T004/T005, T014, T018, polish trio. MVP = US1 only (4 tasks
+ foundation). Every task is a single checklist line with an AC criterion.