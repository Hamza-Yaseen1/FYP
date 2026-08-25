# Research: Better Inbox

**Feature**: 011-better-inbox  
**Date**: 2026-08-26  
**Status**: Complete

## Research Questions

### 1. How should filtering be implemented?

**Decision**: Backend filtering with query parameters

**Rationale**: 
- The constitution requires FR-020: "System MUST apply filtering and searching on the backend/database, not client-side"
- Backend filtering ensures user isolation is maintained at the query level
- Performance scales better with large datasets
- Frontend only receives and displays filtered results

**Alternatives considered**:
- Client-side filtering: Rejected because it violates FR-020 and would require fetching all messages first
- Hybrid approach: Rejected because it adds complexity without clear benefit for this use case

### 2. How should search be implemented?

**Decision**: MongoDB text search with indexed fields

**Rationale**:
- MongoDB supports text indexes on string fields
- Text search is efficient for the expected message volume
- Can search across multiple fields (sender, content, subject) with a single query
- Aligns with existing MongoDB usage in the project

**Alternatives considered**:
- Elasticsearch: Rejected as overkill for FYP scope and adds infrastructure complexity
- Regex search: Rejected because it's slower and less flexible than text search
- Client-side search: Rejected because it violates FR-020

### 3. How should combined filters work?

**Decision**: AND logic with MongoDB query operators

**Rationale**:
- Multiple filters should narrow results (AND logic)
- MongoDB's `$and` operator or implicit AND with multiple fields achieves this
- Example: `{ user_id: uid, priority: "urgent", source: "whatsapp", sender: "Ali" }`
- Clean and efficient query construction

**Alternatives considered**:
- OR logic: Rejected because it would broaden results instead of narrowing
- Complex filter objects: Rejected because simple key-value pairs are sufficient

### 4. How should the inbox page be restructured?

**Decision**: Rebuild the inbox page using existing components

**Rationale**:
- Current inbox page is a stub with no functionality
- Dashboard page has working MessageList and related components
- Can reuse MessageList component with minimal modifications
- Add new filter/search components above the message list

**Alternatives considered**:
- Create entirely new components: Rejected because it violates Simplicity First principle
- Move functionality from dashboard: Rejected because it would break existing dashboard

### 5. What message fields are needed for filtering?

**Decision**: Use existing fields from MessageResponse model

**Rationale**:
- `priority`: Already exists in `ai_analysis.priority`
- `source`: Already exists as `source` field
- `sender`: Already exists as `sender` field
- `created_at`: Already exists for date filtering
- `status`: Already exists for unread filtering (`status: "unread"`)

**No new fields required** - all filtering can be done with existing data.

### 6. How should filter counts be displayed?

**Decision**: Backend aggregation endpoint for counts

**Rationale**:
- Filter counts (e.g., "Urgent (5)") require knowing total counts per filter
- A separate endpoint can provide counts without fetching all messages
- More efficient than calculating counts on frontend from filtered results

**Alternatives considered**:
- Frontend calculation: Rejected because it would require fetching all messages first
- Include counts in main response: Rejected because it couples presentation with data

### 7. How should date filtering work?

**Decision**: Date range with start and end timestamps

**Rationale**:
- Users should be able to filter by a specific date or date range
- MongoDB's `$gte` and `$lte` operators handle date ranges efficiently
- Use ISO date strings for API parameters
- Default to "All dates" when no filter is applied

**Alternatives considered**:
- Relative dates (today, this week): Rejected because it adds complexity without clear benefit
- Single date only: Rejected because date ranges are more flexible

## Best Practices Identified

### Backend Filtering Pattern
```python
# Build query dynamically
query = {"user_id": uid}

if priority:
    query["ai_analysis.priority"] = priority
if source:
    query["source"] = source
if sender:
    query["sender"] = sender
if start_date:
    query["created_at"] = {"$gte": start_date}
if end_date:
    query.setdefault("created_at", {})["$lte"] = end_date
if status:
    query["status"] = status
if search:
    query["$text"] = {"$search": search}
```

### Frontend Filter State Pattern
```typescript
const [filters, setFilters] = useState({
  tab: 'all',        // all | urgent | important | normal | unread
  source: null,      // string | null
  priority: null,    // string | null
  startDate: null,   // Date | null
  endDate: null,     // Date | null
  sender: null,      // string | null
  search: ''         // string
});
```

### MongoDB Text Index
```python
# Create text index on searchable fields
await messages_collection.create_index([
    ("sender", "text"),
    ("content", "text"),
    ("ai_analysis.summary", "text")
])
```

## Assumptions Verified

1. ✅ Existing message model has all required fields for filtering
2. ✅ User isolation is already implemented at query level
3. ✅ MongoDB supports text search on indexed fields
4. ✅ Frontend components can be reused with modifications
5. ✅ Backend API can be extended with query parameters

## Risks Identified

1. **Performance with large datasets**: Text search on large collections may be slow
   - Mitigation: Add proper indexes, limit results, consider pagination
   
2. **Date timezone handling**: Dates stored in UTC, users may expect local time
   - Mitigation: Store all dates in UTC, display in user's local timezone
   
3. **Filter state synchronization**: URL state vs component state
   - Mitigation: Use URL search params for shareable filtered views

## Recommendations

1. Add MongoDB text indexes before implementing search
2. Implement filtering incrementally (tabs first, then dropdowns, then search)
3. Add loading states for each filter operation
4. Test user isolation with combined filters
5. Consider pagination for large message volumes (future enhancement)