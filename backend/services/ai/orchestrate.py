"""AI Orchestration (Day 24).

``process_message`` is the single entry point for the AI pipeline: every
inbound message (REST create, WhatsApp webhook, simulate) funnels through
here, never calling ``analyze_message`` directly. It:
1. decides routing (rule-based, zero cost),
2. short-circuits trivial / no-content messages to deterministic defaults
   with ZERO AI calls,
3. runs one combined analysis call for the selected agent subset otherwise,
4. gates outputs to that subset (inside ``analyze_message``),
5. attaches an explainable routing record to the result on every path.
"""

import logging
from datetime import datetime, timezone

from .analyzer import analyze_message
from .routing import RoutingDecision, decide_routing

logger = logging.getLogger(__name__)

TRIVIAL_EXPLANATION = (
    "Trivial message - deep analysis skipped by orchestrator."
)


def _routing_record(routing: RoutingDecision, llm_call_used: bool) -> dict:
    if not routing.needs_analysis:
        return {
            "agents_run": [],
            "agents_skipped": [],
            "skip_reason": routing.reason,
            "triggers": [],
            "llm_call_used": False,
            "decided_at": datetime.now(timezone.utc),
        }
    return {
        "agents_run": routing.agents_run(),
        "agents_skipped": routing.agents_skipped(),
        "skip_reason": routing.reason,
        "triggers": routing.triggers,
        "llm_call_used": bool(llm_call_used),
        "decided_at": datetime.now(timezone.utc),
    }


def _deterministic_defaults(
    routing: RoutingDecision, message_type: str, content: str
) -> dict:
    """Deterministic result for cheap paths — no provider call.

    Two variants, both attaching the routing record with ``llm_call_used``
    false:
    - no analyzable content / media-only  -> ``status="skipped"`` stub so the
      Dashboard inbox and ``get_filter_counts`` keep working;
    - trivial messages                      -> an honest ``"completed"`` result
      (Priority normal, Summary echoing the content, nothing else) so the
      decision is explainable without an LLM round-trip.
    """
    if not routing.needs_analysis:
        return {
            "priority": "normal",
            "confidence": 0.5,
            "explanation": None,
            "summary": None,
            "recommended_action": "",
            "recommended_actions": [],
            "tasks_extracted": [],
            "deadlines": [],
            "needs_attention": False,
            "attention_reason": "",
            "provider": "rule-based",
            "analyzed_at": None,
            "status": "skipped",
            "routing": _routing_record(routing, llm_call_used=False),
        }

    return {
        "priority": "normal",
        "confidence": 0.5,
        "explanation": TRIVIAL_EXPLANATION,
        "summary": content or None,
        "recommended_action": "",
        "recommended_actions": [],
        "tasks_extracted": [],
        "deadlines": [],
        "needs_attention": False,
        "attention_reason": "",
        "provider": "rule-based",
        "analyzed_at": datetime.now(timezone.utc),
        "status": "completed",
        "routing": _routing_record(routing, llm_call_used=False),
    }


async def process_message(
    content: str, message_id: str = None, user_id: str = None, message_type: str = "text"
) -> dict:
    """Route one message through the Orchestrator and return the combined result.

    Never raises: ``analyze_message`` degrades to a pending fallback, and
    trivial / no-content messages short-circuit into deterministic defaults.
    A routing record is attached on every path.
    """
    routing = decide_routing(content, message_type)
    logger.info(
        "AI routing: message_id=%s reason=%s llm_call=%s agents_run=%s",
        message_id or "(unsaved)",
        routing.reason,
        routing.needs_llm,
        routing.agents_run(),
    )

    if not routing.needs_analysis or not routing.needs_llm:
        return _deterministic_defaults(routing, message_type, content)

    analysis = await _analyze_with_fallback(
        content, message_id=message_id, user_id=user_id, routing=routing
    )
    analysis["routing"] = _routing_record(routing, llm_call_used=True)
    return analysis


async def _analyze_with_fallback(
    content: str, message_id: str = None, user_id: str = None, routing: RoutingDecision = None
) -> dict:
    """Run the single combined analysis, guaranteed to return a dict.

    ``analyze_message`` degrades provider failures to a ``status="pending"``
    fallback itself, but provider *construction* (``get_provider``) is not
    guarded there. This wrapper contains that too so the caller can always
    attach its routing record — failure and skip stay distinguishable and a
    provider-construction error can never crash a message endpoint.
    """
    try:
        return await analyze_message(
            content,
            message_id=message_id,
            user_id=user_id,
            run_tasks=routing.run_task_extraction,
            routing=routing,
        )
    except Exception as exc:
        logger.error(
            "AI analysis crashed for %s: %s", message_id or "(unsaved)", exc
        )
        return {
            "priority": "normal",
            "confidence": 0.0,
            "explanation": "Analysis failed, defaulting to normal priority",
            "summary": None,
            "recommended_action": "",
            "recommended_actions": [],
            "tasks_extracted": [],
            "deadlines": [],
            "provider": "groq",
            "analyzed_at": None,
            "status": "pending",
        }