# Implementation Plan: Day 18 – User Isolation

**Branch**: `009-user-isolation` | **Date**: 2026-08-25 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/009-user-isolation/spec.md`

## Summary

Enforce strict per-user data isolation across all collections. The
primary fix is passing `user_id` through the AI analyzer to task
documents. Secondary work: add MongoDB indexes, write comprehensive
isolation tests, verify all endpoints return 404 for cross-user access.

## Technical Context

**Language/Version**: Python 3.13, TypeScript 5 (Next.js 16)
**Primary Dependencies**: FastAPI, Motor (async MongoDB), Next.js 16
**Storage**: MongoDB (communication_ai database)
**Testing**: pytest (backend), vitest (frontend)
**Target Platform**: Web (localhost:3000 frontend, localhost:8000 backend)
**Project Type**: Web application (monorepo)
**Performance Goals**: No new performance targets; existing indexes suffice
**Constraints**: No breaking API changes; all changes are internal
**Scale/Scope**: Single-user FYP demo; isolation is a security invariant

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| Simplicity First | ✅ PASS | One parameter change + index addition + tests |
| Vertical Slices | ✅ PASS | Isolation is a cross-cutting concern, not a new feature |
| AI is Assistive | ✅ PASS | No AI behavior changes; only task storage |
| User Control | ✅ PASS | Users retain full control over their data |
| Security & Privacy | ✅ PASS | This feature IS the security invariant |
| Clean Code | ✅ PASS | Follows existing patterns |
| Progressive Enhancement | ✅ PASS | No new dependencies |

**Gate result**: ALL PASS. No violations.

## Project Structure

### Documentation (this feature)

```text
specs/009-user-isolation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── api.md
└── tasks.md             # Phase 2 output (NOT created by /sp.plan)
```

### Source Code (repository root)

```text
backend/
├── main.py                          # Add index creation in lifespan
├── database.py                      # No changes (collections already defined)
├── services/ai/analyzer.py          # Add user_id parameter + task docs
├── routes/messages.py               # Pass user_id to analyze_message()
├── routes/webhooks.py               # Pass user_id to analyze_message()
└── tests/
    ├── test_auth.py                 # Existing tests (unchanged)
    └── test_user_isolation.py       # NEW: comprehensive isolation tests
```

**Structure Decision**: Web application layout (Option 2). Changes are
limited to backend files. No frontend changes required — the frontend
already reads from authenticated endpoints.

## Implementation Steps

### Step 1: Fix AI Analyzer — Pass user_id to Tasks

**File**: `backend/services/ai/analyzer.py`

Change the `analyze_message()` function signature to accept `user_id`:

```python
async def analyze_message(
    message_content: str,
    message_id: str = None,
    user_id: str = None,
) -> dict:
```

In the task document creation block (lines 56–71), add `"user_id": user_id`
to every task doc. If `user_id` is `None`, log a warning and skip task
creation:

```python
if message_id and result.tasks_extracted:
    if not user_id:
        logger.warning(
            "Skipping task creation for message %s: no user_id provided",
            message_id,
        )
    else:
        preview = message_content[:80] + ("..." if len(message_content) > 80 else "")
        task_docs = []
        for task in result.tasks_extracted:
            task_docs.append({
                "user_id": user_id,  # <-- ADD THIS
                "description": task["description"],
                # ... rest unchanged
            })
        if task_docs:
            await tasks_collection.insert_many(task_docs)
```

### Step 2: Update Route Handlers to Pass user_id

**File**: `backend/routes/messages.py`

In `create_message()` (line 33), pass `user_id`:

```python
ai_analysis = await analyze_message(
    payload.content,
    message_id=str(result.inserted_id),
    user_id=str(current_user["_id"]),
)
```

**File**: `backend/routes/webhooks.py`

In `whatsapp_webhook()` (line 63), pass `user_id`:

```python
ai_analysis = await analyze_message(
    payload.message,
    message_id=message_id,
    user_id=uid,
)
```

### Step 3: Add MongoDB Indexes

**File**: `backend/main.py`

In the `lifespan()` function, add index creation after the existing
`users.email` unique index:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    await users_collection.create_index("email", unique=True)
    await messages_collection.create_index([("user_id", 1), ("created_at", -1)])
    await tasks_collection.create_index([("user_id", 1), ("created_at", -1)])
    yield
```

### Step 4: Write Comprehensive Isolation Tests

**File**: `backend/tests/test_user_isolation.py` (NEW)

Create a `TestUserIsolation` class that:

1. Registers two users (A and B) with different credentials
2. Creates messages for each user via `POST /messages`
3. Creates tasks for each user by sending messages with actionable content
4. Tests every endpoint with both users' sessions:

| Endpoint | User A session | User B session |
|---|---|---|
| `GET /messages` | Returns A's messages only | Returns B's messages only |
| `GET /messages/{A_id}` | Returns A's message | Returns 404 |
| `PUT /messages/{A_id}` | Updates A's message | Returns 404 |
| `DELETE /messages/{A_id}` | Deletes A's message | Returns 404 |
| `PUT /messages/{A_id}/priority` | Updates A's priority | Returns 404 |
| `GET /tasks` | Returns A's tasks only | Returns B's tasks only |
| `PUT /tasks/{A_task_id}` | Updates A's task | Returns 404 |
| `DELETE /tasks/{A_task_id}` | Deletes A's task | Returns 404 |

5. Verifies that AI analysis data (priority, summary, recommendation) is
   never visible in cross-user responses
6. Verifies that task documents have `user_id` set correctly

### Step 5: Run All Tests and Fix Issues

```bash
cd backend
python -m pytest tests/ -v
```

All 27 existing tests + new isolation tests must pass.

## Complexity Tracking

> No violations. All changes are simple and follow existing patterns.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| N/A | N/A | N/A |

## Definition of Done

- [ ] `analyze_message()` accepts and uses `user_id` parameter
- [ ] Every task document created by the analyzer has `user_id`
- [ ] All route handlers pass `user_id` to `analyze_message()`
- [ ] MongoDB indexes exist on `messages.user_id` and `tasks.user_id`
- [ ] Two-user isolation test passes for all endpoints
- [ ] Cross-user resource access returns 404 (not 403)
- [ ] All 27 existing tests continue to pass
- [ ] No `user_id`-less task documents can be created through any code path
