# Implementation Plan: Task Extraction & Deadline Detection

**Branch**: `004-task-extraction-deadline` | **Date**: 2026-08-20 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-task-extraction-deadline/spec.md`

## Summary

Add task extraction and deadline detection to the existing AI analysis pipeline.
When a message arrives, the system extracts actionable tasks (with deadlines and
priority indicators) in the same single LLM call used for priority classification.
Extracted tasks are stored in both the message's `ai_analysis` embedded document
and the separate `tasks` collection. The dashboard shows task indicators on message
cards; a new Tasks page lists all extracted tasks.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript 5.x (frontend)
**Primary Dependencies**: FastAPI, Motor (MongoDB async), Next.js 16, shadcn/ui
**Storage**: MongoDB (existing: messages, tasks collections)
**Testing**: pytest (backend), manual testing (frontend)
**Target Platform**: Web application (localhost + free-tier cloud)
**Project Type**: Web application (monorepo: backend/ + app/)
**Performance Goals**: <500ms API response (excluding AI), <3s dashboard load
**Constraints**: Single LLM call for all AI features; no extra latency budget
**Scale/Scope**: Single user, ~100 messages/day, FYP demo scale

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| Simplicity First | PASS | Extend existing analyzer.py, no new services; single LLM call |
| Vertical Slices | PASS | Task extraction → stored → displayed; each step testable |
| AI is Assistive | PASS | Tasks are advisory, user reviews before acting, no auto-actions |
| User Control | PASS | No auto-deletion, no auto-responses; user manages tasks |
| Security & Privacy | PASS | API keys in env vars, no new external services, server-side analysis |
| Clean Code | PASS | Extend existing patterns (Pydantic models, prompt templates) |
| Progressive Enhancement | PASS | Dashboard works without tasks; empty arrays on AI failure |
| No false positives | PASS | Prompt rules: only extract explicit tasks, empty array if none |
| No invented deadlines | PASS | Deadline from message text only, null if not mentioned |

**Gate Result**: PASS - all principles satisfied

## Project Structure

### Documentation (this feature)

```text
specs/004-task-extraction-deadline/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0: LLM prompt research
├── data-model.md        # Phase 1: Updated data models
├── quickstart.md        # Phase 1: Development setup guide
├── contracts/           # Phase 1: API contracts
│   └── messages-api.md  # Updated message endpoints with tasks
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code (repository root)

```text
backend/
├── main.py                     # FastAPI app (no changes)
├── database.py                 # MongoDB connection (no changes, tasks_collection exists)
├── models/
│   ├── message.py              # UPDATE: AIAnalysis.tasks_extracted → list[ExtractedTask]
│   └── task.py                 # NEW: Task Pydantic model
├── routes/
│   ├── messages.py             # UPDATE: store tasks in tasks collection after analysis
│   ├── webhooks.py             # UPDATE: same task storage logic
│   └── tasks.py                # NEW: Task CRUD endpoints
├── services/
│   └── ai/
│       ├── __init__.py         # No changes (exports analyze_message)
│       ├── analyzer.py         # UPDATE: call extract_tasks, store in tasks collection
│       ├── providers/
│       │   ├── base.py         # UPDATE: AIAnalysisResult.tasks_extracted → list[ExtractedTask]
│       │   └── groq.py         # UPDATE: single LLM call for priority+tasks+deadlines
│       └── prompts/
│           ├── priority.txt    # UPDATE: combine with task extraction in single prompt
│           ├── tasks.txt       # UPDATE: enhanced with deadline detection rules
│           └── summary.txt     # No changes
└── test_task_extraction.py     # NEW: Tests for task extraction + deadline detection

app/
├── (dashboard)/
│   ├── dashboard/page.tsx      # UPDATE: add Tasks summary card
│   └── tasks/page.tsx          # UPDATE: replace placeholder with real task list
├── components/
│   ├── MessageList.tsx          # UPDATE: show task count indicator on message cards
│   └── TaskList.tsx             # NEW: Task list component for Tasks page
└── lib/
    └── utils.ts                # No changes
```

**Structure Decision**: Extend existing web application structure. New files are
minimal: `task.py` model, `tasks.py` routes, `TaskList.tsx` component, and
`test_task_extraction.py`. Most changes are updates to existing files.

## Complexity Tracking

> No constitution violations. All design choices align with simplicity principles.

| Decision | Rationale | Alternatives Considered |
|----------|-----------|------------------------|
| Single LLM call for priority+tasks | Constitution: no extra latency budget | Two separate calls (adds latency, more complex) |
| Structured task objects in prompt | Reliable parsing with Pydantic validation | Free-form text parsing (unreliable) |
| Tasks in both embedded doc + collection | Embedded = fast dashboard reads; collection = task page queries | Collection only (slow dashboard) or embedded only (slow task queries) |
| Enhance existing priority prompt | Single call = no extra API cost | Separate task extraction call (extra cost + latency) |

---

## Phase 0: Research & Decisions

### Research Task: Combining Priority + Task Extraction in One Prompt

**Decision**: Extend the existing priority prompt to include task extraction
and deadline detection in a single LLM call. The prompt returns a combined
JSON with priority, tasks, and deadlines.

**Rationale**:
- Constitution requires single LLM call (no extra latency)
- Reduces API costs (one call instead of two)
- Groq supports structured JSON output with `response_format={"type": "json_object"}`
- Prompt can instruct the model to classify priority AND extract tasks in one pass

**Alternatives Considered**:
- Separate calls for priority and tasks: Adds latency, violates FR-011
- Chained prompts (priority first, then tasks): More complex, still two calls
- Function calling: Not all providers support it equally, more complex

### Research Task: Task Data Structure in Prompt Output

**Decision**: Return tasks as structured objects within the combined prompt output:

```json
{
  "priority": "urgent",
  "confidence": 0.92,
  "explanation": "Message contains deadline 'tonight' and action request",
  "tasks_extracted": [
    {
      "description": "Send FYP slides",
      "deadline": "Tonight",
      "priority_indicator": "tonight",
      "requires_action": true
    }
  ],
  "deadlines": ["Tonight"]
}
```

**Rationale**:
- Pydantic model validates the structure automatically
- Consistent with existing `AIAnalysisResult` pattern
- `deadlines` array provides a flat list of all detected time expressions
  for quick display without parsing task objects

**Alternatives Considered**:
- Separate API for tasks: More complex, extra round-trip
- Free-form task text: Harder to parse and validate
- Tasks embedded only in deadlines array: Loses structured task info

### Research Task: Storing Tasks in MongoDB

**Decision**: When tasks are extracted, store them in both:
1. The message's `ai_analysis.tasks_extracted` field (embedded)
2. The `tasks` collection (separate documents with source_message reference)

**Rationale**:
- Embedded: Dashboard reads messages and immediately sees tasks (fast)
- Collection: Tasks page can query all tasks across messages (fast)
- Dual-write is simple (just two insert/update operations)
- Consistent with existing pattern (ai_analysis is already embedded)

**Alternatives Considered**:
- Collection only: Requires join query for dashboard (slower)
- Embedded only: Tasks page requires scanning all messages (slower)
- Reference only (link to message): Extra query for task details

---

## Phase 1: Design & Contracts

### Data Model Updates

**See**: [data-model.md](data-model.md)

Key changes:
- New `ExtractedTask` Pydantic model for structured task objects
- `AIAnalysis.tasks_extracted` changes from `list[str]` to `list[ExtractedTask]`
- New `Task` model for MongoDB `tasks` collection documents
- `AIAnalysis.deadlines` remains `list[str]` (flat list of time expressions)

### API Contracts

**See**: [contracts/messages-api.md](contracts/messages-api.md)

Updated endpoints:
- `POST /messages` — Now returns extracted tasks in `ai_analysis.tasks_extracted`
- `GET /messages` — Messages include task data in `ai_analysis`
- `GET /tasks` — NEW: List all extracted tasks (with source message reference)
- `PUT /tasks/{id}/status` — NEW: Mark task as completed/pending
- `DELETE /tasks/{id}` — NEW: Delete a task (source message preserved)

### Quickstart Guide

**See**: [quickstart.md](quickstart.md)

Development setup:
1. Start MongoDB (existing)
2. Set GROQ_API_KEY in backend/.env (existing)
3. Run backend: `uvicorn main:app --reload`
4. Run frontend: `npm run dev`
5. Simulate a message with tasks → verify extraction on dashboard + tasks page

---

## Implementation Roadmap

### Day 11: Task Extraction Backend

**Goal**: AI extracts tasks from messages and stores them in MongoDB

**Tasks**:
1. Create `backend/models/task.py` — ExtractedTask and Task Pydantic models
2. Update `backend/services/ai/providers/base.py` — Change tasks_extracted type
3. Update `backend/services/ai/prompts/priority.txt` — Add task extraction instructions
4. Update `backend/services/ai/providers/groq.py` — Parse task objects from LLM response
5. Update `backend/services/ai/analyzer.py` — Store extracted tasks in tasks collection
6. Update `backend/routes/messages.py` — Store tasks after analysis
7. Update `backend/routes/webhooks.py` — Store tasks after analysis
8. Create `backend/routes/tasks.py` — Task CRUD endpoints
9. Create `backend/test_task_extraction.py` — Test extraction accuracy

**Vertical Slice**: Send message → AI extracts tasks → Tasks stored in MongoDB

### Day 12: Dashboard + Tasks Page Frontend

**Goal**: Users see task indicators on messages and can view all tasks

**Tasks**:
1. Update `components/MessageList.tsx` — Show task count badge on message cards
2. Update `app/(dashboard)/dashboard/page.tsx` — Add tasks summary card
3. Create `components/TaskList.tsx` — Task list component with status management
4. Update `app/(dashboard)/tasks/page.tsx` — Replace placeholder with TaskList

**Vertical Slice**: Dashboard shows task indicators → Tasks page lists all tasks

---

## Risk Areas & Mitigations

### Risk 1: Prompt Quality for Combined Task+Priority Extraction

**Description**: Combining priority classification and task extraction in one
prompt may reduce accuracy of either task.

**Mitigation**:
- Test with 50+ varied messages before finalizing prompt
- Use structured JSON output for reliable parsing
- Log all AI decisions for iteration
- Fallback: revert to separate calls if accuracy drops below thresholds

### Risk 2: Task Extraction Hallucination

**Description**: AI extracts tasks that don't exist in the message (false positives).

**Mitigation**:
- Constitution: "NEVER invent a task that is not in the message"
- Prompt rules: explicit criteria for what constitutes a task
- Test with informational messages to verify zero false positives
- User can dismiss/review all extracted tasks

### Risk 3: Deadline Invention

**Description**: AI invents deadlines not present in the message.

**Mitigation**:
- Constitution: "NEVER invent deadlines" — 0% tolerance
- Prompt rules: deadline must come directly from message text or be null
- Test with messages that have no deadlines to verify null output
- Validate deadline values against message content in tests

---

## Testing Approach

### Unit Tests (pytest)

- `test_task_extraction.py`:
  - Test extraction from messages with clear tasks
  - Test no extraction from informational messages
  - Test deadline preservation (ASAP, tonight, tomorrow, next week)
  - Test no deadline invention (null when no deadline mentioned)
  - Test multiple tasks from single message
  - Test graceful fallback on AI failure

### Manual Testing Checklist

- [ ] Send "Send me the FYP slides tonight" → task extracted with deadline "Tonight"
- [ ] Send "Can you review this document?" → task extracted, no deadline
- [ ] Send "I'll send you the files tomorrow" → no task extracted
- [ ] Send "FYI server down tomorrow" → no task extracted
- [ ] Send "ASAP: submit the form" → task extracted, priority = Urgent
- [ ] Send "Prepare slides next week" → task extracted, deadline = "next week"
- [ ] Dashboard shows task count badge on messages with tasks
- [ ] Tasks page lists all tasks with source message reference
- [ ] AI unavailable → messages appear without tasks, no errors

---

## Success Criteria Verification

| Criterion | Verification Method | Target |
|-----------|-------------------|--------|
| SC-001: Task extraction accuracy | Test set of 50 messages | 85%+ correct |
| SC-002: False positive rate | Informational messages tested | ≤10% |
| SC-003: Time expression accuracy | 30 messages with varied expressions | 90%+ correct |
| SC-004: No invented deadlines | All test messages validated | 0 hallucinated dates |
| SC-005: Single LLM call | Monitor API calls during analysis | 1 call per message |
| SC-006: Tasks page load time | Manual timing on localhost | <3 seconds |
| SC-007: Task indicator update | Send message, check dashboard | <10 seconds |
| SC-008: Graceful fallback | Disable AI, send messages | Dashboard functional |
