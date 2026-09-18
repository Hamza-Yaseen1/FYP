# Load Testing Feature Documentation

## Overview

A temporary load testing feature has been added to your Communication AI project. This allows you to quickly generate multiple test messages to verify system performance and AI analysis capabilities.

## Features

### Backend (`POST /test/bulk-messages`)

**Endpoint:** `http://localhost:8000/test/bulk-messages`

**Authentication:** Required (uses current logged-in user)

**Request Body:**
```json
{
  "count": 50
}
```

**Validation:**
- `count` must be between 1 and 150
- Only authenticated users can access this endpoint

**Behavior:**
- Creates the specified number of messages for the current user
- Each message goes through the full AI analysis pipeline
- Messages use 15 realistic templates that cycle
- Each message is unique (includes timestamp in content)
- Small delays (0.5s every 10 messages) prevent server overload
- Logs progress every 20 messages
- Properly handles threading and conversation grouping
- User isolation is enforced (messages only created for authenticated user)

**Response:**
```json
{
  "success": true,
  "created": 50,
  "requested": 50,
  "message_ids": ["id1", "id2", "..."],
  "errors": []
}
```

### Frontend (`BulkTestButton` Component)

**Location:** Displayed at the bottom of the Dashboard page

**Features:**
- Three preset buttons: 20, 50, and 100 messages
- Loading state with spinner during creation
- Success/error status display with color coding
- Automatic dashboard refresh after completion
- Helpful description text

**Visual Design:**
- Yellow dashed border to indicate temporary/test feature
- Clear loading indicators
- Color-coded result messages:
  - Green for success
  - Yellow for warnings
  - Red for errors

## Sample Messages

The system uses 15 realistic message templates that simulate various business communications:

1. Urgent reports from boss
2. Meeting reschedules from team lead
3. Client requests
4. HR reminders
5. Marketing reviews
6. Support tickets
7. Sprint planning
8. Finance approvals
9. Code reviews
10. Customer feedback
11. Vendor updates
12. Sales announcements
13. Security alerts
14. Design deliverables
15. Operations notifications

Each template includes:
- Realistic sender names
- Appropriate content
- Varied sources (email, slack, github, whatsapp)

## Testing the Feature

1. **Start the backend:**
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

2. **Start the frontend:**
   ```bash
   npm run dev
   ```

3. **Navigate to Dashboard:**
   - Log in to your account
   - Go to http://localhost:3000/dashboard
   - Scroll to the bottom

4. **Create test messages:**
   - Click "20 messages", "50 messages", or "100 messages"
   - Watch the loading indicator
   - Wait for completion message
   - Dashboard will automatically refresh

5. **Verify results:**
   - Check the message counts in summary cards
   - View messages in the "Recent messages" section
   - Check Inbox page for filtered views
   - Verify Analytics page for aggregated data
   - Inspect MongoDB to verify proper storage

## Performance Expectations

- **20 messages:** ~15-25 seconds
- **50 messages:** ~40-60 seconds  
- **100 messages:** ~90-120 seconds

Times vary based on:
- AI provider response time
- Server resources
- Network latency
- Database performance

## Architecture Notes

### Backend Flow

```
POST /test/bulk-messages
  ↓
Validate count (1-150)
  ↓
Authenticate user
  ↓
For each message:
  ├─ Select template (cycling)
  ├─ Generate unique content
  ├─ Resolve threading
  ├─ Insert message document
  ├─ Run AI analysis (process_message)
  └─ Update with ai_analysis
  ↓
Return summary response
```

### Frontend Flow

```
User clicks button
  ↓
Set loading state
  ↓
POST /test/bulk-messages
  ↓
Wait for completion
  ↓
Display result message
  ↓
Refresh dashboard (after 1s delay)
```

## Code Organization

### New Files
- `backend/routes/test.py` - Load testing endpoint
- `components/BulkTestButton.tsx` - UI component
- `LOAD_TESTING_CLEANUP.md` - Removal instructions
- `LOAD_TESTING_FEATURE.md` - This documentation

### Modified Files
- `backend/main.py` - Added test router
- `app/(dashboard)/dashboard/page.tsx` - Added BulkTestButton

## Safety Features

1. **Rate limiting:** Small delays prevent overwhelming the server
2. **Maximum cap:** Cannot create more than 150 messages per request
3. **Authentication:** Only authenticated users can access
4. **User isolation:** Messages only created for authenticated user
5. **Error handling:** Graceful degradation on failures
6. **Progress logging:** Server logs progress for monitoring

## Limitations

- Maximum 150 messages per request (backend enforced)
- No batch deletion feature (use MongoDB directly if needed)
- Messages are permanent (not marked as test data)
- AI analysis uses real quota/credits
- No progress bar (only final result)

## Cleanup Before Production

**IMPORTANT:** This is a temporary testing feature and should be removed before production deployment.

See `LOAD_TESTING_CLEANUP.md` for detailed removal instructions.

Quick checklist:
- [ ] Delete `backend/routes/test.py`
- [ ] Delete `components/BulkTestButton.tsx`
- [ ] Remove test router import from `backend/main.py`
- [ ] Remove test router registration from `backend/main.py`
- [ ] Remove BulkTestButton import from `dashboard/page.tsx`
- [ ] Remove BulkTestButton section from `dashboard/page.tsx`
- [ ] Delete `LOAD_TESTING_CLEANUP.md`
- [ ] Delete `LOAD_TESTING_FEATURE.md`

## Troubleshooting

### Backend errors

**"401 Unauthorized"**
- Solution: Make sure you're logged in

**"422 Validation Error"**
- Solution: Check that count is between 1 and 150

**"500 Internal Server Error"**
- Check backend logs
- Verify MongoDB connection
- Check AI provider credentials

### Frontend errors

**Button not appearing**
- Clear browser cache
- Check console for import errors
- Verify component file exists

**Loading forever**
- Check backend logs
- Verify backend is running
- Check network tab in DevTools

**Dashboard not refreshing**
- Manually refresh the page
- Check browser console for errors

## Future Enhancements (If Needed)

Potential improvements if this becomes permanent:

1. Custom message content input
2. Progress bar with real-time updates
3. Batch deletion of test messages
4. Message template selection
5. Source/sender customization
6. WebSocket for live updates
7. Export results to CSV
8. Performance metrics display
9. Parallel processing option
10. Test data marking/filtering

## Support

For issues or questions:
1. Check backend logs: `cd backend && tail -f logs/app.log`
2. Check browser console: DevTools → Console tab
3. Verify MongoDB documents: Use MongoDB Compass or CLI
4. Test endpoint directly: Use Postman or curl

Example curl test:
```bash
curl -X POST http://localhost:8000/test/bulk-messages \
  -H "Content-Type: application/json" \
  -d '{"count": 5}' \
  --cookie "session=YOUR_SESSION_COOKIE"
```
