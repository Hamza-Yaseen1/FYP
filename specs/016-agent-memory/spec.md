# Feature Specification: Agent Memory / Context (Day 25)

**Feature Branch**: `016-agent-memory`  
**Created**: 2026-08-29  
**Status**: Draft  
**Input**: User description: "Create a clear and focused specification for Day 25 – Agent Memory / Context"

## Feature Overview

Day 25 gives the system lightweight **context between related messages**. Today
every message is analyzed in isolation: the AI sees one message and nothing
around it. This feature lets the system recognize that two messages belong to
the same exchange and use that context when analyzing each of them.

```text
Message 1: "Can you send the report?"        ← task, no deadline
Message 2: "Need it before our meeting."     ← deadline context
```

Together, these two messages tell a complete story: the report task carries a
deadline. The system links them, remembers they are one thread, and — when
analyzing the second message — can conclude that the "meeting" deadline applies
to the report task in the first message.

This is deliberately **lightweight memory, not a memory system**. The solution
is a simple, deterministic link between messages plus a context note passed into
the existing AI analysis. It does not build a vector store, embeddings, a
conversation history database, or any long-term learning.

**Goal**: Messages are no longer always analyzed alone. When two or more messages
clearly belong together, the system links them and uses the linked context to
improve analysis — without changing the existing AI pipeline or the Dashboard.

**Out of scope**: a persistent conversation memory or retrieval system (RAG,
vector search, embeddings), AI-invented grouping, cross-user grouping, and any
change to how the Dashboard renders results.

## Purpose of Memory/Context

The AI should not always judge a message in isolation. Real conversations carry
meaning across messages: a follow-up message often reveals the deadline, tone,
or intent of an earlier message.

```text
Isolated today:
  "Can you send the report?"        → task, unknown deadline, normal priority
  "Need it before our meeting."     → friendly FYI, nothing actionable

With context:
  "Can you send the report?"        → task
  "Need it before our meeting."     → adds "before the meeting" deadline
  Combined                        → report task is due before the meeting
```

It exists for three reasons:

1. **Correctness** — a follow-up message often carries the details that make an
   earlier message actionable (deadline, urgency, scope). Judging each alone
   loses that.
2. **Clarity** — related messages stay connected (same thread), so the inbox and
   task list reflect how the user actually converses.
3. **Simplicity** — context is added with a deterministic link plus a bounded
   note. No memory framework, no extra model calls, no new infrastructure.

**Success means**: When two messages clearly belong to one exchange, the system
links them and a later message's missing-context clues improve the earlier
message's analysis — visibly, explainably, and without ever guessing.

## How Messages Are Linked

Linking is **deterministic and conservative**. The system links two messages
into one thread ONLY when the evidence is clear — it never guesses.

**The link rule**: two messages belong to the same thread when ALL of these
hold:

1. **Same user** — both messages belong to the currently authenticated user.
2. **Same channel** (`source`) — both arrived through the same channel
   (e.g., both WhatsApp, both Gmail).
3. **Same sender** — the sender identity matches (normalized the same way as
   existing inbox sender filtering).
4. **Close in time** — the new message arrives within a bounded window (default
   ≤ 60 minutes) of the latest message already in that thread.

When a new message satisfies the rule against an existing thread, it inherits
that thread's ID. Otherwise the message stands alone (`threadId` and
`conversationId` are empty/null) and is analyzed exactly as today.

The link is established at ingest time, before analysis, using data already
available — it requires no model call and no additional AI decision.

## Data Fields to Store

Every message document already stores its own identity. Day 25 adds **two
optional grouping fields** plus a guaranteed `messageId`:

| Field | Meaning | Always present? |
|---|---|---|
| `messageId` | The message's own unique identifier (existing message ID) | Yes — every message |
| `threadId` | Groups messages in one exchange (the two messages in the example share one `threadId`) | Only for linked messages |
| `conversationId` | Broad, persistent grouping of related threads — set equal to `threadId` for now | Only when a thread exists |

Rules for these fields:

- **Set server-side only.** All three are assigned by the backend at ingest
  time. They are never supplied or trusted from the client.
- **Never invented.** `threadId` exists only when the deterministic link rule
  matches. `conversationId` is never guessed; for this feature it mirrors the
  `threadId` and stays empty otherwise.
- **Scoped to one user.** A thread may combine only that user's own messages.
  Linking across users is forbidden.
- **Optional by design.** A message with no link behaves exactly as it does
  today — no new behavior, no new cost.

## How Context Will Be Used During AI Analysis

When a message belongs to a thread, the system can give the AI **bounded
context** from that thread during analysis.

1. **Fetch the thread.** Up to the 5 most recent messages in the same thread
   (same user only) are gathered at analysis time.
2. **Pass it into the existing single AI call.** The context is included inside
   the analysis prompt for the current message — it does NOT add a new model
   call, a new agent, or a new round-trip.
3. **Use it to refine, never to invent.** The AI may use the linked messages to
   detect context — e.g., a deadline, urgency, or clarification — that applies
   to the current (or the earlier) message.
4. **Record the effect.** If context changed something (e.g., added a deadline
   to the earlier message's task), that update is saved WITH an explanation
   naming the linked message(s), so the user can see why the analysis changed.
5. **User-stated facts win.** If a user explicitly states something, AI-inferred
   context never overrides it.

The Dashboard and the existing pipeline stay unchanged: they keep reading
stored results only. Context is one more input to analysis — it never turns
into a new rendering path.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A Follow-Up Message Completes an Earlier Task (Priority: P1)

As a user, I want two related messages to be treated as one exchange, so that
a follow-up message ("Need it before our meeting.") adds the missing deadline
to the task from the earlier message ("Can you send the report?").

**Why this priority**: This is the entire point of the feature — analyzing
messages with the context that makes them actionable.

**Independent Test**: Send two related messages (task + follow-up deadline).
Confirm the stored record links them (same `threadId`) and the earlier
message's analysis now reflects the deadline, with an explanation naming the
follow-up message.

**Acceptance Scenarios**:

1. **Given** a message that extracts a task with no deadline ("Can you send
   the report?"), and a second, same-sender, same-channel, in-window message
   ("Need it before our meeting."), **When** the second message is processed,
   **Then** both messages are marked with the same `threadId`, and the earlier
   task gains the deadline context with an explanation naming the follow-up
   message.
2. **Given** a linked pair, **When** the user views the applicable Dashboard
   cards, **Then** both messages still render as their own cards, with the
   enriched information clearly shown — no duplicate cards, no merged cards.

---

### User Story 2 - Unrelated Messages Stay Independent (Priority: P1)

As a user, I want unrelated messages to stay separate, so the system never
wrongly combines different conversations and never invents links.

**Why this priority**: False links are false claims about the user's
conversations. Precision matters more than recall.

**Independent Test**: Send messages from different senders, different
channels, or far apart in time, and confirm each keeps its own (unset) thread
identity and is analyzed exactly as today.

**Acceptance Scenarios**:

1. **Given** two messages from different senders, **When** both are processed,
   **Then** they do NOT share a `threadId` and each is analyzed independently.
2. **Given** two messages from the same sender but more than the time window
   apart, **When** both are processed, **Then** they do NOT share a
   `threadId`.

---

### User Story 3 - Existing Pipeline and Dashboard Keep Working (Priority: P1)

As a user, I want the Dashboard, tasks, inbox, and AI pipeline to behave
exactly as they do today when no context applies.

**Why this priority**: A backward-incompatible change would break a working
FYP. Compatibility is non-negotiable.

**Independent Test**: Run the existing simulated workflows (single messages,
with and without tasks/deadlines) and confirm the stored results and rendered
cards are identical to today.

**Acceptance Scenarios**:

1. **Given** any single, standalone message, **When** it is processed, **Then**
   its stored analysis and Dashboard card are identical to the current
   behavior — no new fields are required, no field is missing.
2. **Given** the existing Dashboard, **When** any message (linked or not) is
   displayed, **Then** rendering reads stored results only and shows no
   blank, "null", or empty states.

---

### User Story 4 - Context Is Explainable and Dismissible (Priority: P2)

As a user, I want to know when and why the AI used another message, so I can
trust — or reject — the enriched analysis.

**Why this priority**: Transparency is a constitution principle (AI is
Assistive, not Magical).

**Independent Test**: Trigger a linked pair, then inspect the earlier message's
stored record for an explanation stating which message(s) the context came
from.

**Acceptance Scenarios**:

1. **Given** a message whose analysis was affected by a linked message, **When**
   its record is inspected, **Then** an explanation names the linked message(s)
   used.
2. **Given** an enriched task card, **When** the user reviews it, **Then** the
   user can see the reason and the original wording is never silently
   overwritten.

---

### User Story 5 - Only My Messages Are Considered (Priority: P1)

As a user, I want threads to contain only my own messages, so my data never
mixes with another user's — even in the same channel.

**Why this priority**: User isolation is a hard security invariant in this
project.

**Independent Test**: Simulate the same channel with two users sending
messages; confirm each user's thread contains only their own messages.

**Acceptance Scenarios**:

1. **Given** two users messaging on the same channel, **When** messages are
   linked, **Then** a thread is created only within each user's own message
   set — never across users.

### Edge Cases

- **Two messages, different senders**: Never linked — analyzed independently.
- **Two messages, same sender, over 60 minutes apart**: Not linked by default —
  the time window fails.
- **Two messages, same sender, different channels** (WhatsApp then Gmail):
  Never linked — the channel must match.
- **First message of a conversation**: No thread exists — stored and analyzed
  standalone, exactly as today.
- **Follow-up intended to reference an old message beyond the window**: Not
  linked; analysis stays isolated (safe default — no guessed connection).
- **Media-only or empty messages in a thread**: Stored and shown as today;
  they do not inject fake context.
- **Context changes a deadline**: The change is stored as a NEW, explainable
  analysis revision. Original wording is preserved; nothing is silently
  overwritten.
- **Context conflicts with an explicit user-stated fact** (user says "by
  Friday", context suggests "tonight"): The explicit statement wins.
- **Very long thread**: Context is capped at the 5 most recent messages; older
  history does not crowd the prompt.
- **Link resolution fails or times out**: The message is stored and analyzed
  standalone — ingestion never blocks on linking.
- **Same user, two active threads with one sender** (parallel conversations):
  The time window and consecutive-arrival rule decide; ambiguous cases default
  to no link rather than a wrong link.
- **AI analysis failure inside a linked message**: Existing fallbacks apply;
  the link metadata is unaffected.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every message MUST carry a `messageId` assigned server-side
  (its own unique identifier).
- **FR-002**: System MUST attempt to link each new message to an existing
  thread when — and only when — the deterministic rule holds: same user, same
  channel, same sender, and arrival within the link window (≤ 60 minutes) of
  the thread's latest message.
- **FR-003**: System MUST store a `threadId` on linked messages and MUST leave
  `threadId` unset on messages with no matching thread.
- **FR-004**: System MUST store a `conversationId` equal to the `threadId`
  when a thread exists and MUST NOT invent `conversationId` values otherwise.
- **FR-005**: System MUST set all three identity fields server-side at ingest
  and MUST NOT accept them from the client.
- **FR-006**: System MUST scope all linking strictly to the authenticated
  user's own messages; a thread MUST NEVER span users.
- **FR-007**: When analyzing a message that belongs to a thread, the system
  MUST provide at most the 5 most recent same-user messages from that thread
  as context inside the existing single AI analysis call.
- **FR-008**: Context MUST NOT add new AI calls or new agents — the existing
  single-analysis-call behavior is preserved.
- **FR-009**: If context alters an earlier message's analysis (e.g., adds a
  deadline), the system MUST store the update with an explanation naming the
  linked message(s); the original wording MUST be preserved.
- **FR-010**: An explicitly stated user fact (stated deadline, stated
  preference) MUST take precedence over any inferred context.
- **FR-011**: Standalone messages (no link) MUST be stored and analyzed exactly
  as they are today, with no behavior or cost change.
- **FR-012**: Link resolution failure or timeout MUST NOT block message
  ingestion or analysis — the message is handled standalone.
- **FR-013**: The AI pipeline and Dashboard MUST keep reading stored results
  only; linking MUST NOT add a rendering path or change card output.
- **FR-014**: System MUST enforce user isolation for all linked messages —
  they remain individually owned, individually queryable, and individually
  deletable by their user.
- **FR-015**: System MUST NOT build or use a persistent memory framework —
  no vector store, no embeddings, no RAG, no long-term conversation database.

### Key Entities

- **Message**: The existing normalized incoming record (owned by one user),
  now carrying `messageId`, optional `threadId`, and optional
  `conversationId` — identity only, no behavioral change when unset.
- **Thread**: A lightweight grouping of a user's related messages (same
  channel, sender, time window) sharing one `threadId`; it holds no AI state
  of its own.
- **Conversation**: The broad grouping concept; for this feature it equals the
  thread and is reserved for future user-defined grouping.
- **Link rule**: The deterministic rule (user + channel + sender + window) that
  assigns `threadId`; the only way messages are grouped.
- **Context note**: The bounded (≤ 5 messages) same-thread input supplied to
  the AI analysis and the explanation recorded when context changes a result.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of messages store a server-assigned `messageId`; linked
  messages store a shared `threadId` and matching `conversationId`.
- **SC-002**: ≤ 5% of linked pairs are false links (messages from different
  senders, channels, or time windows are never grouped) — verified against a
  labeled set of 30 message pairs.
- **SC-003**: ≥ 80% of clearly-related same-sender, in-window message pairs
  are correctly grouped into one `threadId` (the same labeled set).
- **SC-004**: When a follow-up message supplies missing context, the affected
  analysis reflects it with an explanation naming the linked message — verified
  end-to-end on the report/meeting example.
- **SC-005**: Zero regression: standalone messages produce identical stored
  analysis and Dashboard cards to today; the existing single-message test set
  passes unchanged.
- **SC-006**: Linking adds zero extra AI analysis calls; total time from message
  arrival to a stored, ready-to-render result stays at or below the current
  limit.
- **SC-007**: Isolation holds for linked data — the two-user isolation test
  passes and no thread ever contains another user's messages.
- **SC-008**: No memory framework is present — a code-level check confirms no
  vector store, embedding, or retrieval components were introduced.

## Assumptions

- The link window (≤ 60 minutes) is a sensible default for a FYP; it can be
  tuned without changing the architecture.
- The context cap (5 most recent messages) keeps prompts small and avoids
  crowding older, less relevant history.
- `conversationId` mirrors `threadId` for now; user-defined conversations are a
  future extension, not part of this feature.
- Messages are available in MongoDB before analysis, so the 5-message thread
  context can be gathered at analysis time in the same flow.
- User isolation, ingestion, and the Dashboard contract are already enforced
  and remain unchanged by this feature.

## Out of Scope

- A persistent memory / retrieval system (vector store, embeddings, RAG, or a
  dedicated conversation-history database)
- AI-based or learned grouping of messages (linking is deterministic only)
- User-defined conversation grouping or renaming (reserved for later)
- Retroactive linking or re-analysis of already-stored history beyond the
  deterministic ingest-time rule
- Any change to the AI pipeline's single-call behavior, agent outputs, the
  NEEDS ATTENTION rules, or the Dashboard rendering
- Cross-user grouping of any kind