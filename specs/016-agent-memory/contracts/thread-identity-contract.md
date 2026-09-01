# Contract: Thread Identity Fields + Link Rule

**Feature**: 016-agent-memory | **Date**: 2026-08-29 | **Phase**: 1 (Design)

Day 25 introduces **no new HTTP endpoints**. It changes the *shape* of every
stored message (adds three server-set identity fields) and the *analysis
pipeline* behind the two existing triggers (adds bounded same-thread context
inside the existing single AI call). This document pins the identity/link
contract so the backend, tests, and any reader of stored records can rely on
it.

## 1. Endpoints Involved (all UNCHANGED in path/auth)

| Endpoint | Link resolution | Analysis scheduling |
|---|---|---|
| `POST /messages` (auth cookie) | Synchronous, before insert (`create_message`) | Orchestrator synchronously; response contains identity fields + `ai_analysis` |
| `POST /webhooks/simulate` (auth cookie) | Synchronous, before insert (`ingest_message`) | Background task → identity fields immediate, `ai_analysis` eventual |
| `POST /webhooks/whatsapp` (HMAC) | Synchronous, before insert (`ingest_message`) | Background task → identity fields immediate, `ai_analysis` eventual |
| `GET /messages*` | Read only | `MessageResponse` carries the three fields (additive) |

Auth, status codes, payloads, and response envelopes are exactly as authored
in `specs/014-whatsapp-webhook/contracts/webhook-api.md` and Day 18/24 —
unchanged by Day 25.

## 2. The Link Rule (the ONLY way messages are grouped)

Two messages belong to one thread iff ALL hold (evaluated at ingest, purely
deterministic):

1. **Same user** — both `user_id`.
2. **Same channel** — equal `source`.
3. **Same sender** — equal `normalize_sender(sender)` (lowercased, stripped).
4. **Close in time** — the new message arrives ≤ `LINK_WINDOW_MINUTES`
   (default 60, env-overridable) after the **thread's latest** message.

### Assignment algorithm (`services/threads.py::resolve_and_stamp`)

```
candidate = messages.find_one({
  user_id, source, sender: normalized, state: "active",
  received_at: { >= new.received_at - window }
}, sort: { received_at: -1 })

none                  -> (threadId=None, conversationId=None)      # stands alone
candidate.threadId    -> inherit (candidate.threadId, candidate.threadId)
else (anchor)         -> threadId = str(candidate._id)
                        stamp candidate {threadId, conversationId}  # guarded update
                        return (threadId, threadId)
```

Invariants:

- `threadId` is NEVER minted for a lone message; it is born on the second
  in-window message and equals the anchor's `_id`.
- The window is measured from the thread's latest message, so a chain
  A→B→C stays linked when B→C is in-window even if A→C is not.
- `conversationId` is ALWAYS equal to `threadId` when a thread exists and is
  never set otherwise. It is reserved for future user-defined conversations;
  no other value is invented at Day 25.
- Parallel strands from one sender resolve to the latest consecutive arrival;
  ambiguity never becomes a wrong link on a different constraint (the query
  enforces user+source+sender+window, so it is provably conservative).

## 3. Identity Field Contract (stored + API)

Server-set only — the backend computes and stores these; payloads from the
client are ignored (the ingest functions never read them).

| Field | Storage | API (`MessageResponse`) | Always present? |
|---|---|---|---|
| `messageId` | `str(_id)` at ingest | `messageId` | Yes |
| `threadId` | link result | `threadId` (nullable) | Only when linked |
| `conversationId` | = `threadId` when set | `conversationId` (nullable) | Only when a thread exists |

Isolation: every link query, anchor stamp, context fetch, and update is
`user_id`-scoped. A thread contains only one user's messages, and each message
remains individually owned, queryable, and deletable. `state: "active"` is
honored so deleted messages are never link candidates.

## 4. Behavior Guarantees

- Standalone messages are stored and analyzed **byte-identical** to Day 24
  (`threadId`/`conversationId` null, no context, zero added LLM calls).
- Trivial/no-content messages still take the Day 24 zero-LLM path; they may
  still receive identity fields (the link is data, not behavior).
- Link resolution failure/timeout never blocks ingestion: the message is
  stored and analyzed standalone.
- Duplicate `external_message_id` deliveries keep returning the existing id
  and never re-run linking or analysis.
- No memory framework: zero vector-store/embedding/RAG artifacts (verified by
  code-level grep — SC-008).