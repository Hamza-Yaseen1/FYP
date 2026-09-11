---
id: phr-constitution-2026-09-11-002
stage: constitution
title: "Day 27 Dashboard Four-Group Amendment"
date: 2026-09-11
feature: day-27-cross-platform-dashboard
status: completed
---

# Prompt History Record

## PROMPT_TEXT

Create a focused constitution for Day 27 – Cross-Platform Dashboard.

### Context
- Project: Communication AI (FYP)
- We can already receive messages from WhatsApp (simulate) and Gmail
- AI analysis (priority, summary, tasks, etc.) is working
- Now we need one unified Dashboard that shows all communications together

### Goal of Day 27:
Create a clean Cross-Platform Dashboard that groups messages by priority:

🔴 URGENT
- FYP presentation deadline (WhatsApp • Ali)
- Submit report (Gmail • Teacher)

🟡 IMPORTANT
- Review project requirements (Gmail • Supervisor)

🟢 NORMAL
- Project update (WhatsApp • Team)

### Principles:
- One place for all platforms
- Priority-first organization
- Clear source label (WhatsApp / Gmail)
- Only show current user's messages
- Keep the design simple and clean

### Please create a short constitution that covers:
1. Purpose of the Cross-Platform Dashboard
2. Core organization principles
3. What information each card should show
4. Rules for grouping and ordering
5. Quality bar for this feature

Keep it practical and user-focused.

## RESPONSE_TEXT

Amended `.specify/memory/constitution.md` from v1.15.0 to v1.16.0 (MINOR).

The Day 27 section already existed (created in v1.15.0). This amendment
reconciled it with the four-group decision agreed during spec/plan/tasks
for branch 018-cross-platform-dashboard, closing the flagged follow-up:

- **Purpose & Core Principles**: add LOW priority level; pending/skipped/
  absent analysis must NOT pollute classified groups — they render in a
  separated "Pending analysis" tail.
- **Card content**: priority indicator covers 🔴🟡🟢⚪; main-title fallback
  explicit (task desc → AI summary → content preview).
- **Grouping/Ordering**: four fixed groups URGENT → IMPORTANT → NORMAL →
  LOW plus Pending tail; `pending`/missing analysis never merged into a
  classified group; recency ordering inside every group incl. tail.
- **MUST NOT**: added "NEVER merge pending/unanalyzed messages into
  classified groups".
- **Quality bar**: priority-accuracy item extended to pending-only-in-tail.
- **Compliance checklist**: the dashboard grouping item renamed to the
  four-group layout + pending tail.
- Sync Impact Report updated (1.15.0 → 1.16.0, modified sections listed,
  templates verified — none need changes). Version line bumped and
  Last Amended set to 2026-09-11.

Note: the attached outline described the implementation workflow
(check-prerequisites + tasks.md execution); the submitted content is a
constitution request, so the constitution was amended instead. If an
implementation run of the 23 cross-platform-dashboard tasks was intended,
invoke the corresponding implement command.