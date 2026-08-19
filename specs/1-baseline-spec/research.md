# Research: LLM Provider & AI Architecture

**Date**: 2026-08-19
**Feature**: Communication AI - AI Intelligence Layer

## Decision 1: LLM Provider Strategy

### Decision
Use a provider abstraction layer with OpenAI as default, Groq and Gemini as
alternatives. Provider selected via `LLM_PROVIDER` environment variable.

### Rationale
- **OpenAI**: Most documented API, reliable, good model variety (GPT-4o-mini
  for cost efficiency), strong structured output support
- **Groq**: Free tier available, extremely fast inference (good for demos),
  compatible with OpenAI API format
- **Gemini**: Free tier, good quality, Google ecosystem, native JSON mode

### Alternatives Considered
| Provider | Pros | Cons | Decision |
|----------|------|------|----------|
| OpenAI | Best docs, reliable, structured output | Paid, rate limits | Default provider |
| Groq | Free, fast, OpenAI-compatible | Limited models, newer service | Development/testing |
| Gemini | Free tier, good quality | Different API format | Alternative option |
| Anthropic Claude | Highest quality | Expensive, limited free access | Excluded |
| Local (Ollama) | Free, private | Requires GPU, adds complexity | Excluded for FYP |
| Hugging Face | Many models | Inconsistent APIs, more setup | Excluded |

### Implementation Notes
- Abstract base class defines provider interface
- Each provider implements `analyze(prompt: str) -> dict`
- Provider-specific code handles API formatting
- Environment variable selects active provider
- Fallback to OpenAI if configured provider fails

---

## Decision 2: Prompt Engineering Strategy

### Decision
Use structured prompts with explicit JSON output format. Prompts stored as
versioned text templates in `backend/services/ai/prompts/`.

### Rationale
- Structured output ensures consistent, parseable responses
- JSON format enables direct Pydantic model validation
- Template files allow iteration without code changes
- Version control tracks prompt evolution

### Alternatives Considered
| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| Structured JSON prompts | Reliable parsing, type-safe | More tokens, verbose | Selected |
| Free-form text parsing | Flexible, fewer tokens | Unreliable, error-prone | Rejected |
| Function calling | Native support in some APIs | Inconsistent across providers | Rejected |
| Chain-of-thought | Better reasoning | Adds latency, not needed | Rejected |

### Prompt Template Structure
```
backend/services/ai/prompts/
├── priority.txt      # Priority classification
├── tasks.txt         # Task extraction
├── summary.txt       # Summary generation
└── actions.txt       # Recommended actions
```

Each template:
- Has placeholders for message content
- Requests JSON output with defined schema
- Includes examples for few-shot learning
- Has confidence score requirement

---

## Decision 3: AI Failure Handling

### Decision
Implement graceful degradation with three levels:
1. **Retry**: Attempt 1 retry on transient failure
2. **Fallback**: Show message without analysis
3. **Notification**: Display "AI analysis pending" status

### Rationale
- Constitution requires progressive enhancement
- Users must know when AI analysis is missing
- Retry handles transient network issues
- Fallback ensures dashboard always loads

### Alternatives Considered
| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| Retry + Fallback + Notify | Comprehensive, user-friendly | More code | Selected |
| Blocking until success | Guaranteed analysis | Violates "never block UI" | Rejected |
| Silent failure | Simple | Users unaware of missing data | Rejected |
| Circuit breaker | Prevents cascade failures | Over-engineered for FYP | Rejected |

### Fallback Behavior
```python
try:
    analysis = await provider.analyze(message)
except Exception as e:
    logger.warning(f"AI analysis failed: {e}")
    analysis = {
        "priority": "pending",
        "summary": None,
        "tasks": [],
        "confidence": 0,
        "status": "analysis_pending"
    }
```

---

## Decision 4: Synchronous vs Asynchronous Analysis

### Decision
Synchronous analysis at message ingestion time. Analysis completes before
API response returned to client.

### Rationale
- Simpler architecture (no background job queue)
- Adequate for FYP scale (single user, ~100 messages/day)
- User sees results immediately in response
- Avoids complexity of polling for analysis status

### Alternatives Considered
| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| Synchronous | Simple, immediate results | Slower ingestion | Selected |
| Async background | Fast ingestion, parallelism | Complex, status polling needed | Rejected for FYP |
| On-demand | Only analyze when needed | Delayed results, lazy UX | Rejected |

### Performance Considerations
- LLM calls take 1-5 seconds depending on provider
- API response time will be 2-6 seconds total
- Frontend shows loading state during analysis
- Acceptable for FYP demo scale

---

## Decision 5: Task Model Design

### Decision
Separate `tasks` collection in MongoDB, linked to messages via `message_id`.
Tasks have their own lifecycle (pending/completed) independent of message state.

### Rationale
- Clear data boundaries between messages and tasks
- Simpler queries for task management
- Tasks can be edited/deleted without affecting source message
- Aligns with spec: "source message reference" attribute

### Alternatives Considered
| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| Separate collection | Clear boundaries, simple queries | Join needed for full context | Selected |
| Embedded in messages | No joins needed | Complex updates, data duplication | Rejected |

### Task Schema
```python
class Task:
    id: ObjectId
    user_id: ObjectId
    message_id: ObjectId  # Reference to source message
    description: str
    deadline: datetime | None
    status: str  # "pending" | "completed"
    created_at: datetime
    updated_at: datetime
```

---

## Decision 6: Confidence Score Thresholds

### Decision
Use three confidence tiers:
- **High (≥80%)**: Show normally, no flag
- **Medium (50-79%)**: Show with "Review recommended" flag
- **Low (<50%)**: Show with "Needs review" flag, prominent warning

### Rationale
- Aligns with spec: "confidence below 70%" triggers review
- Three tiers provide nuance without overwhelming users
- Thresholds can be tuned based on testing results

### Implementation
```python
def get_confidence_level(score: float) -> str:
    if score >= 0.8:
        return "high"
    elif score >= 0.5:
        return "medium"
    else:
        return "low"
```
