import os
import re
import json
import logging
from groq import AsyncGroq
from .base import BaseLLMProvider, AIAnalysisResult
from ..context import build_context_block

logger = logging.getLogger(__name__)

PROMPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts")

MODEL_NAME = os.getenv("GROQ_MODEL", "qwen/qwen3.6-27b")

# Cap output tokens well under the free-tier OTPM limit (1000/min ~= 900+
# output tokens) so a single analysis never trips Groq's 429 "request too
# large" guard. With reasoning disabled the JSON answer is ~150-400 tokens.
MAX_OUTPUT_TOKENS = int(os.getenv("GROQ_MAX_OUTPUT_TOKENS", "700"))

# Single-call analysis prompt: priority + tasks + deadlines + summary +
# recommended action in ONE response. One message must never cost more
# than one LLM round-trip (constitution: single LLM call).
ANALYSIS_PROMPT = """You are a communication analysis engine. Analyze the message below and complete ALL FOUR jobs:

1. CLASSIFY PRIORITY
2. EXTRACT ACTIONABLE TASKS WITH DEADLINES
3. WRITE A ONE-SENTENCE SUMMARY
4. RECOMMEND ONE NEXT ACTION FOR THE RECIPIENT

PRIORITY LEVELS:

URGENT - Requires immediate attention within hours.
Evidence needed:
- Explicit time pressure: "right now", "immediately", "ASAP", "urgent"
- OR deadline within 24 hours ("tonight", "today", "right now")
- AND clear consequence of delay

IMPORTANT - Requires attention within 1-3 days.
Evidence needed:
- Deadline within 1-7 days ("tomorrow", "this week", "by Friday")
- OR action required with some consequence of delay

NORMAL - Requires attention but not time-sensitive.
This is the DEFAULT when evidence is ambiguous.
- No explicit deadline
- OR deadline more than 7 days away ("next week", "next month")
- OR action requested but not time-critical

LOW - Minimal or no immediate action needed.
- No action required
- OR automated/system message
- OR informational only

TASK EXTRACTION RULES:
A task is actionable when:
- It contains a clear verb directed at the recipient (send, review, submit, prepare, confirm, call, etc.)
- It's directed at the recipient (not what the sender will do)
- It's specific enough to act on

For each task, extract:
- description: Clear, concise action description
- deadline: The exact time expression from the message, or null if none
- priority_indicator: Words suggesting urgency from the message, or null
- requires_action: Always true

CRITICAL TASK RULES:
- Only extract tasks explicitly mentioned, never invent tasks
- "I'll send you the files tomorrow" is NOT a task for the recipient
- "FYI server down tomorrow" is NOT a task (informational)
- If no clear tasks exist, return empty array
- NEVER invent deadlines. If no deadline is mentioned, deadline MUST be null
- Preserve deadline wording exactly as stated ("Tonight", "ASAP", "next week")
- NEVER convert relative expressions to dates unless explicitly told the current date

DEADLINE DETECTION:
- "right now", "ASAP", "immediately" -> deadline: the expression itself, priority: urgent
- "today", "tonight" -> deadline: the expression itself, priority: urgent
- "tomorrow" -> deadline: "tomorrow", priority: important
- "this week", "by Friday" -> deadline: the expression itself, priority: important
- "next week", "next month" -> deadline: the expression itself, priority: normal
- "before the meeting" -> deadline: "before the meeting" (do NOT invent a date)
- No time expression -> deadline: null

SUMMARY RULES:
- One sentence, under 20 words
- Capture the core request or information
- Same language as the message

RECOMMENDED ACTION RULES:
- One sentence, verb-first, under 15 words
- Reflect only what the message actually asks the recipient to do
- Never invent actions not present in the message
- If no clear action exists, use "Review this message"
- Same language as the message

MESSAGE TO ANALYZE:
---
{message}
---

Return ONLY a JSON object with exactly these fields:
{{"priority": "urgent", "confidence": 0.9, "explanation": "1-2 sentences", "summary": "one sentence", "tasks_extracted": [{{"description": "...", "deadline": "...", "priority_indicator": "...", "requires_action": true}}], "deadlines": ["..."], "recommended_action": "verb-first sentence"}}"""

VALID_PRIORITIES = {"urgent", "important", "normal", "low"}

PRIORITY_ALIASES = {
    "high": "important",
    "medium": "normal",
    "low_priority": "low",
    "critical": "urgent",
    "very_important": "urgent",
    "somewhat_important": "important",
    "not_important": "low",
}


def normalize_priority(raw: str) -> str:
    p = raw.strip().lower()
    if p in VALID_PRIORITIES:
        return p
    if p in PRIORITY_ALIASES:
        return PRIORITY_ALIASES[p]
    for valid in VALID_PRIORITIES:
        if valid in p:
            return valid
    return "normal"


def clean_response(text: str) -> str:
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*$", "", text)
    text = text.strip()
    json_match = re.search(r"\{.*\}", text, re.DOTALL)
    if json_match:
        return json_match.group(0)
    return text


class GroqProvider(BaseLLMProvider):
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        self.model = MODEL_NAME
        if not api_key:
            logger.error("GROQ_API_KEY is not set! Analysis WILL fail.")
        else:
            logger.info("GroqProvider initialized with model=%s, key=%s...", self.model, api_key[:8])
        self.client = AsyncGroq(api_key=api_key)

    async def _complete(self, prompt: str) -> dict:
        """One LLM call returning parsed JSON. Errors propagate — no
        silent swallowing here."""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt + "\n/no_think"}],
            temperature=0.3,
            max_tokens=MAX_OUTPUT_TOKENS,
            # Qwen 3.6 27B reasons by default and burns its whole output
            # budget (and the Groq OTPM cap) on a "thinking" block that we
            # never surface. Disable reasoning and ask for strict JSON so
            # each analysis stays within one small, parseable response.
            reasoning_effort="none",
            response_format={"type": "json_object"},
        )
        raw_content = response.choices[0].message.content
        cleaned = clean_response(raw_content)
        return json.loads(cleaned)

    async def analyze(
        self,
        message: str,
        context: list[dict] | None = None,
        current_message_id: str | None = None,
    ) -> AIAnalysisResult:
        # NOTE: .replace, NOT .format — messages may contain braces.
        prompt = ANALYSIS_PROMPT
        block = build_context_block(context, current_message_id) if context else None
        if block:
            prompt = prompt.replace(
                "MESSAGE TO ANALYZE:", block + "\n\nMESSAGE TO ANALYZE:"
            )
        prompt = prompt.replace("{message}", message)

        result = await self._complete(prompt)

        priority = normalize_priority(str(result.get("priority", "normal")))
        confidence = result.get("confidence", 0.5)
        if not isinstance(confidence, (int, float)) or not (0.0 <= confidence <= 1.0):
            confidence = 0.5

        tasks_raw = result.get("tasks_extracted", [])
        if not isinstance(tasks_raw, list):
            tasks_raw = []
        tasks = []
        for t in tasks_raw:
            if isinstance(t, dict):
                tasks.append({
                    "description": str(t.get("description", "")).strip(),
                    "deadline": t.get("deadline"),
                    "priority_indicator": t.get("priority_indicator"),
                    "requires_action": True,
                })
            elif isinstance(t, str) and t.strip():
                tasks.append({
                    "description": t.strip(),
                    "deadline": None,
                    "priority_indicator": None,
                    "requires_action": True,
                })

        action = str(result.get("recommended_action") or "").strip()

        return AIAnalysisResult(
            priority=priority,
            confidence=confidence,
            explanation=result.get("explanation"),
            summary=result.get("summary"),
            recommended_actions=[action] if action else [],
            tasks_extracted=tasks,
            deadlines=result.get("deadlines", []) or [],
            context_updates=result.get("context_updates", []) or [],
        )

    def _load_prompt(self, filename: str) -> str:
        path = os.path.join(PROMPTS_DIR, filename)
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    async def generate_summary(self, message_content: str) -> str | None:
        """Legacy standalone call. The pipeline no longer uses this —
        kept only for backward compatibility."""
        try:
            prompt_template = self._load_prompt("summary.txt")
            prompt = prompt_template.replace("{message}", message_content)
            result = await self._complete(prompt)
            return result.get("summary")
        except Exception as e:
            logger.error("Summary generation failed: %s", e, exc_info=True)
            return None

    async def generate_recommendation(self, message_content: str) -> str:
        """Legacy standalone call. The pipeline no longer uses this —
        kept only for backward compatibility."""
        try:
            prompt_template = self._load_prompt("actions.txt")
            prompt = prompt_template.replace("{message}", message_content)
            result = await self._complete(prompt)
            return result.get("recommended_action", "")
        except Exception as e:
            logger.error("Recommendation generation failed: %s", e, exc_info=True)
            return ""
