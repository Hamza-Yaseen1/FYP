# Feature Specification: Complete AI Pipeline

**Feature Branch**: `006-complete-ai-pipeline`  
**Created**: 2026-08-21  
**Status**: Draft  
**Input**: User description: "Create a clear and focused specification for Day 14 – Complete AI Pipeline. Individual parts are already working (Priority, Summary, Task Extraction, Deadline Detection, Recommended Action). Now we want the full pipeline to work smoothly and display clearly on the Dashboard."

## Feature Overview

Connect the five existing AI capabilities into one smooth end-to-end flow.
When a message arrives, it is automatically analyzed by every stage in
sequence, the complete result is saved once, and the Dashboard presents it
as a clear, scannable card. Urgent actionable messages are flagged with a
🔴 NEEDS ATTENTION badge so the user instantly knows where to focus.

**Success means**: A message goes in; a complete, understandable card comes
out — without the user reading raw messages or waiting on broken steps.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Full Analysis on Arrival (Priority: P1)

As a user, when a message arrives from any connected channel, I want the
system to automatically run the complete analysis (priority, summary,
tasks, deadlines, recommended action) and save it, so that everything I
need is ready on my dashboard without any manual steps.

**Why this priority**: This is the core promise of Day 14 — the parts
already work individually; connecting them delivers the product's main
value. Without this, nothing else in the feature matters.

**Independent Test**: Can be fully tested by sending one test message and
verifying that all five analysis results appear on the dashboard for that
message.

**Acceptance Scenarios**:

1. **Given** a message arrives with an action request and a deadline,
   **When** the pipeline completes, **Then** the dashboard shows the
   message with its priority, summary, extracted task, deadline, and
   recommended action together.
2. **Given** a purely informational message arrives, **When** the pipeline
   completes, **Then** the dashboard shows the message with priority and
   summary, zero tasks, no deadline, and a generic recommendation.
3. **Given** the same message is processed again, **When** the pipeline
   completes, **Then** the existing record is updated — no duplicate
   entries appear anywhere.

---

### User Story 2 - Needs Attention Flagging (Priority: P2)

As a user, I want genuinely urgent actionable messages flagged with a clear
🔴 NEEDS ATTENTION card that explains why and tells me what to do, so that
I can triage my dashboard at a glance.

**Why this priority**: The flag turns raw analysis into a decision. It
builds directly on User Story 1 and is the visible payoff of the pipeline.

**Independent Test**: Can be tested by sending one qualifying message
(task + near deadline) and one non-qualifying message, verifying only the
first gets the badge and reason line.

**Acceptance Scenarios**:

1. **Given** a message contains an actionable task with a near deadline
   (e.g., "Send FYP slides ... tonight"), **When** the pipeline completes,
   **Then** the card shows the 🔴 NEEDS ATTENTION badge, the task, the
   channel and sender, the deadline in original wording, a "Why it
   matters" line, and a recommended action.
2. **Given** a message is classified Urgent AND contains an actionable
   task, **When** the pipeline completes, **Then** the card is flagged
   NEEDS ATTENTION with a matching reason.
3. **Given** a message meets none of the flag criteria, **When** the
   pipeline completes, **Then** the card appears normally WITHOUT the
   badge and without a "Why it matters" line.

---

### User Story 3 - Graceful Degradation (Priority: P3)

As a user, I want the dashboard to remain useful even when part of the
analysis fails, so that a single weak step never hides my messages or
breaks the page.

**Why this priority**: Reliability matters, but it protects value already
delivered by Stories 1 and 2 rather than creating new value.

**Independent Test**: Can be tested by simulating a failure in one stage
(e.g., recommendation unavailable) and verifying the message still appears
with all other fields intact.

**Acceptance Scenarios**:

1. **Given** the recommendation step fails for a message, **When** the
   card is displayed, **Then** the message appears with all other fields
   and simply omits the recommendation line.
2. **Given** deadline detection fails for a message, **When** the card is
   displayed, **Then** the message appears without a deadline line and is
   NOT falsely flagged as NEEDS ATTENTION.
3. **Given** the entire analysis is delayed, **When** the user opens the
   dashboard, **Then** the interface remains responsive and shows a
   loading indication for the pending message.

---

### Edge Cases

- What happens when two signals conflict (priority says Urgent but no
  actionable task exists)? The message is NOT flagged — urgency alone is
  not enough; a task must exist.
- What happens when a message has a task but no deadline? It is flagged
  only if priority is Urgent; otherwise it appears normally.
- What happens when the same message is forwarded twice? The second copy
  updates the first record; no duplicates.
- What happens when a message is empty or contains only attachments?
  It is stored with default values (normal priority, empty summary, zero
  tasks) and never flagged.
- What happens when a message is in Arabic? All generated text (summary,
  tasks, recommendation, reason line) is returned in Arabic.
- What happens when the deadline expression is ambiguous ("before the
  meeting")? The original wording is preserved verbatim; nothing is
  invented or converted.
- What happens when the analysis service is completely down? Messages are
  stored unprocessed and appear on the dashboard with basic info; they can
  be analyzed later.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every incoming message MUST pass through all five analysis
  stages exactly once per processing run.
- **FR-002**: Stages MUST run in fixed order: Priority → Summary → Task
  Extraction → Deadline Detection → Recommended Action.
- **FR-003**: The five stages MUST share a single AI analysis pass (adding
  pipeline integration MUST NOT add extra AI round-trips).
- **FR-004**: The complete result MUST be saved as ONE record per message;
  the Dashboard MUST read saved results only and never trigger analysis
  itself.
- **FR-005**: The saved record MUST include: channel, sender, received
  time, priority, summary, extracted tasks, deadlines, recommended action,
  needs-attention flag, and attention reason.
- **FR-006**: The needs-attention flag MUST be set ONLY when (a) an
  actionable task was extracted AND a near-term deadline was detected, OR
  (b) priority is Urgent AND an actionable task was extracted.
- **FR-007**: Every flagged record MUST include an attention reason stating
  the actual trigger in plain language (e.g., "A task with a near deadline
  was detected."); reasons MUST NEVER be invented.
- **FR-008**: The card MUST render fields in fixed order: attention badge
  (if flagged), task description, channel • sender, deadline, why it
  matters (if flagged), recommended action.
- **FR-009**: Deadlines MUST be displayed in their original wording
  ("Tonight" stays "Tonight"; never a converted date/time).
- **FR-010**: Missing optional fields (deadline, recommendation) MUST be
  omitted cleanly — never shown as blank space, null, or undefined.
- **FR-011**: Reprocessing a message MUST update its existing record and
  MUST NOT create duplicates.
- **FR-012**: A failed stage MUST store its documented fallback value and
  MUST NOT block later stages, the save, or the card render.
- **FR-013**: Unflagged messages MUST appear on the dashboard identically
  to today, without the badge or reason line.

### Complete Pipeline Flow (step-by-step)

1. A message arrives from a connected channel (e.g., WhatsApp).
2. **Priority Agent** classifies it (Urgent / Important / Normal).
3. **Summary** produces a short digest of the message.
4. **Task Extraction** identifies actionable tasks directed at the user
   (zero if none).
5. **Deadline Detection** captures stated deadlines in original wording
   (none if absent).
6. **Recommended Action** produces one verb-first next step.
7. The complete result is evaluated against the Needs Attention rules and
   saved as a single record.
8. The Dashboard renders the saved record as a card.

### Rules for Showing "Needs Attention"

A message is flagged 🔴 NEEDS ATTENTION ONLY when at least one of these is
true of the SAVED analysis:

| # | Condition | Signals used |
|---|-----------|--------------|
| R1 | Actionable task extracted AND near-term deadline detected | Tasks + Deadline |
| R2 | Priority = Urgent AND actionable task extracted | Priority + Tasks |

Hard rules:

- The flag is derived from saved signals — never guessed, never manual.
- Every flag carries a truthful "Why it matters" line naming its trigger.
- No flag → no badge, no reason line; the card looks like it does today.
- False positives are worse than missed flags: if evidence is unclear,
  do not flag.

### How the "Needs Attention" Card Should Look

```text
🔴 NEEDS ATTENTION
Send FYP slides
WhatsApp • Ali
Deadline: Tonight
Why it matters: A task with a near deadline was detected.
Recommended: Send the slides before tonight.
```

| Line | Source | Rule |
|------|--------|------|
| 🔴 NEEDS ATTENTION | Flag evaluation | Only when R1/R2 met |
| Send FYP slides | Task extraction | User's own words |
| WhatsApp • Ali | Message metadata | Channel • sender |
| Deadline: Tonight | Deadline detection | Original wording kept |
| Why it matters: … | Attention reason | Names the real trigger |
| Recommended: … | Recommended action | One verb-first sentence |

Unflagged cards show the same layout minus the badge and reason lines.

### Key Entities

- **Message Analysis Record**: One record per received message containing:
  channel, sender, received time, original content, priority, summary,
  tasks (each with description, deadline wording, urgency hint),
  deadlines, recommended action, needs_attention (yes/no),
  attention_reason (text), and processing status. Persisted in the
  project's message store (MongoDB, per project convention).
- **Task**: An action the user must do, extracted from the message, with
  its stated deadline wording and urgency hint.
- **Needs Attention Card**: The dashboard view of a record — derived
  entirely from saved fields; contains no computed content of its own.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A message sent to the system appears on the dashboard with
  all available analysis fields within 10 seconds.
- **SC-002**: 100% of processed messages have a saved analysis record,
  even when individual stages fail.
- **SC-003**: 100% of NEEDS ATTENTION flags are explainable by their
  "Why it matters" line (zero invented reasons).
- **SC-004**: Zero duplicate records after reprocessing the same message.
- **SC-005**: A user can identify what needs their attention within
  5 seconds of opening the dashboard.
- **SC-006**: The dashboard stays responsive while analysis is running;
  users are never blocked by a pending analysis.

## Assumptions

- The five agents (Priority, Summary, Task Extraction, Deadline
  Detection, Recommended Action) are already working individually from
  Days 11–13 and need connection, not rebuilding.
- The message store and dashboard already exist and render analyzed
  messages; this feature changes what is saved and how cards present it.
- WhatsApp is the primary channel for testing; other channels follow the
  same flow.
- Flag rules may be tuned later; R1/R2 are the starting defaults aligned
  with the project constitution.

## Out of Scope

- Auto-executing any recommended action (everything stays advisory).
- Push notifications or alerts outside the dashboard.
- Adding new messaging channels.
- User-configurable flag rules or thresholds.
- Analytics or reporting on attention patterns.
