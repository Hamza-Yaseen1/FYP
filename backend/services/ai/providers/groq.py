import os
import re
import json
import logging
from groq import AsyncGroq
from .base import BaseLLMProvider, AIAnalysisResult

logger = logging.getLogger(__name__)

PROMPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts")

PRIORITY_PROMPT = """You are a message priority classifier AND task extractor. You have TWO jobs:
1. Classify the message priority
2. Extract actionable tasks with deadlines

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

CRITICAL RULES:
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

MESSAGE TO ANALYZE:
---
{message}
---

Return a JSON object with these fields:
- priority: "urgent", "important", "normal", or "low"
- confidence: 0.0 to 1.0
- explanation: 1-2 sentences explaining why
- tasks_extracted: array of task objects (empty array if no tasks)
- deadlines: array of deadline strings found in the message (empty array if none)

Return ONLY the JSON object, no other text."""

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
    text = text.strip()
    json_match = re.search(r"\{.*\}", text, re.DOTALL)
    if json_match:
        return json_match.group(0)
    return text


class GroqProvider(BaseLLMProvider):
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            logger.error("GROQ_API_KEY is not set!")
        self.client = AsyncGroq(api_key=api_key)
        self.model = "qwen/qwen3.6-27b"

    async def analyze(self, message: str) -> AIAnalysisResult:
        prompt = PRIORITY_PROMPT.format(message=message)

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3,
        )

        raw_content = response.choices[0].message.content
        cleaned = clean_response(raw_content)
        result = json.loads(cleaned)

        result["priority"] = normalize_priority(result.get("priority", "normal"))

        if not (0.0 <= result.get("confidence", 0) <= 1.0):
            result["confidence"] = 0.5

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

        result["tasks_extracted"] = tasks
        result["deadlines"] = result.get("deadlines", [])

        return AIAnalysisResult(**result)

    def _load_prompt(self, filename: str) -> str:
        path = os.path.join(PROMPTS_DIR, filename)
        with open(path, "r") as f:
            return f.read()

    async def generate_summary(self, message_content: str) -> str | None:
        try:
            prompt_template = self._load_prompt("summary.txt")
            prompt = prompt_template.replace("{message}", message_content)

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.3,
            )

            raw_content = response.choices[0].message.content
            cleaned = clean_response(raw_content)
            result = json.loads(cleaned)
            return result.get("summary")
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return None
