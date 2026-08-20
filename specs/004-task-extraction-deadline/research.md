# Research: Task Extraction & Deadline Detection

**Feature**: 004-task-extraction-deadline
**Date**: 2026-08-20

## Research Task 1: Combining Priority + Task Extraction in One Prompt

**Decision**: Extend the existing priority prompt to include task extraction
and deadline detection in a single LLM call.

**Rationale**:
- Constitution (v1.1.0) requires single LLM call — no extra latency budget
- Existing `groq.py` already makes two calls (priority + summary); combining
  priority + tasks into one call reduces total from 2 to 2 (summary stays separate)
- Groq's `qwen/qwen3.6-27b` handles structured JSON output well
- Prompt engineering: add task extraction rules to priority prompt, return combined JSON

**Alternatives Considered**:
1. **Separate task extraction call**: Adds 1-3s latency, violates FR-011, doubles API cost
2. **Chained prompts**: Priority first, then tasks if action detected — still two calls
3. **Function calling**: Not supported uniformly across providers, adds complexity
4. **Batch prompt (all at once)**: Priority + tasks + summary in one call — summary quality
   may degrade when prompt is too long; summary is already working well separately

**Recommendation**: Combine priority + tasks + deadlines in one call. Keep summary
as a separate call (it's already working and has different output characteristics).

---

## Research Task 2: Task Data Structure in Prompt Output

**Decision**: Return tasks as structured objects within the combined prompt output.

**Output schema**:
```json
{
  "priority": "urgent",
  "confidence": 0.92,
  "explanation": "Message requests action with deadline tonight",
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
- Pydantic `AIAnalysisResult` validates structure automatically
- `tasks_extracted` as objects (not strings) enables rich task display
- `deadlines` as flat string array provides quick access without parsing tasks
- `requires_action` boolean helps UI decide whether to highlight task

**Alternatives Considered**:
1. **Tasks as strings only**: Loses deadline/priority info, can't display rich task cards
2. **Tasks in separate collection only**: Requires extra query for dashboard display
3. **No deadlines array**: Would need to extract from tasks every time; redundant

---

## Research Task 3: Storing Tasks in MongoDB

**Decision**: Dual-write — store in both message's embedded `ai_analysis.tasks_extracted`
AND in the `tasks` collection.

**Rationale**:
- **Embedded**: Dashboard reads message → immediately sees tasks (zero extra queries)
- **Collection**: Tasks page queries `tasks.find()` → fast, indexed, paginated
- **Dual-write cost**: One extra `insert_one` per message with tasks — negligible
- **Consistency**: Both locations updated in same request; if tasks collection write
  fails, message still has tasks embedded (graceful degradation)

**Implementation**:
```python
# In analyzer.py or routes/messages.py after analysis:
if ai_analysis.get("tasks_extracted"):
    for task in ai_analysis["tasks_extracted"]:
        task_doc = {
            "description": task["description"],
            "deadline": task.get("deadline"),
            "priority_indicator": task.get("priority_indicator"),
            "requires_action": task.get("requires_action", True),
            "status": "pending",
            "source_message_id": str(message_id),
            "source_message_preview": content[:100],
            "created_at": datetime.now(timezone.utc),
        }
        await tasks_collection.insert_one(task_doc)
```

**Alternatives Considered**:
1. **Collection only**: Dashboard would need `$lookup` aggregation — complex, slow
2. **Embedded only**: Tasks page would scan all messages — O(n) scan, slow
3. **Reference only**: Extra query for every task detail — N+1 problem

---

## Research Task 4: Prompt Engineering for Task Extraction

**Decision**: Add task extraction rules to the existing priority prompt template.
The prompt instructs the model to classify priority AND extract tasks in one pass.

**Key prompt additions**:
- Define what constitutes a task (clear verb, directed at recipient, specific)
- Define deadline rules (preserve exact wording, null if not mentioned)
- Define priority_indicator rules (only words from message, no invention)
- Provide examples of task extraction and non-extraction
- Emphasize: NEVER invent tasks or deadlines

**Rationale**:
- Existing priority prompt already handles structured JSON output
- Adding task rules to same prompt avoids extra API call
- qwen/qwen3.6-27b can handle the combined prompt length
- Examples in prompt improve accuracy (few-shot learning)

**Alternatives Considered**:
1. **Separate tasks.txt prompt**: Would need separate API call — violates single-call rule
2. **Post-processing with regex**: Unreliable for natural language task extraction
3. **Two-pass prompt**: First classify priority, then extract tasks if urgent — still two calls
