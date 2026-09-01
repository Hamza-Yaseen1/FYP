from datetime import datetime, timezone
import logging
import traceback
from bson import ObjectId
from .providers.base import BaseLLMProvider, AIAnalysisResult
from .providers.groq import GroqProvider
from .attention import evaluate_attention
from .routing import RoutingDecision
from database import tasks_collection

logger = logging.getLogger(__name__)


def get_provider() -> BaseLLMProvider:
    return GroqProvider()


def _gate_outputs(analysis: dict, routing: RoutingDecision | None) -> dict:
    """Clear outputs of agents the Orchestrator skipped.

    A skipped agent keeps its documented fallback (empty tasks/deadlines,
    empty recommendation) so nothing is ever invented by routing. The
    provided ``analysis`` dict is mutated and returned.
    """
    if routing is None:
        return analysis
    if not routing.run_summary:
        analysis["summary"] = None
    if not routing.run_task_extraction:
        analysis["tasks_extracted"] = []
    if not routing.run_deadline_detection:
        analysis["deadlines"] = []
    if not routing.run_recommended_action:
        analysis["recommended_action"] = ""
        analysis["recommended_actions"] = []
    return analysis


async def analyze_message(
    message_content: str,
    message_id: str = None,
    user_id: str = None,
    run_tasks: bool = True,
    routing: RoutingDecision | None = None,
    context_messages: list[dict] | None = None,
) -> dict:
    provider = get_provider()

    try:
        logger.info("Starting AI analysis for message (%d chars)", len(message_content))

        # Single LLM call: priority + tasks + deadlines + summary +
        # recommended action come back together. Context (≤5 earlier messages
        # in this thread) rides inside that SAME call — never a second round-trip.
        if context_messages is None:
            result = await provider.analyze(message_content)
        else:
            result = await provider.analyze(
                message_content, context=context_messages, current_message_id=message_id
            )

        recommendation = result.recommended_actions[0] if result.recommended_actions else ""

        analysis = {
            "priority": result.priority,
            "confidence": result.confidence,
            "explanation": result.explanation,
            "summary": result.summary,
            "recommended_action": recommendation,
            "recommended_actions": list(result.recommended_actions),
            "tasks_extracted": result.tasks_extracted,
            "deadlines": result.deadlines,
            "context_updates": list(getattr(result, "context_updates", [])),
            "provider": "groq",
            "analyzed_at": datetime.now(timezone.utc),
            "status": "completed",
        }

        # Gate skipped agents FIRST, then compute attention on the stored
        # state so flags reflect what is actually kept.
        _gate_outputs(analysis, routing)

        analysis.update(evaluate_attention(analysis))

        logger.info(
            "Pipeline stages complete for message %s (1 LLM call): priority=%s, summary=%s, tasks=%d, deadlines=%d, recommendation=%s, flagged=%s",
            message_id or "(unsaved)",
            analysis["priority"],
            bool(analysis["summary"]),
            len(analysis["tasks_extracted"]),
            len(analysis["deadlines"]),
            bool(analysis["recommended_action"]),
            analysis["needs_attention"],
        )

        if message_id and run_tasks and result.tasks_extracted:
            if not user_id:
                logger.warning(
                    "Skipping task creation for message %s: no user_id provided",
                    message_id,
                )
            else:
                preview = message_content[:80] + ("..." if len(message_content) > 80 else "")
                task_docs = []
                for task in result.tasks_extracted:
                    task_docs.append({
                        "user_id": user_id,
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
        error_text = str(e)
        if "429" in error_text or "rate_limit" in error_text.lower():
            logger.error(
                "AI analysis BLOCKED — Groq rate limit / daily token cap hit. "
                "Message stored with fallback values until quota resets. "
                "Provider said: %s",
                error_text[:300],
            )
        else:
            logger.error("AI analysis FAILED: %s", e, exc_info=True)
        return {
            "priority": "normal",
            "confidence": 0.0,
            "explanation": "Analysis failed, defaulting to normal priority",
            "summary": None,
            "recommended_action": "",
            "recommended_actions": [],
            "tasks_extracted": [],
            "deadlines": [],
            "context_updates": [],
            "provider": "groq",
            "analyzed_at": None,
            "status": "pending",
        }
