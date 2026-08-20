# Implementation Plan: Summary Agent & Delete Message

**Feature Branch**: `3-summary-delete` | **Date**: 2026-08-20 | **Spec**: [specs/3-summary-delete/spec.md](spec.md)
**Input**: Feature specification from `/specs/3-summary-delete/spec.md`

## Goal of This Phase

Add two features to the Communication AI system:
1. Summary Agent that creates short, clear summaries of messages
2. Delete Message feature that allows users to remove messages from the dashboard

Both features follow Simplicity First principle. One agent, one endpoint, clean UI.

## Technical Approach

### Summary Agent
Single LLM call with a focused prompt. The prompt requests a 1-2 sentence summary
that captures the main point of the message. The agent is stateless - each message
is summarized independently.

### Delete Message
Simple REST endpoint that permanently removes a message from MongoDB. Frontend
shows a confirmation dialog before deletion and refreshes the list after success.

## Files to Create or Update

### New Files

| File | Purpose |
|------|---------|
| `backend/services/ai/prompts/summary.txt` | Summary prompt template |
| `backend/services/ai/agents/summary.py` | Summary Agent implementation |

### Updated Files

| File | Changes |
|------|---------|
| `backend/services/ai/providers/groq.py` | Add summary method |
| `backend/services/ai/analyzer.py` | Add summary to analysis |
| `backend/models/message.py` | Add summary field to AIAnalysis |
| `backend/routes/messages.py` | Add DELETE endpoint |
| `components/MessageList.tsx` | Add summary display and delete button |

## How the Summary Agent Works

### Step-by-Step Flow

1. User sends message (via webhook or API)
2. Message stored in MongoDB (state: active)
3. Priority Agent classifies priority (existing)
4. Summary Agent generates summary (new)
5. Both results stored in message's ai_analysis field
6. Response returned to caller with priority and summary
7. Dashboard auto-polls, shows priority badge and summary

### Failure Flow

1. LLM call fails (timeout, API error)
2. Agent catches exception
3. Agent returns null for summary (not an error message)
4. Status set to "pending" (not "failed")
5. Message still appears on dashboard without summary
6. Error logged for debugging

## Summary Prompt Design

The prompt template lives in `backend/services/ai/prompts/summary.txt`.

Key elements:
- Clear instruction to create 1-2 sentence summary
- Rule: preserve action items and deadlines
- Rule: never invent information
- Rule: remove greetings and filler
- Request for JSON output with summary field

## How Delete Message Works

### API Flow

1. User clicks delete button on message card
2. Confirmation dialog appears
3. User confirms deletion
4. Frontend sends DELETE /messages/{id}
5. Backend removes message from MongoDB
6. Backend returns 204 No Content
7. Frontend removes message from list

### Failure Flow

1. Delete request fails (network error, etc.)
2. Backend returns error status
3. Frontend shows error message
4. Message remains on dashboard
5. User can retry

## How Results Are Stored in MongoDB

### Message Document Structure

```json
{
  "_id": "ObjectId",
  "sender": "John",
  "content": "Please send the report by Friday",
  "source": "whatsapp",
  "status": "unread",
  "state": "active",
  "ai_analysis": {
    "priority": "important",
    "confidence": 0.85,
    "explanation": "Message contains a deadline within 7 days.",
    "summary": "Report must be sent by Friday.",
    "provider": "groq",
    "analyzed_at": "ISODate",
    "status": "completed"
  },
  "created_at": "ISODate",
  "updated_at": "ISODate"
}
```

### Summary Field Values

- string - The generated summary
- null - Analysis not yet completed or failed

## How Results Are Shown on Dashboard

### Message Card Updates

1. **Summary**: Displayed below message content in gray text
2. **Delete Button**: Trash icon on the right side of each message card
3. **Confirmation Dialog**: Modal asking "Delete this message?"

### Layout

```
┌─────────────────────────────────────────────────────────┐
│ [Avatar] Sender Name  [Priority] [Source]    [Delete]  │
│                                                         │
│ Message content goes here...                            │
│                                                         │
│ Summary: Brief summary of the message                  │
│                                                         │
│ 2 hours ago                                             │
└─────────────────────────────────────────────────────────┘
```

## Implementation Steps

### Step 1: Create Summary Prompt

Create `backend/services/ai/prompts/summary.txt` with the summary prompt.

### Step 2: Update AIAnalysis Model

Add summary field to `backend/models/message.py` AIAnalysis class.

### Step 3: Update Analyzer

Update `backend/services/ai/analyzer.py` to generate summary after priority.

### Step 4: Add Delete Endpoint

Add DELETE /messages/{id} endpoint to `backend/routes/messages.py`.

### Step 5: Update MessageList Component

Update `components/MessageList.tsx` to:
- Display summary below message content
- Add delete button with confirmation dialog
- Handle deletion and list refresh

### Step 6: Update Frontend Types

Update Message interface to include summary field.

## Testing Plan

### Unit Tests

- Test summary prompt renders correctly
- Test summary is null on failure
- Test delete endpoint removes message
- Test delete endpoint returns 404 for invalid ID

### Integration Tests

- Test POST message triggers summary generation
- Test summary is stored in MongoDB
- Test DELETE removes message from MongoDB
- Test dashboard shows summary after creation
- Test dashboard removes message after deletion

### Manual Testing Checklist

- Send long message, verify summary generated
- Send short message, verify summary reflects content
- Click delete button, verify confirmation appears
- Confirm deletion, verify message disappears
- Cancel deletion, verify message remains
- Test with AI unavailable, verify no summary shown

## Definition of Done

- [ ] Summary Agent generates summaries for all messages
- [ ] Summaries are 1-2 sentences under 30 words
- [ ] Summaries accurately reflect message content
- [ ] Summaries are displayed on dashboard
- [ ] Delete button appears on each message card
- [ ] Confirmation dialog appears before deletion
- [ ] Messages are permanently removed from MongoDB
- [ ] Dashboard updates immediately after deletion
- [ ] Error handling works for both features
- [ ] All tests pass
- [ ] Manual testing complete
