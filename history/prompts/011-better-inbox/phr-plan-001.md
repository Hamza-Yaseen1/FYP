---
id: phr-plan-001
title: Better Inbox Implementation Plan
stage: plan
date: 2026-08-26
surface: cli
model: big-pickle
feature: 011-better-inbox
branch: 011-better-inbox
user: user
command: plan
labels: [plan, inbox, filtering, search, fyp]
links:
  spec: specs/011-better-inbox/spec.md
  plan: specs/011-better-inbox/plan.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/011-better-inbox/plan.md
  - specs/011-better-inbox/research.md
  - specs/011-better-inbox/data-model.md
  - specs/011-better-inbox/quickstart.md
  - specs/011-better-inbox/contracts/messages-api.md
tests: []
---

## Prompt

# Day 20 – Better Inbox Implementation Plan

Create a practical implementation plan for the Day 20 – Better Inbox feature based on the approved specification and project constitution.

## Goal

Improve the existing Inbox by adding:

* Inbox tabs: All, Urgent, Important, Normal, Unread
* Filters: Source, Priority, Date, Sender
* Search: `Search communications...`
* Combined filtering
* Filter reset/clear functionality
* Loading, empty, and error states
* Strict current-user data isolation

## Planning Requirements

Create a concise implementation plan covering:

1. **Frontend changes**

   * Inbox tabs
   * Search input
   * Filter controls
   * Active filter/reset behavior
   * Message list updates
   * Loading and empty states

2. **Backend/API changes**

   * Support search and filtering
   * Support combined filters
   * Ensure queries are restricted to the authenticated user
   * Keep existing Inbox functionality working

3. **Database/query changes**

   * Identify the message fields required for filtering/search
   * Use efficient queries where appropriate

4. **Testing**

   * Test each filter individually
   * Test search
   * Test multiple filters together
   * Test reset behavior
   * Test empty/error states
   * Verify that one user can never access another user's messages

## Important Constraints

* Follow the existing project architecture and coding patterns.
* Reuse existing components and APIs where possible.
* Do not introduce unnecessary dependencies.
* Do not redesign unrelated parts of the application.
* Keep the implementation focused only on Day 20 – Better Inbox.

Provide the plan in clear implementation steps with the files/components likely to be affected.

## Response snapshot

Created complete implementation plan for Day 20 Better Inbox feature.

### Plan Structure

**Phase 0 (Research)**: Completed research.md with:
- Decision on backend filtering with query parameters
- Decision on MongoDB text search for search functionality
- Decision on AND logic for combined filters
- Decision on rebuilding inbox page using existing components
- Verified all existing message fields are sufficient for filtering

**Phase 1 (Design)**: Created:
- data-model.md: Documented existing Message entity and new FilterCounts response
- contracts/messages-api.md: Defined 4 API endpoints with full request/response schemas
- quickstart.md: Provided step-by-step guide for testing the feature

**Phase 2 (Implementation Plan)**: Detailed 3-phase implementation:

**Backend API Extensions**:
1. Add MongoDB text index on sender, content, summary
2. Extend GET /messages with query parameters (tab, source, priority, dates, sender, search)
3. Add GET /messages/counts for filter counts
4. Add GET /messages/senders for sender filter dropdown
5. Add GET /messages/sources for source filter dropdown

**Frontend Components**:
1. Create InboxTabs component for priority tabs
2. Create FilterBar component for dropdown filters
3. Create SearchBar component with debounced search
4. Create EmptyState component for empty results
5. Rebuild inbox page with state management and API integration

**Testing**:
1. Backend API tests for filtering and search
2. Frontend component tests for UI interactions
3. Integration tests for complete flows
4. User isolation verification tests

### Key Decisions

- **Backend filtering**: All filtering/search on server-side (FR-020 compliance)
- **MongoDB text index**: Enable efficient search across multiple fields
- **AND logic**: Filters compose to narrow results
- **Reuse components**: Use existing MessageList, extend with new filter/search UI
- **User isolation**: Maintained at query level with user_id filter always included

### Files Created

- `specs/011-better-inbox/plan.md` - Main implementation plan
- `specs/011-better-inbox/research.md` - Research findings and decisions
- `specs/011-better-inbox/data-model.md` - Data model documentation
- `specs/011-better-inbox/quickstart.md` - Quickstart guide
- `specs/011-better-inbox/contracts/messages-api.md` - API contract

## Outcome

- Impact: Complete implementation plan for Day 20 Better Inbox feature
- Tests: None required (planning phase only)
- Files: specs/011-better-inbox/ (plan.md, research.md, data-model.md, quickstart.md, contracts/messages-api.md)
- Next prompts: /sp.tasks for task breakdown
- Reflection: Plan extends existing architecture with minimal changes, follows constitution principles

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results: N/A
- Prompt variant: N/A
- Next experiment: N/A