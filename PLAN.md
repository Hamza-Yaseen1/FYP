# Implementation Plan: Communication AI - Week 2 AI Intelligence

**Branch**: `1-baseline-spec` | **Date**: 2026-08-19 | **Spec**: [specs/1-baseline-spec/spec.md](specs/1-baseline-spec/spec.md)
**Input**: Feature specification from `/specs/1-baseline-spec/spec.md`

## Summary

Add AI intelligence layer to the existing Communication AI system. The AI module
analyzes incoming messages synchronously at ingestion time to classify priority,
extract tasks, detect deadlines, generate summaries, and suggest recommended actions.
The system uses a flexible LLM abstraction layer that supports OpenAI, Groq, or
Gemini providers. All AI outputs are advisory, explainable, and dismissible per
the constitution's "AI is Assistive, Not Magical" principle.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript 5.x (frontend)
**Primary Dependencies**: FastAPI, Motor (MongoDB async), Next.js, shadcn/ui
**Storage**: MongoDB (existing: messages, users, ai_analysis, tasks, connections collections)
**Testing**: pytest (backend), manual testing (frontend)
**Target Platform**: Web application (localhost + free-tier cloud)
**Project Type**: Web application (monorepo: backend/ + app/)
**Performance Goals**: <500ms API response (excluding AI), <3s dashboard load
**Constraints**: AI calls may take 1-5s; must not block UI; single-user dev mode
**Scale/Scope**: Single user, ~100 messages/day, FYP demo scale

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| Simplicity First | PASS | Single LLM abstraction, no microservices, straightforward orchestrator |
| Vertical Slices | PASS | Each AI feature (priority, tasks, summary) independently testable |
| AI is Assistive | PASS | All outputs advisory, confidence levels shown, user can dismiss |
| User Control | PASS | No auto-actions, user confirms all AI suggestions |
| Security & Privacy | PASS | API keys in env vars, no plaintext logging, server-side analysis |
| Clean Code | PASS | Python PEP 8, TypeScript ESLint, clear module separation |
| Progressive Enhancement | PASS | Dashboard works without AI, shows "pending" status when unavailable |

**Gate Result**: PASS - all principles satisfied

## Project Structure

### Documentation (this feature)

```text
specs/1-baseline-spec/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0: LLM provider research
├── data-model.md        # Phase 1: Updated data models
├── quickstart.md        # Phase 1: Development setup guide
└── contracts/           # Phase 1: API contracts
    └── messages-api.md  # Updated message endpoints
```

### Source Code (repository root)

```text
backend/
├── main.py                     # FastAPI app (existing)
├── database.py                 # MongoDB connection (existing)
├── models/
│   ├── message.py              # Message model (update: add AI fields)
│   ├── task.py                 # NEW: Task model
│   └── ai_analysis.py          # NEW: AI analysis result model
├── routes/
│   ├── messages.py             # Message routes (update: add AI analysis)
│   ├── webhooks.py             # Webhook routes (update: add AI trigger)
│   └── tasks.py                # NEW: Task management routes
├── services/
│   ├── ai/
│   │   ├── __init__.py         # AI service package
│   │   ├── analyzer.py         # NEW: Main AI orchestrator
│   │   ├── providers/
│   │   │   ├── __init__.py     # Provider package
│   │   │   ├── base.py         # Abstract LLM provider interface
│   │   │   ├── openai.py       # OpenAI provider
│   │   │   ├── groq.py         # Groq provider
│   │   │   └── gemini.py       # Gemini provider
│   │   ├── prompts/
│   │   │   ├── priority.txt    # Priority classification prompt
│   │   │   ├── tasks.txt       # Task extraction prompt
│   │   │   ├── summary.txt     # Summary generation prompt
│   │   │   └── actions.txt     # Recommended actions prompt
│   │   └── fallback.py         # Fallback logic for AI failures
│   └── message_service.py      # Message business logic (existing, update)
└── requirements.txt            # Add: openai, groq, google-generativeai

app/
├── (dashboard)/
│   └── page.tsx                # Update: show AI analysis results
├── components/
│   ├── message-card.tsx        # Update: add priority badge, summary
│   ├── task-list.tsx           # NEW: Task display component
│   └── ai-status.tsx           # NEW: AI analysis status indicator
└── lib/
    └── api.ts                  # Update: add task API calls
```

**Structure Decision**: Web application structure with backend/ and app/ directories.
New AI services live in backend/services/ai/ with provider abstraction. Frontend
components are added to app/components/ following existing shadcn/ui patterns.

## Complexity Tracking

> No constitution violations. All design choices align with simplicity principles.

| Decision | Rationale | Alternatives Considered |
|----------|-----------|------------------------|
| Single LLM abstraction | Allows provider swaps without code changes | Hardcoding one provider (less flexible) |
| Synchronous AI analysis | Simpler architecture, adequate for FYP scale | Async queue (over-engineered for single user) |
| Prompt templates as files | Version-controlled, easy to iterate | Hardcoded strings (harder to maintain) |
| Separate task collection | Clear data boundaries, simpler queries | Embedding in messages (complex aggregation) |

---

## Phase 0: Research & Decisions

### Research Task: LLM Provider Selection

**Decision**: Use a provider abstraction with OpenAI as default, Groq and Gemini
as alternatives.

**Rationale**:
- OpenAI: Most documented, reliable, good for FYP demos
- Groq: Free tier available, fast inference, good for development
- Gemini: Free tier, good quality, Google ecosystem integration

**Alternatives Considered**:
- Anthropic Claude: Higher quality but more expensive, less free tier access
- Local models (Ollama): Requires GPU, adds complexity, not suitable for FYP
- Hugging Face: More setup overhead, less consistent API

**Implementation**: Abstract base class with provider-specific implementations.
Configuration via environment variable `LLM_PROVIDER=openai|groq|gemini`.

### Research Task: Prompt Engineering Strategy

**Decision**: Use structured prompts with JSON output format for all AI tasks.

**Rationale**:
- Structured output ensures consistent parsing
- JSON format allows direct model validation with Pydantic
- Version-controlled prompt templates enable iteration

**Alternatives Considered**:
- Free-form text parsing: Less reliable, harder to validate
- Function calling: More complex, not all providers support it equally
- Chain-of-thought: Adds latency, not needed for classification tasks

### Research Task: AI Failure Handling

**Decision**: Implement graceful degradation with retry logic and user notification.

**Rationale**:
- Constitution requires progressive enhancement
- Users must know when AI analysis is pending or failed
- Retry logic prevents transient failures from affecting UX

**Alternatives Considered**:
- Blocking until AI responds: Violates "never block UI" principle
- Silent failure: Users wouldn't know analysis is missing
- Circuit breaker: Over-engineered for FYP scale

---

## Phase 1: Design & Contracts

### Data Model Updates

**See**: [data-model.md](data-model.md)

Key changes:
- Message model: Add `ai_analysis` embedded document
- New Task model: Extracted tasks with status tracking
- New AI Analysis model: Confidence scores, provider metadata

### API Contracts

**See**: [contracts/messages-api.md](contracts/messages-api.md)

Updated endpoints:
- `POST /messages` - Now triggers synchronous AI analysis
- `GET /messages/{id}` - Returns message with AI analysis
- `GET /tasks` - List all tasks for user
- `PUT /tasks/{id}` - Update task status
- `DELETE /tasks/{id}` - Delete task

### Quickstart Guide

**See**: [quickstart.md](quickstart.md)

Development setup:
1. Set LLM_PROVIDER env var (openai/groq/gemini)
2. Set corresponding API key env var
3. Run backend: `uvicorn main:app --reload`
4. Run frontend: `npm run dev`
5. Test with simulated message via webhook

---

## Implementation Roadmap

### Week 2, Days 1-2: AI Foundation

**Goal**: LLM abstraction layer working with one provider

**Tasks**:
1. Create `backend/services/ai/providers/base.py` - Abstract provider interface
2. Create `backend/services/ai/providers/openai.py` - OpenAI implementation
3. Create `backend/services/ai/analyzer.py` - Main orchestrator
4. Create prompt templates in `backend/services/ai/prompts/`
5. Test with hardcoded message, verify structured output

**Vertical Slice**: Send message via API → AI analyzes → Response includes priority

### Week 2, Days 3-4: Priority Classification

**Goal**: Messages classified into Urgent/Important/Normal/Low with confidence

**Tasks**:
1. Implement priority classification prompt
2. Update Message model to include `ai_analysis` field
3. Update `POST /messages` endpoint to trigger analysis
4. Update frontend MessageCard to show priority badge
5. Test with various message types

**Vertical Slice**: Message arrives → Priority assigned → Dashboard shows badge

### Week 2, Days 5-6: Task Extraction

**Goal**: Actionable tasks extracted from messages with deadlines

**Tasks**:
1. Implement task extraction prompt
2. Create Task model and routes
3. Update analyzer to extract tasks
4. Create TaskList frontend component
5. Test with messages containing clear action items

**Vertical Slice**: Message with task → Task extracted → Task appears in list

### Week 3, Days 1-2: Summary & Actions

**Goal**: Summaries generated, recommended actions suggested

**Tasks**:
1. Implement summary generation prompt
2. Implement recommended actions prompt
3. Update MessageCard to show summary and actions
4. Test with long messages and various content types

**Vertical Slice**: Long message → Summary shown → Action suggested

### Week 3, Days 3-4: Multi-Provider Support

**Goal**: Switch between OpenAI, Groq, Gemini via config

**Tasks**:
1. Implement Groq provider
2. Implement Gemini provider
3. Add provider selection via env var
4. Test each provider with same prompts

**Vertical Slice**: Change env var → Different provider used → Same results

### Week 3, Days 5: Polish & Testing

**Goal**: Error handling, edge cases, documentation

**Tasks**:
1. Implement fallback logic for AI failures
2. Add confidence level display
3. Test edge cases (long messages, no tasks, etc.)
4. Update quickstart.md
5. Final integration testing

**Vertical Slice**: AI fails → Graceful fallback → User notified

---

## Risk Areas & Mitigations

### Risk 1: AI Hallucination

**Description**: AI generates incorrect priorities, fake tasks, or wrong deadlines.

**Mitigation**:
- Show confidence levels for all AI outputs
- Mark low-confidence results with "Needs review" flag
- Log discrepancies for prompt improvement
- User can always override/correct AI decisions

### Risk 2: AI Service Unavailable

**Description**: LLM API down, rate limited, or network issues.

**Mitigation**:
- Dashboard loads without AI analysis (Progressive Enhancement)
- Show "AI analysis pending" indicator
- Queue messages for analysis when service recovers
- Never block the UI waiting for AI

### Risk 3: Slow AI Response

**Description**: AI takes 5+ seconds, impacting user experience.

**Mitigation**:
- Synchronous analysis for now (adequate for FYP scale)
- Show loading state during analysis
- Future: async background processing if needed
- Cache analysis results to avoid re-analysis

### Risk 4: Prompt Quality

**Description**: Initial prompts produce poor results, requiring iteration.

**Mitigation**:
- Prompt templates as separate files (easy to iterate)
- Structured JSON output for reliable parsing
- Test with diverse message set
- Log all AI decisions for analysis

---

## Testing Approach

### Unit Tests (pytest)

- `test_ai_analyzer.py`: Test orchestrator logic with mocked providers
- `test_providers.py`: Test each provider's response parsing
- `test_prompts.py`: Test prompt template rendering

### Integration Tests

- `test_messages_ai.py`: Test POST /messages triggers AI analysis
- `test_tasks.py`: Test task CRUD operations
- `test_fallback.py`: Test AI failure scenarios

### Manual Testing Checklist

- [ ] Send message with deadline → Priority = Urgent/Important
- [ ] Send message with task request → Task extracted
- [ ] Send long message → Summary generated
- [ ] Send casual message → Priority = Normal/Low
- [ ] AI unavailable → Dashboard still loads
- [ ] Low confidence → "Needs review" flag shown
- [ ] User dismisses AI suggestion → Works correctly

---

## Success Criteria Verification

| Criterion | Verification Method | Target |
|-----------|-------------------|--------|
| SC-003: AI priority accuracy | Test set of 50 messages | 80%+ match |
| SC-004: Task extraction accuracy | Messages with clear tasks | 85%+ correct |
| SC-005: Summary quality | Long messages tested | 90% under 100 words |
| SC-006: Workflow time | User testing | Under 2 minutes |
| SC-007: Performance | Load test with 100 messages | No degradation |
| SC-008: Fallback works | AI service disabled | Dashboard functional |
