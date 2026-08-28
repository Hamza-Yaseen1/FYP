# Feature Specification: AI Orchestrator (Day 24)

**Feature Branch**: `015-ai-orchestrator`  
**Created**: 2026-08-29  
**Status**: Draft  
**Input**: User description: "Create a clear and focused specification for Day 24 – AI Orchestrator"

## Feature Overview

Day 24 adds a central **AI Orchestrator** that sits between message ingestion
and the existing AI capabilities — Priority, Summary, Task Extraction,
Deadline Detection, and Recommended Action. Today every incoming message gets
the full analysis treatment through one combined AI call. The Orchestrator
changes that: for each new message it decides *what the system needs to know*
and routes the message to exactly those agents that add value. Trivial
messages are handled cheaply, rich messages get full treatment, and nothing
irrelevant is ever computed.

The Orchestrator is deliberately simple: it is **one** decision layer, not a
multi-agent framework. It keeps a single AI analysis call for the messages
that need one, records every routing decision for transparency (AI is
Assistive, not Magical), and leaves the Dashboard untouched — the Dashboard
keeps reading stored results only.

**Goal**: When a new message arrives, decide which agents need to run, run
them, and save one combined result — priority, summary, tasks, deadline,
recommended action — exactly as the Dashboard expects today.

**Out of scope**: a general multi-agent framework (agent-to-agent messaging,
orchestration runtime, agent SDKs), re-routing already-stored messages, and
per-user routing preferences.

## Purpose of the Orchestrator

The Orchestrator answers one question per message: **"What do we need to know
about this message — and which agents tell us?"**

```text
New Message
  ↓
AI Orchestrator
  ↓
Decides what is needed
  ↓
Priority Agent / Summary Agent / Task Agent / etc.
  ↓
Final combined result saved
```

It exists for three reasons:

1. **Efficiency** — trivial messages ("ok", "hi", one-word replies) do not
   need full analysis. Routing them to a minimal subset keeps the system fast
   and cheap.
2. **Clarity** — one clear orchestration layer is better than scattered AI
   calls. Every AI decision flows through a single, auditable path.
3. **Agentic behavior** — the system starts deciding *what it needs to know*
   instead of blindly running every capability. This is the first step toward
   a more agentic Communication AI.

## Decision Logic

The Orchestrator is **rule-based first**: it routes using cheap, deterministic
signals (content length, channel, sender, trigger keywords) and only spends an
AI analysis call when it adds value. It does not run a model just to make
routing decisions — that would defeat the purpose.

### What it MUST decide (in order)

1. **Whether to analyze at all.** No analyzable content (empty,
   whitespace-only, media-only with no text) → store the message without AI
   analysis and mark it accordingly.
2. **Which agents run.** From the five agents, select the smallest subset that
   serves the message:
   - **Priority** — always runs; every inbox and Dashboard view depends on it.
   - **Summary** — runs for every message except trivial one-liners where the
     summary would just duplicate the content.
   - **Task Extraction** — runs only when the message plausibly requests an
     action (task-trigger words: send, review, submit, confirm, prepare,
     call, ...).
   - **Deadline Detection** — runs only when a time expression is present
     ("tonight", "tomorrow", "by Friday", "ASAP", ...).
   - **Recommended Action** — runs only when a next step is warranted;
     otherwise it falls back to the honest default ("Review this message").
3. **Whether an AI analysis call is needed at all.** Trivial content →
   deterministic defaults are stored, zero AI spend. Otherwise → exactly one
   combined AI analysis call for all selected agents (never one call per
   agent).
4. **The execution order.** Priority first, Recommended Action last; the
   Orchestrator fixes the order and agents cannot reorder themselves.

### Routing fallback

When the Orchestrator cannot decide confidently (ambiguous text, unfamiliar
language, mixed signals), it MUST default to **full analysis** — failing toward
completeness, never toward skipping information a user might need.

## Input / Output

### Input

A normalized message — the same canonical record produced by all channels and
the simulate endpoint (established in Day 23). The attributes used for routing:
channel / source, sender, content, content length, and the presence of
task-trigger or time-expression signals.

### Output

One combined analysis result with the same shape the Dashboard reads today:

| Field | Content | Routing rule |
|---|---|---|
| `priority` | Urgent / Important / Normal | Always produced |
| `summary` | Short plain-language summary | Produced unless the message is trivial |
| `tasks` | Extracted tasks | Produced only when Task Extraction runs |
| `deadline` | Original time expression or none | Produced only when Deadline Detection runs |
| `recommended_action` | One clear next step | Produced only when a next step is warranted |

Plus a **routing record** saved alongside the analysis stating which agents
ran, which were skipped, the trigger for the decision, and whether an AI call
was used. A skipped agent and a failed agent MUST be distinguishable in this
record.

The combined result and routing record are saved as **one update** for the
message; the Dashboard keeps reading stored data only.

## How It Works with Existing Agents

The five agents stay exactly as they are — same outputs, same contract. The
Orchestrator is the only new piece and it decides when each one contributes.

```text
Message arrives (WhatsApp webhook or simulate)
  ↓
AI Orchestrator (rule-based routing)
  ↓  decides: analyze? which agents? AI call needed? order
  ↓
Priority Agent                  (always)
Summary / Task / Deadline       (as routed)
  ↓
Recommended Action               (when routed)
  ↓
One combined result + routing record saved
  ↓
Dashboard (reads stored results — unchanged)
```

- Nothing bypasses the Orchestrator: no service, endpoint, webhook, or
  Dashboard component calls an agent directly.
- The Dashboard is untouched — NEEDS ATTENTION flags, "Why it matters" lines,
  and card rendering all keep working because the stored result keeps its
  shape.
- Idempotency is preserved: a duplicate delivery is caught before the
  Orchestrator runs (Day 23), so it does not re-route or re-analyze.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Every Message Gets Exactly the Analysis It Needs (Priority: P1)

As a user, I want each message routed to the analyses that matter for it, so
trivial messages are handled instantly and important messages get full
treatment.

**Why this priority**: This is the entire purpose of the Orchestrator.
Everything else supports a correct, efficient routing decision.

**Independent Test**: Send a set of messages — a greeting, an action request
without a deadline, an action request with "tonight", and a peer-to-peer FYI —
and confirm each stored result contains exactly the expected subset of
analyses.

**Acceptance Scenarios**:

1. **Given** a trivial message such as "ok" or "hi", **When** it is processed,
   **Then** it receives only priority, plus a summary when meaningful, with no
   tasks, no deadline, and no invented recommendation.
2. **Given** a message with an action request and a time expression such as
   "Send the slides tonight", **When** it is processed, **Then** it receives
   priority, summary, task extraction, deadline detection, and a recommended
   action.
3. **Given** a message with an action request but no time expression such as
   "Please call me", **When** it is processed, **Then** it receives priority,
   summary, and task extraction, with no deadline.
4. **Given** an ambiguous or unfamiliar message, **When** the Orchestrator
   cannot decide confidently, **Then** the message receives full analysis
   rather than a possibly-missing treatment.

---

### User Story 2 - A Single Clear Orchestration Layer (Priority: P1)

As a developer, I want all AI activity to flow through one orchestrator, so the
system has a single auditable path and no scattered AI calls.

**Why this priority**: This is the architectural guarantee that keeps the
feature maintainable and explainable.

**Independent Test**: Verify that every incoming message passes through the
Orchestrator — code inspection confirming no direct agent calls elsewhere,
plus runtime logs showing one routing decision per message.

**Acceptance Scenarios**:

1. **Given** any incoming message, **When** it is processed, **Then** it
   passes through the Orchestrator exactly once and a routing decision is
   recorded.
2. **Given** the existing system, **When** the Orchestrator is in place,
   **Then** no agent is invoked from a service, endpoint, or Dashboard
   component outside the Orchestrator.

---

### User Story 3 - Final Result Is Unchanged for the Dashboard (Priority: P1)

As a user, I want the Dashboard to keep working exactly as it does today, with
the same cards and fields.

**Why this priority**: The Orchestrator must not break an already-working
feature. The Dashboard contract is the compatibility guarantee.

**Independent Test**: Run the existing dashboard flows (simulated and real
messages) and confirm cards render identically to before, with all expected
fields.

**Acceptance Scenarios**:

1. **Given** a message routed to full analysis, **When** it is saved, **Then**
   the stored result contains priority, summary, tasks, deadline, and
   recommended action, and the Dashboard card shows them as before.
2. **Given** the Dashboard, **When** any message is analyzed, **Then** the
   Dashboard renders from stored results only — it gains no dependency on the
   Orchestrator at render time.

---

### User Story 4 - Trivial Messages Cost Almost Nothing (Priority: P2)

As a user, I want trivial messages handled without wasting a full AI analysis,
so the system stays fast and cheap under load.

**Why this priority**: This is the efficiency payoff of the feature and
protects the AI budget.

**Independent Test**: Send a set of trivial messages and confirm each is
stored with deterministic defaults and no AI analysis call, while still
appearing on the Dashboard.

**Acceptance Scenarios**:

1. **Given** a trivial message, **When** it is processed, **Then** it is
   stored with deterministic defaults and makes no AI analysis call.
2. **Given** a trivial message, **When** it is processed, **Then** it still
   appears on the Dashboard with the correct priority surface and no
   blank or missing-state errors.

---

### User Story 5 - Routing Decisions Are Explainable (Priority: P2)

As a user, I want to see why a message got light or full treatment, so AI
behavior stays transparent.

**Why this priority**: Transparency is a non-negotiable constitution principle
(AI is Assistive, not Magical).

**Independent Test**: Inspect the stored record for any message and confirm it
names the agents that ran, the agents skipped with a reason, and whether an AI
call was used.

**Acceptance Scenarios**:

1. **Given** any processed message, **When** its stored record is inspected,
   **Then** a routing record names the agents run, the agents skipped, and the
   reason.
2. **Given** a message with a failed agent, **When** its stored record is
   inspected, **Then** the failure is distinguishable from a deliberate skip.

### Edge Cases

- **Empty or whitespace-only content**: Stored with no AI analysis; the
  routing record explains why.
- **Media-only message (image, audio, document)**: Same as empty content —
  stored, not analyzed, never dropped.
- **Trivial one-liner** ("ok", "yes", "thanks"): Minimal routing — priority
  plus summary only, no tasks or deadline, honest fallback recommendation.
- **Time expression but no action** ("The meeting is tomorrow"): No task is
  invented; the deadline stays empty when nothing is owed to the recipient.
- **Action request but no deadline** ("Call me"): Task extraction runs, no
  deadline.
- **Unfamiliar or mixed language (e.g., Arabic)**: Keyword routing is
  unreliable → default to full analysis rather than risk skipping needed work.
- **Ambiguous content**: Default to full analysis (fail toward completeness).
- **AI analysis failure at runtime**: Selected agents store their documented
  fallback values; the routing record marks the failure — the message still
  appears on the Dashboard.
- **Duplicate delivery of an already-routed message**: Caught before the
  Orchestrator by existing deduplication; the Orchestrator does not re-run.
- **Very long message**: Routed normally; trigger detection is not defeated by
  length.
- **Out-of-scope channel message**: Follows existing ingestion rules (stored
  or ignored per Day 23), never analyzed as a special case.
- **Contradictory signals** (e.g., aggressive tone with no request): Routing
  follows objective signals only — whether a request or a time expression
  exists; tone alone never triggers tasks or urgency.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST route every incoming message through a single
  central Orchestrator before any agent runs.
- **FR-002**: System MUST decide whether a message needs AI analysis and
  MUST store messages with no analyzable content without any analysis.
- **FR-003**: System MUST select the smallest subset of agents that fully
  serves each message (Priority, Summary, Task Extraction, Deadline
  Detection, Recommended Action).
- **FR-004**: System MUST always include Priority classification in every
  analyzed message; Priority MUST never be skipped.
- **FR-005**: System MUST run Task Extraction only when the message plausibly
  requests an action.
- **FR-006**: System MUST run Deadline Detection only when a time expression
  is present.
- **FR-007**: System MUST run Recommended Action only when a next step is
  warranted and MUST use the honest fallback otherwise.
- **FR-008**: System MUST default to full analysis whenever the Orchestrator
  cannot make a confident routing decision.
- **FR-009**: System MUST save a routing record with every processed message
  naming the agents run, the agents skipped with the reason, and whether an AI
  analysis call was used; skipped and failed agents MUST be distinguishable.
- **FR-010**: System MUST produce the combined result in the same shape as
  today — priority, summary, tasks, deadline, recommended action — when the
  corresponding agents run.
- **FR-011**: System MUST NOT add AI analysis calls beyond the existing
  single-call behavior; routing MUST NOT increase the number of AI calls a
  message triggers.
- **FR-012**: System MUST persist the combined result and routing record as
  one update, and the Dashboard MUST keep reading stored results only.
- **FR-013**: System MUST NOT invoke any agent from a service, endpoint,
  webhook, or Dashboard component outside the Orchestrator.
- **FR-014**: System MUST preserve user isolation — the existing ownership
  rules apply unchanged to every routed message; routing decisions never
  cross user boundaries.
- **FR-015**: System MUST keep the simulate flow and the real WhatsApp flow
  working through the same routed path without regression.

### Key Entities

- **Message**: The normalized incoming record (existing entity) the
  Orchestrator receives — carries source, sender, content, and received
  metadata.
- **Orchestrator Routing Decision**: The new record produced per message —
  captures whether to analyze, which agents to run, the order, the trigger
  signals used, and whether an AI call was made.
- **Analysis Result**: The existing combined output (priority, summary,
  tasks, deadline, recommended action) that feeds the Dashboard — unchanged
  in shape.
- **Agent**: One of the five existing analysis capabilities (Priority,
  Summary, Task Extraction, Deadline Detection, Recommended Action), selected
  and ordered by the Orchestrator.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of incoming messages are routed through the Orchestrator —
  zero known bypass paths where an agent runs outside it.
- **SC-002**: ≥ 90% of a labeled set of 50 messages are routed to the correct
  agent subset (trivial messages get no task extraction; action messages do).
- **SC-003**: 100% of analyzed messages include a priority classification, and
  100% of processed messages carry an explainable routing record.
- **SC-004**: Adding the Orchestrator adds zero AI analysis calls — total time
  from message arrival to a stored, ready-to-render result stays at or below
  the current limit.
- **SC-005**: The Dashboard renders identically to before for all existing
  flows — cards, fields, flags, and "Why it matters" lines unchanged.
- **SC-006**: Zero invented tasks, deadlines, or recommended actions are
  produced by routing; skipped agents store documented fallbacks only.
- **SC-007**: Trivial messages produce stored results with no AI analysis call
  and still appear correctly on the Dashboard.
- **SC-008**: No regression in the simulate flow; simulated and real messages
  keep producing consistent results.

## Assumptions

- The five existing agents and the Dashboard contract are fixed; the
  Orchestrator adds selection only and does not change outputs.
- Routing is rule-based (deterministic signals); AI-powered routing is not
  required for this FYP and would only be considered if rules prove
  insufficient.
- A single combined AI analysis call remains the target for messages that need
  analysis; per-agent calls are not introduced.
- Content may be in English or Arabic; when routing keywords cannot be
  trusted, full analysis is the safe default.
- The existing deduplication (Day 23) runs before the Orchestrator, so
  duplicate deliveries do not reach it.
- Multi-user behavior and user isolation are already enforced upstream and
  remain unchanged by this feature.

## Out of Scope

- A general multi-agent framework (agent-to-agent messaging, orchestration
  runtime, agent SDKs)
- AI-driven routing decisions (rules are the default)
- Per-user routing preferences or learned routing
- Retroactively re-routing or re-analyzing already-stored messages
- Any change to agent outputs, the Dashboard, or the NEEDS ATTENTION rules
- Sending or auto-replying to messages