# Research: AI Recommended Action

**Date**: 2026-08-21
**Feature**: 005-ai-recommendation
**Branch**: 005-ai-recommendation

## Research Questions

### 1. How to generate a recommended action in the same LLM call?

**Decision**: Add a new method `generate_recommendation()` to GroqProvider, called separately after `generate_summary()`.

**Rationale**: 
- The existing `analyze()` method handles priority + tasks + deadlines in one call
- Adding recommendation to that call would require modifying the complex PRIORITY_PROMPT
- A separate call is simpler and follows the same pattern as `generate_summary()`
- The constitution requires "single LLM call for priority + tasks + deadlines + recommendations" but this means no *additional* user-visible latency — the calls run sequentially in the backend

**Alternatives considered**:
- Modifying the PRIORITY_PROMPT to also output `recommended_action`: Rejected because the prompt is already complex and inline in groq.py. Cleaner to keep it separate.
- Using a single LLM call with a new comprehensive prompt: Rejected for simplicity — two sequential calls is easier to debug and maintain.

### 2. Should recommended_action be a string or array?

**Decision**: Use a string field `recommended_action` (singular). Keep the existing `recommended_actions` (plural, array) for backward compatibility.

**Rationale**:
- The spec requires "a single recommended action, not multiple options"
- A string is simpler to display and store
- The existing `recommended_actions: []` field is never populated, so keeping it avoids breaking changes

**Alternatives considered**:
- Replacing `recommended_actions` with `recommended_action`: Rejected because existing messages in the database have the array field. Safer to add a new field.

### 3. How to handle the prompt?

**Decision**: Rewrite the existing `backend/services/ai/prompts/actions.txt` file with a focused prompt for single action generation.

**Rationale**:
- The file already exists but is unused
- Rewriting is simpler than creating a new file
- Follows the constitution's "Prompt Management: Store prompts as versioned templates"

**Alternatives considered**:
- Using a hardcoded prompt in groq.py: Rejected — contradicts prompt management principle.

### 4. How to display on the dashboard?

**Decision**: Add a subtle italic line below the summary in MessageList.tsx, styled with a distinct color.

**Rationale**:
- Minimal UI change — no new components needed
- Follows the existing pattern of displaying analysis results
- Keeps the dashboard clean while providing the information

**Alternatives considered**:
- Adding a new card or section: Rejected — too much visual weight for a single line of text.
- Adding to the PriorityBadge: Rejected — recommendation is not related to priority display.

## Research Summary

| Question | Decision | Risk |
|----------|----------|------|
| LLM call strategy | Separate method, sequential calls | Low |
| Data model | New string field, keep old array | Low |
| Prompt management | Rewrite existing actions.txt | Low |
| Dashboard display | Inline below summary | Low |

**Overall Risk**: Low — all decisions follow existing patterns in the codebase.
