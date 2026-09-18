---
id: phr-spec-018-2026-09-11-001
stage: spec
title: "cross-platform-dashboard-spec"
date: 2026-09-11
feature: 018-cross-platform-dashboard
status: completed
---

# Prompt History Record

## PROMPT_TEXT

Create a clear and focused specification for Day 27 – Cross-Platform Dashboard.

### Context
- Project: Communication AI
- Messages are already coming from WhatsApp (simulate) and Gmail
- AI analysis (priority, summary, task, deadline, recommended action) is working
- Now we need one unified Dashboard that shows all communications together

### Goal:
Create a clean Cross-Platform Dashboard grouped by priority:

🔴 URGENT
- FYP presentation deadline
  WhatsApp • Ali

- Submit report
  Gmail • Teacher

🟡 IMPORTANT
- Review project requirements
  Gmail • Supervisor

🟢 NORMAL
- Project update
  WhatsApp • Team

### Requirements:
- Show messages from all sources (WhatsApp, Gmail, etc.) in one place
- Group clearly by priority (Urgent → Important → Normal → Low)
- Each card should show:
  - Priority
  - Main title / task or summary
  - Source + Sender
  - Time
  - Optional: Deadline and Recommended Action
- Only show messages of the logged-in user
- Keep the design clean and consistent with the current UI
- "Needs Your Attention" should still work well with this view

### Please include in the specification:
1. Feature Overview
2. User Stories
3. Dashboard layout rules
4. Card content rules
5. Sorting and grouping logic
6. Acceptance Criteria
7. Edge cases

Keep it practical and clean for a university FYP.

## RESPONSE_TEXT

Created branch `018-cross-platform-dashboard` and wrote `specs/018-cross-platform-dashboard/spec.md`.

Spec contents:
- **Feature Overview**: unified priority-first home screen for all channels
- **4 User Stories** (prioritized, independently testable):
  - US1 (P1): Unified Priority-Grouped Dashboard
  - US2 (P2): Informative Message Cards
  - US3 (P2): Needs Your Attention Integration
  - US4 (P3): User Isolation and Graceful States
- **Requirements**: 14 functional requirements (FR-001..FR-014)
- **Dashboard Layout Rules**: single scrollable view, priority sections top-to-bottom, cards stacked newest-first, attention stays visible, empty state
- **Card Content Rules**: priority indicator, main title (task→summary→preview), source+sender, relative time, optional deadline/subject/recommended action/attention
- **Sorting and Grouping Logic**: group by stored AI priority, fixed URGENT→IMPORTANT→NORMAL→LOW order, newest first, pending handling
- **Key Entities**: Message, ai_analysis, Priority group (derived), User
- **Success Criteria**: 8 measurable, technology-agnostic outcomes
- **Edge Cases**: 11 cases covering empty/pending/optional-field/long-content/unknown-channel scenarios

Quality checklist created at `specs/018-cross-platform-dashboard/checklists/requirements.md` — all items pass. No [NEEDS CLARIFICATION] markers used.

Compliance note: user requested four priority groups (incl. LOW); constitution v1.15.0 names three. Documented in checklist notes for `/sp.plan` to reconcile.