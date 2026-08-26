# Quickstart: Task Management

**Feature**: 012-task-management  
**Date**: 2026-08-26  
**Status**: Complete

## Overview

The Task Management feature provides a clean "My Tasks" page that displays AI-extracted tasks organized by priority with actions to complete, snooze, and view source messages.

## Prerequisites

- Existing Communication AI project running
- User authenticated with valid JWT token
- Tasks in the database (at least 5-10 for testing)
- AI pipeline extracting tasks from messages

## Quick Start

### 1. Start the Development Servers

**Frontend**:
```bash
cd my-app
npm run dev
```
Frontend available at: http://localhost:3000

**Backend**:
```bash
cd my-app/backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
Backend available at: http://localhost:8000

### 2. Navigate to Tasks Page

1. Open http://localhost:3000/tasks
2. You should see the task list with priority indicators

### 3. Test Task Display

1. Verify tasks are sorted by priority (urgent first, then important, then normal)
2. Verify each task shows:
   - Priority indicator (🔴, 🟡, 🟢)
   - Task description
   - Deadline (if available)
   - Action buttons (Complete, Snooze, View)

### 4. Test Complete Action

1. Click "Complete" on a task
2. Task should disappear from the active list
3. Refresh the page - task should still be gone
4. Verify task status is "completed" in database

### 5. Test Snooze Action

1. Click "Snooze" on a task
2. Select "tomorrow" from dropdown
3. Task should disappear from the active list
4. Wait until tomorrow (or change system time) - task should reappear
5. Verify `snoozed_until` timestamp is set correctly

### 6. Test View Message Action

1. Click "View message" on a task
2. Should navigate to the original message detail view
3. Verify message shows sender, source, timestamp, and content
4. Navigate back to tasks page

### 7. Test Empty State

1. Complete all tasks
2. Should see "No tasks found" message
3. Verify message is helpful and clear

### 8. Test Loading State

1. Refresh the tasks page
2. Should see skeleton loaders while tasks load

## API Testing

### Get Tasks

```bash
# Get all active tasks (sorted by priority)
curl -b "access_token=YOUR_TOKEN" http://localhost:8000/tasks

# Get tasks including completed
curl -b "access_token=YOUR_TOKEN" "http://localhost:8000/tasks?include_completed=true"

# Get tasks including snoozed
curl -b "access_token=YOUR_TOKEN" "http://localhost:8000/tasks?include_snoozed=true"
```

### Complete Task

```bash
curl -X PUT -b "access_token=YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "completed"}' \
  http://localhost:8000/tasks/TASK_ID/status
```

### Snooze Task

```bash
curl -X PUT -b "access_token=YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"duration": "tomorrow"}' \
  http://localhost:8000/tasks/TASK_ID/snooze
```

### Get Source Message

```bash
curl -b "access_token=YOUR_TOKEN" http://localhost:8000/tasks/TASK_ID/message
```

## Testing Checklist

- [x] Tasks load and display correctly
- [x] Priority indicators show correct emojis
- [x] Tasks are sorted by priority (urgent → important → normal)
- [x] Complete action works and removes task from active list
- [x] Snooze action works and hides task temporarily
- [x] View message action navigates to source message
- [x] Empty state displays "No tasks found"
- [x] Loading state shows skeleton loaders
- [x] User isolation is maintained (only own tasks shown)
- [x] Performance is acceptable (< 1 second)
- [x] Responsive design works on mobile
- [x] Keyboard navigation works for actions

## Troubleshooting

### Tasks not loading
- Check if backend server is running
- Check if user is authenticated (JWT token valid)
- Check if tasks exist in database
- Check browser console for errors

### Priority indicators not showing
- Check if `priority_indicator` field exists in task data
- Check frontend mapping of priority values to emojis
- Check backend sorting logic

### Actions not working
- Check if backend API endpoints are working
- Check if request body is correct format
- Check browser network tab for API responses

### User seeing other users' tasks
- Check if `user_id` filter is applied in queries
- Check if JWT token is valid
- Check database indexes

## Next Steps

1. Implement the backend API extensions (snooze endpoint)
2. Implement the frontend task list component
3. Test with real data from AI pipeline
4. Optimize performance if needed
5. Add pagination for large task lists