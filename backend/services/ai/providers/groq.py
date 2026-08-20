import os
import json
from groq import AsyncGroq
from .base import BaseLLMProvider, AIAnalysisResult

PRIORITY_PROMPT = """You are a message priority classifier. Your ONLY job is to classify
a message into exactly one priority level.

PRIORITY LEVELS:

URGENT - Requires immediate attention within hours.
Evidence needed:
- Explicit time pressure: "right now", "immediately", "ASAP", "urgent"
- OR deadline within 24 hours
- AND clear consequence of delay

IMPORTANT - Requires attention within 1-3 days.
Evidence needed:
- Deadline within 1-7 days
- OR action required with some consequence of delay

NORMAL - Requires attention but not time-sensitive.
This is the DEFAULT when evidence is ambiguous.
- No explicit deadline
- OR deadline more than 7 days away
- OR action requested but not time-critical

LOW - Minimal or no immediate action needed.
- No action required
- OR automated/system message
- OR informational only

RULES:
- Base classification ONLY on message content
- Do NOT invent urgency that isn't present
- When uncertain, default to NORMAL
- Return EXACTLY one priority level

MESSAGE TO CLASSIFY:
---
{message}
---

Return a JSON object with these fields:
- priority: "urgent", "important", "normal", or "low"
- confidence: 0.0 to 1.0
- explanation: 1-2 sentences explaining why

Return ONLY the JSON object, no other text."""


class GroqProvider(BaseLLMProvider):
    def __init__(self):
        self.client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "qwen/qwen3.6-27b"

    async def analyze(self, message: str) -> AIAnalysisResult:
        prompt = PRIORITY_PROMPT.format(message=message)

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3,
        )

        result = json.loads(response.choices[0].message.content)
        return AIAnalysisResult(**result)
