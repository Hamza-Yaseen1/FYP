from datetime import datetime, timezone
import logging
from .providers.base import BaseLLMProvider, AIAnalysisResult
from .providers.groq import GroqProvider

logger = logging.getLogger(__name__)


def get_provider() -> BaseLLMProvider:
    return GroqProvider()


async def analyze_message(message_content: str) -> dict:
    provider = get_provider()

    try:
        result = await provider.analyze(message_content)
        return {
            "priority": result.priority,
            "confidence": result.confidence,
            "explanation": result.explanation,
            "summary": result.summary,
            "recommended_actions": result.recommended_actions,
            "tasks_extracted": result.tasks_extracted,
            "deadlines": result.deadlines,
            "provider": "groq",
            "analyzed_at": datetime.now(timezone.utc),
            "status": "completed",
        }
    except Exception as e:
        logger.error(f"AI analysis failed: {e}")
        return {
            "priority": "normal",
            "confidence": 0.0,
            "explanation": "Analysis failed, defaulting to normal priority",
            "summary": None,
            "recommended_actions": [],
            "tasks_extracted": [],
            "deadlines": [],
            "provider": "groq",
            "analyzed_at": None,
            "status": "pending",
        }
