# Data Model: Identity Fields + `context_updates` Revisions

**Feature**: 016-agent-memory | **Date**: 2026-08-29 | **Phase**: 1

## 1. Scope

Day 25 adds **three additive identity fields** (`messageId`, `threadId`,
`conversationId`) to every `messages` document and an **additive
`ai_analysis.context_updates` array** on messages that were enriched by later
thread context. No collection is changed/renamed/migrated; the Day 18 + Day
23 message shape (incl. `ai_analysis.routing` from Day 24) is otherwise
untouched. SIMULATE / web / legacy documents remain valid.

## 2. Message Document (MongoDB `messages`)

```json
{
  "_id": "ObjectId(66e1a2b3c4d5e6f7a8b9c0d1)",
  "user_id": "ObjectId(507f1f77bcf86cd799439011)",
  "source": "whatsapp | gmail | web",
  "sender": "ali",
  "content": "Need it before our meeting.",
  "message_type": "text",
  "status": "unread",
  "state": "active",
  "received_at": "2026-08-29T12:00:00Z",
  "created_at": "2026-08-29T12:00:00Z",
  "updated_at": "2026-08-29T12:00:00Z",

  "messageId": "66e1a2b3c4d5e6f7a8b9c0d1",
  "threadId": "66e1a2b3c4d5e6f7a8b9c0d1",
  "conversationId": "66e1a2b3c4d5e6f7a8b9c0d1",

  "ai_analysis": {
    "priority": "urgent",
    "confidence": 0.9,
    "explanation": "1-2 sentences",
    "summary": "one sentence",
    "recommended_action": "…",
    "recommended_actions": [],
    "tasks_extracted": [],
    "deadlines": ["before the meeting"],
    "needs_attention": true,
    "attention_reason": "…",
    "provider": "groq",
    "analyzed_at": "2026-08-29T12:00:01Z",
    "status": "completed",
    "routing": { "agents_run": ["priority"], "llm_call_used": true, "…": "…" },

    "context_updates": [
      {
        "field": "deadline",
        "value": "before the meeting",
        "source_message_id": "a9b2c3d4e5f6a7b8c9d0e1f2",
        "reason": "Deadline supplied by the follow-up message from the same sender.",
        "applied_at": "2026-08-29T12:00:02Z"
      }
    ]
  }
}
```

### Field notes

- **`messageId`** — always `str(doc["_id"])`; stored literally so the
  constitution compliance check is greppable and `MessageResponse` can echo
  it verbatim.
- **`threadId`** — present ONLY when the deterministic link rule matched.
  Value = `str(anchor["_id"])` (the first message of the thread). A lone
  message never gets one (no speculation). Hosted on `user_id`-scoped
  queries only.
- **`conversationId`** — set equal to `threadId` whenever a thread exists;
  never invented, never present otherwise.
- **`ai_analysis.context_updates`** — additive revision array on the
  **earlier** message when a later linked message supplied missing context.
  Original `ai_analysis` fields are never modified by enrichment — the update
  is a new, explainable revision (constitution: original wording preserved).
  `reason` MUST name the `source_message_id`. Omitting this key = no
  enrichment; the Dashboard renders stored results identically with or
  without it.

## 3. Example States

### Standalone message (first message, or no in-window match)

```json
{ "_id": "…(x1)", "user_id": "…", "source": "whatsapp", "sender": "ali",
  "messageId": "x1", "threadId": null, "conversationId": null }
```

Behavior: analyzed exactly as today; no context block; zero added cost.

### Linked pair (anchor + follow-up)

```text
M1 (anchor): _id=abc, sender=ali, source=whatsapp, received 12:00
  → threadId/conversationId stamped to "abc" when M2 arrives
M2 (follow-up): _id=def, sender=ali, source=whatsapp, received 12:30
  → messageId=def, threadId="abc", conversationId="abc"
```

Analysis of M2 may fetch M1 as context; if the model (validated) reports a
deadline for M1, M1 gains:

```json
"ai_analysis": { "…existing…",
  "context_updates": [{ "field": "deadline", "value": "before the meeting",
                        "source_message_id": "def", "reason": "…", "applied_at": "…" }] }
```

## 4. Indexes (created in `backend/main.py` lifespan)

| Index | Purpose |
|---|---|
| `{user_id: 1, conversationId: 1, received_at: -1}` | Link resolution + conversation display, per user |
| `{user_id: 1, threadId: 1, received_at: -1}` | Thread-anchor lookup + context fetch, per user |

Notes: the constitution writes these index keys as `receivedAt`; the realized
backing field is the existing `received_at` (research §3.3). Indexes are
per-user first, so no query can cross a user boundary. Existing indexes are
unchanged.

## 5. API Response Mapping (`MessageResponse`)

```json
"id": "…", "messageId": "…", "threadId": "…|null", "conversationId": "…|null"
```

- `message_doc_to_response` maps `messageId` from `doc.get("messageId",
  str(doc["_id"]))`; `threadId`/`conversationId` from `doc.get`.
- `ai_analysis` is validated `AIAnalysis(**doc)` — `context_updates` is not a
  declared `AIAnalysis` field (Day 24's lesson: Pydantic 2 drops undeclared
  keys), so the current message's stored analysis never carries it; it
  travels as a sibling write to the anchor. If a future UI needs it, declare
  `ContextUpdate` on `AIAnalysis` additively then.

## 6. Modeling Rules (behavioral contract)

| Condition | `messageId` | `threadId` | `conversationId` | Context to AI |
|---|---|---|---|---|
| Any message | always `_id` | — | — | — |
| No in-window match | set | null | null | none |
| Follow-up in window (anchor exists, no threadId) | set | anchor `_id` | anchor `_id` | ≤5 recent |
| Follow-up in window (thread exists) | set | inherited | inherited | ≤5 recent |
| Trivial / no-content (Day 24) | set | (per rule) | (per rule) | never fetched |
| Duplicate `external_message_id` delivery | existing id returned | — | — | pipeline NOT re-run |

Writes that touch a thread/context are ALWAYS filtered by `user_id`; a thread
or a context revision can never span users (Day 18).