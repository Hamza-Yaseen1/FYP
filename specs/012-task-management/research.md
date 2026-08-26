# Research: Task Management

**Feature**: 012-task-management  
**Date**: 2026-08-26  
**Status**: Complete

## Research Questions

### 1. How should tasks be fetched and sorted?

**Decision**: Extend existing GET /tasks endpoint with priority-based sorting

**Rationale**: 
- Existing endpoint already returns tasks for the current user
- Need to add sorting by priority (urgent → important → normal)
- Can use MongoDB's aggregation pipeline for priority ordering
- Frontend can handle secondary sorting by deadline within each priority

**Alternatives considered**:
- Client-side sorting: Rejected because it would require fetching all tasks first, violating performance goals
- Separate endpoint for sorted tasks: Rejected because it adds unnecessary complexity

### 2. How should the Complete action work?

**Decision**: Use existing PUT /tasks/{task_id}/status endpoint with status="completed"

**Rationale**:
- Endpoint already exists and works
- Status field already supports "completed" value
- Constitution requires visual confirmation but not permanent deletion
- Task remains in database for history/audit purposes

**Alternatives considered**:
- Delete task: Rejected because constitution says "MUST NOT delete the task permanently"
- New endpoint: Rejected because existing endpoint already handles status updates

### 3. How should the Snooze action work?

**Decision**: Add new PUT /tasks/{task_id}/snooze endpoint with duration parameter

**Rationale**:
- Constitution requires snooze for defined periods (1 hour, tomorrow, next week)
- Need to update task's deadline to snoozed time
- Can reuse existing task model with deadline field
- Duration options: "1hour", "tomorrow", "nextweek"

**Alternatives considered**:
- Use existing status update: Rejected because snooze is different from status change
- Client-side snooze: Rejected because it wouldn't persist to database

### 4. How should View Message work?

**Decision**: Frontend navigation to existing message detail view

**Rationale**:
- Tasks already have `source_message_id` field
- Existing inbox/message detail page can display the message
- Can pass message ID via URL parameters
- No backend changes needed for this action

**Alternatives considered**:
- Modal/popup: Rejected because it adds UI complexity without clear benefit
- New endpoint: Rejected because message detail endpoint already exists

### 5. How should user isolation be enforced?

**Decision**: Use existing user isolation patterns from authentication system

**Rationale**:
- Existing task routes already filter by `user_id`
- `get_current_user` dependency extracts user from JWT
- All queries include `user_id` filter as first condition
- Constitution requires user isolation for tasks

**No new isolation code needed** - existing patterns are sufficient.

### 6. How should priority indicators be displayed?

**Decision**: Map priority_indicator values to emojis and colors

**Rationale**:
- Constitution specifies: 🔴 for urgent, 🟡 for important, 🟢 for normal
- AI pipeline already sets priority_indicator values
- Frontend can map values to visual indicators
- Simple conditional rendering based on priority value

**Alternatives considered**:
- Color-only indicators: Rejected because constitution specifies emojis
- Complex priority system: Rejected because it violates Simplicity First principle

### 7. How should the frontend task list be structured?

**Decision**: Build new Tasks page with task list component

**Rationale**:
- Need dedicated /tasks page (already exists as stub)
- Task list component can be reused from dashboard if available
- Add action buttons (Complete, Snooze, View) for each task
- Loading states and empty states as per constitution

**Alternatives considered**:
- Modify dashboard: Rejected because it would break existing dashboard
- Modal overlay: Rejected because it adds complexity

## Best Practices Identified

### Backend Task Sorting Pattern
```python
# Sort by priority then by deadline
pipeline = [
    {"$match": {"user_id": uid}},
    {"$addFields": {
        "priority_order": {
            "$switch": {
                "branches": [
                    {"case": {"$eq": ["$priority_indicator", "urgent"]}, "then": 1},
                    {"case": {"$eq": ["$priority_indicator", "important"]}, "then": 2},
                    {"case": {"$eq": ["$priority_indicator", "normal"]}, "then": 3}
                ],
                "default": 4
            }
        }
    }},
    {"$sort": {"priority_order": 1, "created_at": -1}}
]
```

### Frontend Priority Mapping
```typescript
const priorityConfig = {
  urgent: { emoji: '🔴', color: 'text-red-500', bgColor: 'bg-red-50' },
  important: { emoji: '🟡', color: 'text-yellow-500', bgColor: 'bg-yellow-50' },
  normal: { emoji: '🟢', color: 'text-green-500', bgColor: 'bg-green-50' }
};
```

### Snooze Duration Calculation
```python
from datetime import datetime, timedelta

def calculate_snooze_deadline(duration: str) -> datetime:
    now = datetime.now(timezone.utc)
    if duration == "1hour":
        return now + timedelta(hours=1)
    elif duration == "tomorrow":
        return now + timedelta(days=1)
    elif duration == "nextweek":
        return now + timedelta(weeks=1)
    return now  # default
```

## Assumptions Verified

1. ✅ Existing task model has all required fields (description, deadline, priority_indicator, status, source_message_id)
2. ✅ User isolation is already implemented in task routes
3. ✅ MongoDB supports sorting by computed fields
4. ✅ Frontend can navigate to existing message detail view
5. ✅ AI pipeline already sets priority_indicator values correctly

## Risks Identified

1. **Priority indicator values may vary**: AI might return different values than expected
   - Mitigation: Add fallback mapping for common variations
   
2. **Snooze deadline calculation timezone**: Users may expect local time
   - Mitigation: Store all deadlines in UTC, display in user's local timezone
   
3. **Task list performance with many tasks**: Large task lists may be slow
   - Mitigation: Implement pagination or limit to 100 tasks initially

## Recommendations

1. Extend existing task routes rather than creating new ones
2. Implement frontend task list component with priority indicators
3. Add snooze endpoint with duration parameter
4. Test user isolation for all task actions
5. Add loading states and empty states as per constitution