from datetime import datetime, timezone
import logging
from .providers.base import BaseLLMProvider, AIAnalysisResult
from .providers.openai import OpenAIProvider

logger = logging.getLogger(__name__)


def get_provider() -> BaseLLMProvider:
    return OpenAIProvider()


async def analyze_message(message_content: str) -> dict:
    provider = get_provider()

    try:
        result = await provider.analyze(message_content)
        return {
            "priority": result.priority,
            "confidence": result.confidence,
            "summary": result.summary,
            "recommended_actions": result.recommended_actions,
            "tasks_extracted": result.tasks_extracted,
            "deadlines": result.deadlines,
            "provider": "openai",
            "analyzed_at": datetime.now(timezone.utc),
            "status": "completed",
        }
    except Exception as e:
        logger.error(f"AI analysis failed: {e}")
        return {
            "priority": "pending",
            "confidence": 0.0,
            "summary": None,
            "recommended_actions": [],
            "tasks_extracted": [],
            "deadlines": [],
            "provider": "openai",
            "analyzed_at": None,
            "status": "failed",
        }
