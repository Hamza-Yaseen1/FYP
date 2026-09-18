---
id: phr-plan-018-2026-09-11-001
stage: plan
title: "cross-platform-dashboard-plan"
date: 2026-09-11
feature: 018-cross-platform-dashboard
status: completed
---

# Prompt History Record

## PROMPT_TEXT

Create a practical technical implementation plan for Day 27 – Cross-Platform Dashboard.

### Context
- Project: Communication AI
- Frontend: Next.js + TypeScript + Tailwind + shadcn/ui
- Backend: FastAPI + MongoDB
- Messages already come from WhatsApp (simulate) and Gmail
- AI analysis (priority, summary, task, etc.) is working
- User isolation is working

### Goal:
Build a unified Cross-Platform Dashboard that shows all communications grouped by priority:

🔴 URGENT
🟡 IMPORTANT
🟢 NORMAL

Each item should clearly show source (WhatsApp / Gmail) and sender.

### Please include in the plan:
1. Goal of this phase
2. Technical approach
3. How messages from different sources will be combined
4. Grouping and sorting logic (by priority)
5. Frontend components to create or update
6. API changes needed (if any)
7. Implementation steps in order
8. Testing plan
9. Definition of Done

Keep it simple, clean, and consistent with the current design system.

## RESPONSE_TEXT

Wrote `specs/018-cross-platform-dashboard/plan.md` plus Phase 0/1 artifacts.

**Approach** (decided in research.md): frontend-only vertical slice.
Reuse existing user-scoped `GET /messages`; group client-side by stored
`ai_analysis.priority` — no new endpoint, no schema change, no AI changes.
Backend `backend/routes/messages.py` is untouched.

**Grouping/sorting**: URGENT → IMPORTANT → NORMAL → LOW → Pending tail;
newest-first inside groups (created_at desc); empty groups hidden; pending
/missing analysis lands in a Pending tail with an indicator.

**Components**: NEW `PriorityDashboard.tsx` (fetch+group),
`PrioritySection.tsx` (group header + cards), `PlatformMessageCard.tsx`
(card: priority, title task→summary→preview, source+sender, time, optional
deadline/subject/recommended action/attention). REWORK
`app/(dashboard)/dashboard/page.tsx` to render it. EXTEND `lib/priority.ts`
with `low`. REUSE MessageList (Inbox), NeedsAttentionSection,
PriorityBadge, EmptyState, useTimeAgo.

**Artifacts generated**:
- research.md — 5 unknowns resolved (grouping location, group order,
  card field mapping, source labels, backend changes=non)
- data-model.md — no schema change; derived PriorityGroup documented
- contracts/messages.md — documents existing GET /messages (no new
  endpoints)
- quickstart.md — run + 7-point verification
- AGENTS.md — agent context updated (Active Technologies for 018)

**Constitution Check**: all gates pass. Compliance note: user requires
four groups incl. LOW; constitution v1.15.0 names three — amend Day 27
section before shipping. Testing: pytest suite must stay green (197 tests,
600s), next build/tsc sanity, manual UI checks incl. two-user isolation.
Definition of Done: 7 criteria.