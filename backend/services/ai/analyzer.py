from datetime import datetime, timezone
import logging
import traceback
from bson import ObjectId
from .providers.base import BaseLLMProvider, AIAnalysisResult
from .providers.groq import GroqProvider
from database import tasks_collection

logger = logging.getLogger(__name__)


def get_provider() -> BaseLLMProvider:
    return GroqProvider()


async def analyze_message(message_content: str, message_id: str = None) -> dict:
    provider = get_provider()

    try:
        logger.info("Starting AI analysis for message (%d chars)", len(message_content))
        result = await provider.analyze(message_content)
        logger.info("Priority analysis done: %s (%.0f%%)", result.priority, result.confidence * 100)

        summary = await provider.generate_summary(message_content)
        logger.info("Summary analysis done: %s", "OK" if summary else "null")

        analysis = {
            "priority": result.priority,
            "confidence": result.confidence,
            "explanation": result.explanation,
            "summary": summary,
            "recommended_actions": result.recommended_actions,
            "tasks_extracted": result.tasks_extracted,
            "deadlines": result.deadlines,
            "provider": "groq",
            "analyzed_at": datetime.now(timezone.utc),
            "status": "completed",
        }

        if message_id and result.tasks_extracted:
            preview = message_content[:80] + ("..." if len(message_content) > 80 else "")
            task_docs = []
            for task in result.tasks_extracted:
                task_docs.append({
                    "description": task["description"],
                    "deadline": task.get("deadline"),
                    "priority_indicator": task.get("priority_indicator"),
                    "requires_action": True,
                    "status": "pending",
                    "source_message_id": message_id,
                    "source_message_preview": preview,
                    "created_at": datetime.now(timezone.utc),
                })
            if task_docs:
                await tasks_collection.insert_many(task_docs)
                logger.info("Stored %d tasks for message %s", len(task_docs), message_id)

        return analysis
    except Exception as e:
        logger.error("AI analysis FAILED: %s", e)
        logger.error("Traceback: %s", traceback.format_exc())
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
