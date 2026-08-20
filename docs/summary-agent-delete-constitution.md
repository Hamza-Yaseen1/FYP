# Summary Agent & Delete Message Constitution

**Version**: 1.0.0 | **Ratified**: 2026-08-19 | **Parent**: CONSTITUTION.md

---

## Part 1: Summary Agent

### Purpose

The Summary Agent creates short, clear summaries of incoming messages.
Its sole job is to help users quickly understand what a message is about
without reading the full content.

This agent exists because users receive many messages. By providing
concise summaries, the agent reduces reading time and helps users
decide which messages need attention.

---

### Core Principles

#### 1. Accuracy Over Completeness

The summary MUST accurately reflect the message content. The agent
MUST NOT add information that isn't present in the original message.

**Rationale**: A wrong summary is worse than no summary. Users rely
on summaries to make decisions. Inaccurate summaries erode trust.

#### 2. Conciseness

Summaries MUST be short and to the point. Target length is 1-2 sentences
or under 30 words. Remove filler words, greetings, and pleasantries.

**Rationale**: Users want the key point fast. Long summaries defeat
the purpose of having a summary.

#### 3. Preserve Action Items

If the message contains an action, request, or deadline, the summary
MUST include it. Action items are the most important part of a message.

**Rationale**: Users need to know what to do, not just what was said.

#### 4. No Invention

The agent MUST NOT invent, infer, or assume information not explicitly
stated in the message. If the message is vague, the summary should
reflect that vagueness.

**Rationale**: Hallucinated details can cause users to miss important
context or take wrong actions.

#### 5. Consistent Style

Summaries MUST follow a consistent format: subject-verb-object when
possible. Avoid starting with "This message is about..." or similar
padding phrases.

**Rationale**: Consistent style makes summaries scannable and
professional.

---

### What the Agent SHOULD Do

- Extract the main point or request from the message
- Identify and include action items, deadlines, and requests
- Remove greetings, pleasantries, and filler content
- Preserve the urgency level implied by the message
- Handle messages of any length (short or long)
- Return results quickly (within 2 seconds)

### What the Agent MUST NEVER Do

- Invent information not present in the message
- Add opinions, interpretations, or assumptions
- Change the meaning of the original message
- Include sender identity in the summary
- Auto-respond or take action based on the summary
- Store or log message content beyond the analysis
- Modify the original message content

---

### Examples

**Input**: "Hey bro, just wanted to remind you that the teacher said
we have to submit the final documentation before tomorrow's meeting."

**Output**: "Final documentation must be submitted before tomorrow's
meeting."

**Input**: "Hi team, the client meeting has been moved to 3pm Thursday.
Please update your calendars."

**Output**: "Client meeting moved to 3pm Thursday."

**Input**: "Thanks for your help yesterday! Really appreciate it."

**Output**: "Thank you message with no action required."

---

### Quality Bar

#### Accuracy Target

The agent MUST produce summaries that accurately reflect the message
content at least 85% of the time when measured against human judgment.

#### Response Time

The agent MUST return a summary within 2 seconds for messages under
1000 characters. Longer messages may take up to 5 seconds.

#### Length Target

Summaries SHOULD be under 30 words. The agent MUST NOT produce
summaries longer than 50 words.

#### Failure Behavior

If the agent fails (API error, timeout, etc.):
1. Set summary to null (not a placeholder like "Summary unavailable")
2. Set status to "pending" (not "failed")
3. Log the error for debugging
4. Never block the message from appearing on the dashboard

---

### Alignment with Parent Constitution

| Parent Principle | How Summary Agent Follows |
|------------------|---------------------------|
| Simplicity First | One-sentence summaries, no complex extraction |
| Vertical Slices | Agent works independently, returns results immediately |
| AI is Assistive | Summary is advisory, original message always available |
| User Control | User reads full message if summary is insufficient |
| Progressive Enhancement | Dashboard works without summaries, shows null |

---

## Part 2: Delete Message

### Purpose

The Delete Message feature allows users to remove messages from their
dashboard and MongoDB. This is a simple CRUD operation that gives
users control over their message list.

---

### Core Principles

#### 1. User Initiated Only

Messages MUST only be deleted by explicit user action. The system
MUST NOT auto-delete messages based on age, priority, or AI analysis.

**Rationale**: Users may need to reference old messages. Auto-deletion
could cause data loss.

#### 2. Confirmation Required

The system MUST show a confirmation dialog before deleting a message.
The dialog MUST show the message sender and a preview of content.

**Rationale**: Deletion is irreversible. Confirmation prevents
accidental data loss.

#### 3. Permanent Deletion

Deleted messages MUST be permanently removed from MongoDB. The system
MUST NOT soft-delete or archive messages unless the user explicitly
chooses that option.

**Rationale**: Users want clean inboxes. Soft deletion adds complexity
without value for a single-user system.

#### 4. No Cascade Effects

Deleting a message MUST NOT affect other messages, tasks, or system
state. The delete operation is isolated to the single message document.

**Rationale**: Simple, predictable behavior. Users should not worry
about side effects when deleting.

---

### What the Feature SHOULD Do

- Show a delete button on each message card
- Display a confirmation dialog before deletion
- Remove the message from MongoDB permanently
- Update the dashboard immediately after deletion
- Handle errors gracefully (show message if deletion fails)

### What the Feature MUST NEVER Do

- Auto-delete messages without user action
- Delete multiple messages at once (batch delete)
- Soft-delete or archive messages
- Affect other messages, tasks, or system state
- Delete messages from external channels (WhatsApp, Gmail)

---

### Quality Bar

#### Success Criteria

- User can delete any message from the dashboard
- Deleted message is permanently removed from MongoDB
- Dashboard updates immediately after deletion
- Confirmation dialog prevents accidental deletion
- Error handling shows user-friendly message on failure

#### Response Time

Delete operation MUST complete within 1 second.

#### Failure Behavior

If deletion fails:
1. Show error message to user
2. Keep the message on the dashboard
3. Log the error for debugging
4. Allow user to retry

---

### Alignment with Parent Constitution

| Parent Principle | How Delete Message Follows |
|------------------|---------------------------|
| Simplicity First | Simple delete endpoint, no soft-delete complexity |
| User Control | User initiates deletion, confirms before action |
| Security & Privacy | User can remove their own data |
| Progressive Enhancement | Dashboard works without delete (messages still show) |

---

## Combined Quality Bar

### Priority Agent + Summary Agent + Delete Message

| Feature | Accuracy | Response Time | Failure Behavior |
|---------|----------|---------------|------------------|
| Priority Agent | 80%+ | < 2 seconds | Default to NORMAL |
| Summary Agent | 85%+ | < 2 seconds | Set to null |
| Delete Message | 100% | < 1 second | Show error, keep message |

---

## Version History

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-08-19 | Initial constitution for Summary Agent and Delete Message |
