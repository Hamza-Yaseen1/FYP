# Implementation Plan: Priority Agent

**Feature Branch**: `2-priority-agent` | **Date**: 2026-08-19 | **Spec**: [specs/2-priority-agent/spec.md](spec.md)
**Input**: Feature specification from `/specs/2-priority-agent/spec.md`

## Goal of This Phase

Build a simple, reliable Priority Agent that classifies messages into
URGENT, IMPORTANT, NORMAL, or LOW. One agent, one job, done well.

No multi-agent system. No complex orchestration. Just a focused agent
that reads a message and returns a priority with confidence score.

## Technical Approach

Single LLM call with a structured prompt. The prompt includes:
- Clear priority level definitions
- Evidence requirements for each level
- Examples of correct classification
- Request for JSON output with priority, confidence, and explanation

The agent is stateless - it does not remember previous classifications.
Each message is analyzed independently.

## Files to Create or Update

### New Files

| File | Purpose |
|------|---------|
| `backend/services/ai/agents/__init__.py` | Agent package |
| `backend/services/ai/agents/priority.py` | Priority Agent implementation |
| `backend/services/ai/prompts/priority.txt` | Prompt template |
| `backend/services/ai/models.py` | Pydantic models for agent I/O |

### Updated Files

| File | Changes |
|------|---------|
| `backend/services/ai/analyzer.py` | Use Priority Agent |
| `backend/routes/messages.py` | Add priority override endpoint |

## How the Priority Agent Works

### Step-by-Step Flow

1. User sends message (via webhook or API)
2. Message stored in MongoDB (state: active)
3. Priority Agent triggered synchronously
4. Agent sends message to LLM with priority prompt
5. LLM returns JSON: priority, confidence, explanation
6. Agent validates response
7. Result stored in message ai_analysis.priority field
8. Response returned to caller with priority included
9. Dashboard auto-polls, shows priority badge

### Failure Flow

1. LLM call fails (timeout, API error)
2. Agent catches exception
3. Agent returns safe default: NORMAL, confidence 0.0
4. Status set to pending (not failed)
5. Message still appears on dashboard
6. Error logged for debugging

## Prompt Design

The prompt template lives in `backend/services/ai/prompts/priority.txt`.

Key elements:
- Clear definitions of all four priority levels
- Evidence requirements for URGENT and IMPORTANT
- Rule: when uncertain, default to NORMAL
- Rule: never invent urgency
- Request for JSON output with priority, confidence, explanation

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
    "explanation": "Message contains a deadline within 7 days requiring action.",
    "provider": "openai",
    "analyzed_at": "ISODate",
    "status": "completed"
  },
  "created_at": "ISODate",
  "updated_at": "ISODate"
}
```

### Priority Field Values

- urgent - Red indicator, top of queue
- important - Orange indicator, near top
- normal - Blue indicator, middle (DEFAULT)
- low - Gray indicator, bottom
- pending - Analysis not yet completed

## How Results Are Shown on Dashboard

### Message Card Updates

1. Priority Badge: Colored indicator next to message sender
2. Confidence Indicator: Subtle flag for low confidence
3. Explanation Tooltip: Hover over priority badge to see why
4. Override Button: Click priority badge to change priority

### Sorting

Dashboard sorts messages by priority:
1. URGENT (top)
2. IMPORTANT
3. NORMAL
4. LOW (bottom)

Within each priority, sort by timestamp (newest first).

## Implementation Steps

### Step 1: Create Pydantic Models

Create `backend/services/ai/models.py` with PriorityResult model.

### Step 2: Create Prompt Template

Create `backend/services/ai/prompts/priority.txt` with the classification prompt.

### Step 3: Create Priority Agent

Create `backend/services/ai/agents/priority.py` with PriorityAgent class.

### Step 4: Update Analyzer

Update `backend/services/ai/analyzer.py` to use PriorityAgent.

### Step 5: Add Priority Override Endpoint

Add PUT endpoint to `backend/routes/messages.py` for user overrides.

### Step 6: Update Frontend

Update dashboard components to show priority badges and explanations.

## Testing Plan

### Unit Tests

- Test classify returns valid priority levels
- Test confidence is between 0.0 and 1.0
- Test explanation is provided
- Test failure returns NORMAL default
- Test prompt renders correctly

### Integration Tests

- Test POST message triggers priority classification
- Test priority override persists
- Test dashboard shows priority badge

### Manual Testing Checklist

- Send urgent message, verify URGENT classification
- Send casual message, verify NORMAL classification
- Send message with deadline, verify IMPORTANT classification
- Override priority, verify it persists
- Disable AI, verify NORMAL default with pending status

## Definition of Done

- [ ] Priority Agent classifies messages into 4 levels
- [ ] Confidence score returned with every classification
- [ ] Explanation provided with every classification
- [ ] Failure gracefully defaults to NORMAL
- [ ] Priority override works via API
- [ ] Dashboard shows priority badges
- [ ] Dashboard shows confidence flags for low confidence
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing complete
- [ ] 80% accuracy on test set of 50 messages
