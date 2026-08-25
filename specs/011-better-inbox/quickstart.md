# Quickstart: Better Inbox

**Feature**: 011-better-inbox  
**Date**: 2026-08-26  
**Status**: Complete

## Overview

The Better Inbox feature improves the existing Inbox page with:
- Priority tabs (All, Urgent, Important, Normal, Unread)
- Filters (Source, Priority, Date, Sender)
- Search functionality
- Combined filtering
- Loading, empty, and error states

## Prerequisites

- Existing Communication AI project running
- User authenticated with valid JWT token
- Messages in the database (at least 5-10 for testing)

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

### 2. Navigate to Inbox

1. Open http://localhost:3000/inbox
2. You should see the improved inbox with tabs and filters

### 3. Test Priority Tabs

1. Click "All" tab - should show all messages
2. Click "Urgent" tab - should show only urgent messages
3. Click "Important" tab - should show only important messages
4. Click "Normal" tab - should show only normal messages
5. Click "Unread" tab - should show only unread messages

### 4. Test Source Filter

1. Click the Source dropdown
2. Select "WhatsApp" - should show only WhatsApp messages
3. Select "Gmail" - should show only Gmail messages
4. Clear the filter - should show all messages again

### 5. Test Priority Filter

1. Click the Priority dropdown
2. Select "Urgent" - should show only urgent messages
3. Select "Important" - should show only important messages
4. Clear the filter - should show all messages again

### 6. Test Date Filter

1. Click the Date filter
2. Select a start date - should show messages from that date onwards
3. Select an end date - should show messages up to that date
4. Clear the filter - should show all messages again

### 7. Test Sender Filter

1. Click the Sender dropdown
2. Select a sender - should show only messages from that sender
3. Clear the filter - should show all messages again

### 8. Test Search

1. Click in the search bar
2. Type a search term (e.g., "meeting", "slides", sender name)
3. Should show messages matching the search term
4. Clear the search - should show all messages again

### 9. Test Combined Filters

1. Click "Important" tab
2. Select "WhatsApp" source
3. Select a sender
4. Should show only important WhatsApp messages from that sender
5. Click "Clear All" - should reset all filters

### 10. Test Empty States

1. Apply filters that result in no messages
2. Should see "No communications found" message

### 11. Test Loading States

1. Refresh the page
2. Should see loading indicator while messages load

## API Testing

### Get Messages with Filters

```bash
# Get all messages
curl -b "access_token=YOUR_TOKEN" http://localhost:8000/messages

# Get urgent messages
curl -b "access_token=YOUR_TOKEN" "http://localhost:8000/messages?tab=urgent"

# Get WhatsApp messages
curl -b "access_token=YOUR_TOKEN" "http://localhost:8000/messages?source=whatsapp"

# Search for messages
curl -b "access_token=YOUR_TOKEN" "http://localhost:8000/messages?search=meeting"

# Combine filters
curl -b "access_token=YOUR_TOKEN" "http://localhost:8000/messages?tab=important&source=whatsapp&sender=Ali"
```

### Get Filter Counts

```bash
curl -b "access_token=YOUR_TOKEN" http://localhost:8000/messages/counts
```

### Get Unique Senders

```bash
curl -b "access_token=YOUR_TOKEN" http://localhost:8000/messages/senders
```

### Get Unique Sources

```bash
curl -b "access_token=YOUR_TOKEN" http://localhost:8000/messages/sources
```

## Testing Checklist

- [ ] Priority tabs work correctly
- [ ] Source filter works correctly
- [ ] Priority filter works correctly
- [ ] Date filter works correctly
- [ ] Sender filter works correctly
- [ ] Search works correctly
- [ ] Combined filters work correctly
- [ ] Clear all filters works
- [ ] Empty states display correctly
- [ ] Loading states display correctly
- [ ] Error states display correctly
- [ ] User isolation is maintained
- [ ] Performance is acceptable (< 2 seconds)

## Troubleshooting

### Messages not loading
- Check if backend server is running
- Check if user is authenticated (JWT token valid)
- Check browser console for errors

### Filters not working
- Check if backend API endpoints are working
- Check if query parameters are being sent correctly
- Check browser network tab for API responses

### Search not working
- Check if MongoDB text index is created
- Check if search query is being sent correctly
- Check backend logs for errors

## Next Steps

1. Implement the backend API endpoints
2. Implement the frontend components
3. Test with real data
4. Optimize performance if needed
5. Add pagination for large datasets