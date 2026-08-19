import os
import json
from openai import AsyncOpenAI
from .base import BaseLLMProvider, AIAnalysisResult


class OpenAIProvider(BaseLLMProvider):
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o-mini"

    async def analyze(self, message: str) -> AIAnalysisResult:
        prompt = f"""Analyze this message and return a JSON object with these fields:
- priority: "urgent", "important", "normal", or "low"
- confidence: 0.0 to 1.0
- summary: brief summary if message is long (>200 chars), null otherwise
- recommended_actions: list of suggested actions like "Reply", "Schedule", "Archive"
- tasks_extracted: list of actionable task descriptions found in the message
- deadlines: list of deadline strings found (e.g., "2026-08-22", "Friday")

Message: {message}

Return ONLY valid JSON, no other text."""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3,
        )

        result = json.loads(response.choices[0].message.content)
        return AIAnalysisResult(**result)
