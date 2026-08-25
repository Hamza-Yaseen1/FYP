---
id: phr-spec-001
title: Better Inbox Specification
stage: spec
date: 2026-08-26
surface: cli
model: big-pickle
feature: 011-better-inbox
branch: 011-better-inbox
user: user
command: spec
labels: [spec, inbox, filtering, search, fyp]
links:
  spec: specs/011-better-inbox/spec.md
  plan: null
  ticket: null
  adr: null
  pr: null
files:
  - specs/011-better-inbox/spec.md
  - specs/011-better-inbox/checklists/requirements.md
tests: []
---

## Prompt

# Day 20 – Better Inbox

Create a specification for **Day 20 – Better Inbox** for the Communication AI project.

## Context

This is an existing Communication AI FYP project.

The following features are already working:

* Authentication
* User isolation
* Basic Dashboard
* Inbox/messages functionality
* Messages stored in the database
* Message source information such as WhatsApp/Gmail
* Message priority/status information

The goal of Day 20 is to improve the Inbox experience by adding better filtering and search functionality.

Do **not** redesign the entire application. Focus only on improving the existing Inbox.

---

## Feature Goal

Create a Better Inbox that allows users to quickly find and organize their communications.

The Inbox should provide:

### Main Tabs

Display the following inbox tabs:

* All
* Urgent
* Important
* Normal
* Unread

The tabs should allow the user to quickly filter messages based on their priority or read/unread status.

### Additional Filters

Provide filters for:

* Source
* Priority
* Date
* Sender

#### Source

The user should be able to filter messages based on their communication source, for example:

* WhatsApp
* Gmail
* Other supported sources

The filter should use the actual sources available in the system.

#### Priority

The user should be able to filter messages by:

* Urgent
* Important
* Normal

#### Date

The user should be able to filter communications based on date.

The specification should define appropriate date filtering behavior, such as selecting a specific date or date range.

#### Sender

The user should be able to filter communications by sender.

The sender filter should use senders that belong to the current user's available communications.

---

## Search

Add a search input with the placeholder:

`Search communications...`

The search should allow the user to find relevant communications.

Search should consider useful message information such as:

* Message content
* Sender
* Subject/title when available

Search results must only contain communications belonging to the currently authenticated user.

---

## Filtering Behavior

The specification must define how multiple filters work together.

For example:

If the user selects:

* Tab: Important
* Source: WhatsApp
* Sender: Ali

The Inbox should display only messages that satisfy all selected conditions.

Filters should work together rather than replacing each other.

The user should also be able to clear/reset filters and return to the normal Inbox view.

---

## User Isolation

This is a critical requirement.

A user must **never** be able to see another user's communications through:

* Inbox tabs
* Search
* Source filters
* Priority filters
* Date filters
* Sender filters
* Any combination of filters

Every Inbox query must respect the currently authenticated user.

Do not introduce any feature that bypasses the existing authentication or user-isolation system.

---

## Empty States

Define appropriate behavior when no communications match the selected filters or search query.

For example:

`No communications found`

The empty state should clearly communicate that the current filters/search produced no results.

---

## Loading and Error States

The specification should define expected behavior for:

* Loading communications
* Applying filters
* Performing searches
* Database/API errors
* Empty results

The UI should remain understandable and should not appear broken while data is loading.

---

## Performance Expectations

The Better Inbox should remain responsive when the user has a large number of communications.

Search and filtering should not require downloading unrelated users' messages to the client.

Where appropriate, filtering and searching should be handled through the backend/database rather than loading all messages into the browser.

---

## User Experience Requirements

The Inbox should make common actions fast and simple.

A user should be able to:

1. Open the Inbox.
2. See all relevant communications.
3. Quickly switch between All, Urgent, Important, Normal, and Unread.
4. Search for a communication.
5. Filter by source.
6. Filter by priority.
7. Filter by date.
8. Filter by sender.
9. Combine multiple filters.
10. Clear filters/search and return to all communications.

The interface should remain consistent with the existing application's design.

Do not introduce unnecessary UI components or unrelated functionality.

---

## Functional Requirements

The specification should include clear acceptance criteria for:

### Inbox Tabs

* All displays all communications belonging to the current user.
* Urgent displays urgent communications.
* Important displays important communications.
* Normal displays normal communications.
* Unread displays unread communications.

### Source Filter

* User can select a communication source.
* Results are limited to the selected source.
* Source filtering respects user isolation.

### Priority Filter

* User can select a priority.
* Results are limited to the selected priority.

### Date Filter

* User can select a date/date range.
* Results are limited to communications matching the selected date criteria.

### Sender Filter

* User can select a sender.
* Results contain only communications from that sender.

### Search

* User can search communications.
* Search works with message content.
* Search works with sender information.
* Search works with subject/title when available.
* Search respects user isolation.

### Combined Filtering

Multiple filters must work together.

For example:

`Important + WhatsApp + Ali + Date Range`

must return only communications satisfying all of those conditions.

### Reset

The user can clear active filters and search and return to the default Inbox state.

---

## Acceptance Criteria

Create measurable acceptance criteria using the project's existing specification style.

The feature should be considered complete only when:

* All five Inbox tabs are available.
* Each tab correctly filters communications.
* Source filtering works.
* Priority filtering works.
* Date filtering works.
* Sender filtering works.
* Search works.
* Multiple filters can be combined.
* Filters can be cleared/reset.
* Search can be cleared.
* Empty states are handled.
* Loading states are handled.
* Errors are handled gracefully.
* User isolation is maintained for every query.
* No communication belonging to another user can appear.
* Existing Inbox functionality continues to work.
* The feature follows the existing application's UI/design conventions.

---

## Out of Scope

Do not include the following in this Day 20 specification:

* New authentication system
* New user registration system
* New communication providers
* AI summarization
* AI reply generation
* Message sending
* Message deletion
* Notifications
* Major dashboard redesign
* Changes to unrelated pages
* New database technology

Keep the scope limited to the **Better Inbox filtering and search experience**.

---

## Specification Output

Produce a complete, implementation-ready specification for Day 20.

The specification should clearly describe:

1. User stories
2. Functional requirements
3. Filtering behavior
4. Search behavior
5. User-isolation requirements
6. UI/UX requirements
7. Loading/error/empty states
8. Combined filter behavior
9. Acceptance criteria
10. Edge cases
11. Out-of-scope items

Do not prescribe unnecessary implementation details.

Focus on **what the system must do and how it should behave**, not on specific code, libraries, or implementation techniques.

## Response snapshot

Created complete specification for Day 20 Better Inbox feature.

### Specification Structure

**User Stories**: 6 user stories covering priority tabs, source/priority filtering, date/sender filtering, search, combined filtering, and empty/loading states.

**Functional Requirements**: 20 requirements covering all aspects of the Better Inbox feature.

**Success Criteria**: 10 measurable outcomes covering performance, usability, and reliability.

**Key Features**:
- Five priority tabs (All, Urgent, Important, Normal, Unread)
- Source, priority, date, and sender filters
- Search across message content, sender, and subject
- Combined filtering with AND logic
- One-click reset for all filters
- User isolation for all queries
- Empty, loading, and error states
- Backend/database filtering for performance

### Quality Validation

All quality checklist items pass:
- No implementation details in spec
- Focused on user value
- Written for non-technical stakeholders
- All mandatory sections completed
- Requirements are testable and unambiguous
- Success criteria are measurable and technology-agnostic
- Edge cases identified
- Scope clearly bounded

## Outcome

- Impact: Complete specification for Day 20 Better Inbox feature
- Tests: None required (specification only)
- Files: specs/011-better-inbox/spec.md, specs/011-better-inbox/checklists/requirements.md
- Next prompts: /sp.plan for implementation planning
- Reflection: Specification covers all user requirements with clear acceptance criteria and measurable outcomes

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results: N/A
- Prompt variant: N/A
- Next experiment: N/A