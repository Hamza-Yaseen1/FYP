# Research: Day 18 – User Isolation

**Date**: 2026-08-25
**Feature**: 009-user-isolation

## Decision 1: Task user_id Assignment Strategy

**Decision**: Pass `user_id` as a parameter to `analyze_message()` and embed
it in every task document created by the AI analyzer.

**Rationale**: The analyzer currently creates tasks via
`tasks_collection.insert_many()` without a `user_id`. The message document
already contains `user_id` at the time the analyzer runs (it was set by the
route handler at message creation). Passing `user_id` through the function
signature is the simplest, most explicit approach — no database lookups
needed.

**Alternatives considered**:
- Lookup message by `message_id` inside analyzer to get `user_id`: adds an
  unnecessary database query and couples the analyzer to the messages
  collection schema.
- Store `user_id` on the message AFTER analysis: breaks the invariant that
  every document has `user_id` at creation time.

## Decision 2: Index Strategy

**Decision**: Add compound indexes `{"user_id": 1, "created_at": -1}` on both
`messages` and `tasks` collections.

**Rationale**: Every query filters on `user_id` and sorts on `created_at`.
A compound index supports both operations efficiently. Creating these indexes
in the app lifespan ensures they exist without a separate migration step.

**Alternatives considered**:
- Single index on `user_id` only: works for filtering but requires in-memory
  sort on `created_at`.
- No indexes: works at small scale but degrades as data grows. The
  constitution requires efficient per-user queries.

## Decision 3: Analyzer Error Handling for Missing user_id

**Decision**: If `user_id` is not provided to `analyze_message()`, log a
warning and skip task creation. Return the analysis dict without tasks.

**Rationale**: The constitution requires that tasks MUST NOT be created
without a `user_id`. Skipping task creation is the safest fallback. The
analysis (priority, summary, recommendation) is still stored on the message
— only task extraction is skipped.

**Alternatives considered**:
- Raise an exception: would break the message creation flow and prevent the
  message from being stored at all.
- Default to a system user_id: violates the isolation invariant.

## Decision 4: Test Strategy

**Decision**: Write a dedicated `test_user_isolation.py` test file with a
`TestUserIsolation` class that registers two users, creates messages and
tasks for each, and verifies complete separation through every API endpoint.

**Rationale**: The existing `TestIsolation` class in `test_auth.py` covers
basic message/task isolation but does not test every endpoint comprehensively.
A dedicated isolation test file provides clear, focused coverage.

**Alternatives considered**:
- Extend existing tests: would make `test_auth.py` even longer and harder
  to maintain.
- Unit tests only: insufficient for verifying end-to-end isolation.
