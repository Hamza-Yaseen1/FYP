# Data Model: Security & Reliability Verification (Day 29)

**Feature**: `020-security-testing` | **Date**: 2026-09-11

Day 29 adds **no new collections, fields, or documents**. This file states the
ownership, dedupe-key, and analysis-state model the verification suites assert
against, plus the one schema-touching change (an index).

## 1. Ownership model (unchanged, verified)

| Entity (collection) | Ownership field | Set by | Filtered by | Cross-user result |
|---|---|---|---|---|
| User (`users`) | `_id` | System (registration) | N/A (identity) | — |
| Message (`messages`) | `user_id` | Server (JWT / server-side webhook owner) | Every query (first condition) | 404 identical to not-found |
| Task (`tasks`) | `user_id` | Server (task extraction) | Every query | 404 identical to not-found |
| Connection (`connections`) | `user_id` | Server (JWT / OAuth callback) | Every query | 404 identical to not-found |
| Analysis (embedded in `messages.ai_analysis`) | `user_id` (inherits message) | Server (orchestrator) | Every message query | not reachable |

Invariant gate (re-asserted by new tests): every `find`, `aggregate`,
`count_documents`, `update_one`, and `delete_one` in a request path has
`user_id` as its FIRST condition.

## 2. Message identity & dedupe key

Message fields set server-side at ingest (already present):

| Field | Type | Nullable | Meaning |
|---|---|---|---|
| `messageId` | string | Never | Identity (`_id`) |
| `threadId` | string | Yes | Deterministic link (Day 25 rule) |
| `conversationId` | string | Yes | Defaults to `threadId` |
| `external_message_id` | string | Yes | **Provider idempotence key** |

### Dedupe key (CHANGED in Day 29)

- **Before**: unique index on `external_message_id` alone (partial). App recovery
  lookup unfiltered by user — could attribute another user's id on a collision.
- **After**: unique index on **`{user_id, external_message_id}`** (partial on
  `external_message_id` being a string), and the recovery lookup in
  `ingest_message` scoped to `{"user_id": user_id, ...}`.

```
Index: messages.create_index(
    [("user_id", 1), ("external_message_id", 1)],
    unique=True,
    partialFilterExpression={"external_message_id": {"$type": "string"}},
)
```

Duplicate delivery semantics (webhook redelivery, Gmail poll overlap, AI-failure
retry): the second insert raises `DuplicateKeyError` → recovery finds the user's
existing document → the response is acknowledged (200/201) with the existing id →
**no re-analysis, no new document**.

### Key-less messages (explicit exemption, documented)

- `simulate` (and manual `POST /messages`) messages carry no
  `external_message_id`. A deterministic hash can only approximate "the same
  message" and would risk falsely deduping legitimate identical sends, so these
  are **explicitly exempt** from dedupe (constitution Day 29 rule 5 allows
  exemption). Each delivery stores its own document.

## 3. Analysis state machine

`messages.ai_analysis.status`:

```
ingest (no analysis yet)  →  pending  ── retry_pending_analyses() ──▶  completed
                                     ◀── provider fails again ────────────────┘
                                                          │
                                               stays "pending" (visible),
                                               no duplicate user-visible degradation
```

- `pending` — analysis attempted but provider failed/unavailable (or analysis
  never completed); message is visible on the dashboard in the "Pending" tail.
- `completed` — analysis persisted for this message; the ONLY terminal state for
  AI-work that succeeded.
- `skipped` — orchestrator short-circuit (trivial / no-content): deterministic
  defaults, zero LLM calls (Day 24).

Retry contract (see `contracts/`): `retry_pending_analyses()` traverses
`{"ai_analysis.status": "pending"}` messages (user-scoped per document update),
re-runs `process_message` for each, and `update_one`s the SAME document —
retries must never change the document count.

## 4. Collections READ/WRITE summary for Day 29

| Collection | Day 29 operation | Notes |
|---|---|---|
| `messages` | Index change + user-scoped recovery read | Only schema-touching change |
| `users` | Read (auth verification) | unchanged |
| `tasks` | Read-only (verification fixtures) | unchanged |
| `connections` | Read-only (owner resolution / isolation tests) | unchanged |
| `ai_analysis` | Not used | stores no data for this phase |