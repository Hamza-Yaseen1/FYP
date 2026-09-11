---
id: phr-constitution-2026-09-11-001
stage: constitution
title: "Day 27 Cross-Platform Dashboard Constitution"
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

Updated `.specify/memory/constitution.md` from v1.14.0 to v1.15.0 (MINOR bump). Added a new "Day 27 Cross-Platform Dashboard" section covering:

- **Purpose**: Unified view of all communications organized by priority
- **Core principles**: Priority-first grouping, one place for all platforms, clear source labels, current-user-only, simple/clean design
- **Card spec**: Priority indicator, message content/task description, source label + sender, timestamp; optional fields (deadline, subject, recommended action)
- **Grouping rules**: Priority-based groups, recency ordering within groups, empty groups hidden, all sources mix freely, user isolation absolute
- **Prohibitions**: No cross-user visibility, no source segregation, no UI-side priority computation, no empty group rendering, no raw timestamps, no blocking on AI, no content invention, no normalization bypass
- **Quality bar**: 10 criteria covering unified view, priority accuracy, source visibility, user isolation, recency ordering, empty state, missing field handling, responsive design, performance, no regression

Added 8 new compliance checklist items for the dashboard. Verified all templates (plan, spec, tasks) require no changes. Sync Impact Report prepended as HTML comment.
