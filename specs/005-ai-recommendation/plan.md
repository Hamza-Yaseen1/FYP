# Implementation Plan: AI Recommended Action

**Branch**: `005-ai-recommendation` | **Date**: 2026-08-21 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-ai-recommendation/spec.md`

## Summary

Add a recommended action field to the AI analysis pipeline. When a message is analyzed, the system generates a short, verb-first recommendation (e.g., "Send the report before Friday") and displays it on the dashboard alongside priority, summary, and task information. The implementation extends the existing Groq LLM call to include recommendation generation in a single pass.

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript 5.x (frontend)
**Primary Dependencies**: FastAPI, Motor (MongoDB), Groq SDK, Next.js 15, Tailwind CSS, shadcn/ui
**Storage**: MongoDB (messages collection, ai_analysis embedded subdocument)
**Testing**: pytest (backend), manual testing (frontend)
**Target Platform**: Web (localhost development, Linux server deployment)
**Project Type**: Web application (frontend + backend monorepo)
**Performance Goals**: Dashboard loads < 3s, API responses < 500ms (excluding LLM calls)
**Constraints**: Single LLM call for all analysis features (no additional latency)
**Scale/Scope**: Single user FYP project, 10-50 messages/day

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Simplicity First**: Extending existing pipeline, no new services or patterns
- [x] **Vertical Slice**: End-to-end from LLM generation to dashboard display
- [x] **AI is Assistive, Not Magical**: Recommendation is advisory, stored for user review
- [x] **User Control**: User retains control; recommendation is display-only
- [x] **Security and Privacy**: No new data exposure; recommendation stored in existing ai_analysis subdocument
- [x] **Clean Code**: Extends existing GroqProvider pattern; follows PEP 8 and ESLint conventions
- [x] **Progressive Enhancement**: If recommendation fails, empty string returned; message still displays

**Gate Result**: PASS — no violations to justify.

## Project Structure

### Documentation (this feature)

```text
specs/005-ai-recommendation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (NOT created by /sp.plan)
```

### Source Code (repository root)

```text
backend/
├── models/
│   └── message.py          # UPDATE: Add recommended_action to AIAnalysis
├── services/
│   └── ai/
│       ├── analyzer.py     # UPDATE: Call recommendation generation
│       ├── prompts/
│       │   └── actions.txt # UPDATE: Rewrite prompt for single action
│       └── providers/
│           └── groq.py     # UPDATE: Add generate_recommendation() method
└── routes/
    └── messages.py         # No changes needed (response model handles it)

components/
└── MessageList.tsx         # UPDATE: Display recommended_action

app/
└── (dashboard)/
    └── dashboard/
        └── page.tsx        # No changes needed (MessageList handles display)
```

**Structure Decision**: Web application layout (Option 2). Backend in `backend/`, frontend in `app/` and `components/`. Feature touches 4 files total.

## Implementation Steps

### Step 1: Update the actions.txt prompt

**File**: `backend/services/ai/prompts/actions.txt`

Rewrite the prompt to generate a single recommended action. The prompt should:
- Accept the message content as input
- Output a JSON object with a single `recommended_action` string
- Follow the constitution rules: verb-first, under 15 words, same language, no invented actions
- Default to "Review this message" when no clear action exists

### Step 2: Add generate_recommendation() to GroqProvider

**File**: `backend/services/ai/providers/groq.py`

Add a new async method `generate_recommendation(message: str) -> str` that:
- Loads the `actions.txt` prompt
- Sends it to the Groq API with the message content
- Parses the JSON response
- Returns the `recommended_action` string
- Returns empty string `""` on failure (graceful fallback)

Follow the same pattern as `generate_summary()`.

### Step 3: Update AIAnalysis model

**File**: `backend/models/message.py`

Add `recommended_action: str = ""` to the `AIAnalysis` Pydantic model. This ensures the field is:
- Serialized in API responses
- Stored in MongoDB as part of the ai_analysis subdocument
- Defaults to empty string for existing messages

### Step 4: Update analyzer.py to call recommendation

**File**: `backend/services/ai/analyzer.py`

In the `analyze_message()` function, after calling `generate_summary()`:
- Call `provider.generate_recommendation(content)`
- Add the result to the analysis dict as `recommended_action`
- On failure, set `recommended_action: ""`

### Step 5: Update MessageList.tsx to display recommendation

**File**: `components/MessageList.tsx`

Add a display element for `recommended_action`:
- Show it as a subtle, italic line below the summary
- Style it with a distinct color (e.g., text-blue-400) to differentiate from summary
- Only render if `recommended_action` is non-empty
- Keep it compact (single line, no wrapping if possible)

## Data Model Changes

### MongoDB messages collection (ai_analysis subdocument)

**Before**:
```json
{
  "ai_analysis": {
    "priority": "urgent",
    "confidence": 0.85,
    "explanation": "...",
    "summary": "...",
    "recommended_actions": [],
    "tasks_extracted": [...],
    "deadlines": [...],
    "provider": "groq",
    "analyzed_at": "...",
    "status": "completed"
  }
}
```

**After**:
```json
{
  "ai_analysis": {
    "priority": "urgent",
    "confidence": 0.85,
    "explanation": "...",
    "summary": "...",
    "recommended_action": "Send the report before Friday",
    "recommended_actions": [],
    "tasks_extracted": [...],
    "deadlines": [...],
    "provider": "groq",
    "analyzed_at": "...",
    "status": "completed"
  }
}
```

**Note**: `recommended_actions` (array) is kept for backward compatibility. `recommended_action` (string) is the new field. Both coexist.

## Complexity Tracking

No violations — section not applicable.

## Testing Plan

### Manual Testing

1. **Send a test message with clear action**: "Please send the report before 5 PM"
   - Expected: Priority=Urgent, Recommended action="Send the report before 5 PM"
2. **Send an informational message**: "The meeting is at 3 PM tomorrow"
   - Expected: Recommended action="Review this message"
3. **Send a message in Arabic**: (if applicable)
   - Expected: Recommended action in Arabic
4. **Check dashboard display**: Verify recommended action appears below summary
5. **Check existing messages**: Old messages should show no recommended action (empty)

### Automated Testing (Optional)

- Unit test for `generate_recommendation()` with mocked Groq API
- Unit test for `analyze_message()` with recommendation flow
- Integration test for `POST /messages` response includes `recommended_action`

## Definition of Done

- [ ] `actions.txt` prompt rewritten for single action generation
- [ ] `generate_recommendation()` method added to GroqProvider
- [ ] `AIAnalysis` model includes `recommended_action` field
- [ ] `analyze_message()` calls recommendation generation
- [ ] Dashboard displays recommended action for new messages
- [ ] Old messages still work (backward compatible)
- [ ] Graceful fallback on recommendation failure (empty string)
- [ ] No additional LLM calls (single call for all analysis)
- [ ] Manual testing passed for all 3 user stories
- [ ] Code follows project conventions (PEP 8, ESLint)
