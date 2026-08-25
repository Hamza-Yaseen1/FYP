---
id: phr-const-005
title: Better Inbox Constitution
stage: constitution
date: 2026-08-26
surface: cli
model: big-pickle
feature: general
branch: main
user: user
command: constitution
labels: [constitution, inbox, filtering, search, fyp]
links:
  spec: null
  plan: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/memory/constitution.md
  - README.md
tests: []
---

## Prompt

Create a focused constitution for Day 20 – Better Inbox.

### Context
- Project: Communication AI (FYP)
- Authentication, User Isolation, and basic Dashboard are already working
- Now we need a much better Inbox experience

### Goal of Day 20:
Improve the Inbox page with clear filters and search.

Inbox should have tabs/filters:
- All
- Urgent
- Important
- Normal
- Unread

Additional filters:
- Source (WhatsApp, Gmail, etc.)
- Priority
- Date
- Sender

Search bar:
- "Search communications..."

### Please create a short constitution that covers:
1. Purpose of the Better Inbox
2. Core principles for filtering and searching
3. What the user should be able to do quickly
4. Rules for showing messages (only current user’s messages)
5. Quality bar for this feature

Keep it practical, clean, and user-focused.

## Response snapshot

Updated constitution at `.specify/memory/constitution.md` with Day 20 Better Inbox section.

### Constitution Structure

**Day 20 Better Inbox (new section added):**
- Purpose of Better Inbox
- Core Filtering Principles (6 principles)
- User Capabilities (9 capabilities)
- Message Display Rules (5 rules)
- Quality Bar for Better Inbox (8 quality metrics)

**Updated existing sections:**
- Compliance Review: added 12 new inbox-related checks
- Version bumped: 1.7.0 → 1.8.0 (MINOR: new feature section)
- Last Amended date: 2026-08-26

### Key Design Decisions
- Version bump: 1.7.0 → 1.8.0 (MINOR: new feature section)
- Priority tabs (All, Urgent, Important, Normal, Unread) are primary navigation
- Source filtering is secondary (WhatsApp, Gmail, LinkedIn, etc.)
- Search bar searches across sender, subject, and content fields
- Filters compose (priority + source work together)
- One-click reset clears all filters
- User isolation extends to inbox (only current user's messages shown)
- Performance target: filtering/search under 200ms for 1000 messages
- Empty states, loading states, responsive design, and accessibility included

## Outcome

- Impact: Governance document for Day 20 Better Inbox feature
- Tests: None required (constitution only)
- Files: .specify/memory/constitution.md, README.md
- Next prompts: /sp.spec or /sp.plan for Better Inbox feature
- Reflection: Constitution extends existing principles (II, Vertical Slices; IV, User Control) with concrete inbox rules

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results: N/A
- Prompt variant: N/A
- Next experiment: N/A