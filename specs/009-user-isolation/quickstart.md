# Quickstart: Day 18 – User Isolation

**Date**: 2026-08-25
**Feature**: 009-user-isolation

## Prerequisites

- MongoDB running on `localhost:27017`
- Python 3.13+ with dependencies from `backend/requirements.txt`
- Node.js 18+ with dependencies from `package.json`

## Step 1: Run Backend Tests

```bash
cd backend
python -m pytest tests/ -v
```

All 27 existing tests must pass. The new isolation tests will be added
by this feature.

## Step 2: Start the Backend

```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

## Step 3: Start the Frontend

```bash
npm run dev
```

## Step 4: Manual Two-User Isolation Test

### Register User A

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"User A","email":"a@test.com","password":"password123"}' \
  -c cookies_a.txt
```

### Register User B

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"User B","email":"b@test.com","password":"password123"}' \
  -c cookies_b.txt
```

### Create a Message as User A

```bash
curl -X POST http://localhost:8000/messages \
  -H "Content-Type: application/json" \
  -d '{"sender":"Alice","content":"Send the report by Friday","source":"simulated"}' \
  -b cookies_a.txt
```

### Verify User B Cannot See User A's Messages

```bash
# Should return empty array []
curl http://localhost:8000/messages -b cookies_b.txt

# Should return 404
curl http://localhost:8000/messages/<USER_A_MESSAGE_ID> -b cookies_b.txt
```

### Verify Tasks Are Isolated

```bash
# User A should see tasks extracted from their message
curl http://localhost:8000/tasks -b cookies_a.txt

# User B should see empty task list
curl http://localhost:8000/tasks -b cookies_b.txt
```

## Step 5: Run New Isolation Tests

```bash
cd backend
python -m pytest tests/test_user_isolation.py -v
```

## Definition of Done

- [ ] Every document in `messages` and `tasks` has a `user_id` field
- [ ] AI analyzer passes `user_id` to extracted tasks
- [ ] All API endpoints return only the authenticated user's data
- [ ] Cross-user resource access returns 404
- [ ] MongoDB indexes exist on `messages.user_id` and `tasks.user_id`
- [ ] Two-user isolation test passes end-to-end
- [ ] All existing tests continue to pass
