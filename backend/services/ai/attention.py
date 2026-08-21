"""Needs Attention evaluation (Day 14).

Pure functions only — no LLM, no database. Rules mirror constitution
v1.3.0:
- R1: actionable task extracted AND near-term deadline detected
- R2: priority is urgent AND actionable task extracted
"""

NEAR_TERM_KEYWORDS = [
    "tonight",
    "today",
    "tomorrow",
    "asap",
    "right now",
    "immediately",
]

R1_REASON = "A task with a near deadline was detected."
R2_REASON = "An urgent message with an actionable task was detected."


def _has_tasks(analysis: dict) -> bool:
    return bool(analysis.get("tasks_extracted"))


def _near_term_deadline(analysis: dict) -> str | None:
    candidates = list(analysis.get("deadlines") or [])
    for task in analysis.get("tasks_extracted") or []:
        deadline = task.get("deadline")
        if deadline:
            candidates.append(deadline)

    for candidate in candidates:
        lowered = str(candidate).lower()
        if any(keyword in lowered for keyword in NEAR_TERM_KEYWORDS):
            return str(candidate)
    return None


def evaluate_attention(analysis: dict) -> dict:
    """Derive needs_attention + attention_reason from a completed analysis.

    Returns {"needs_attention": bool, "attention_reason": str} where the
    reason is non-empty exactly when the flag is True.
    """
    has_tasks = _has_tasks(analysis)

    if has_tasks and _near_term_deadline(analysis):
        return {"needs_attention": True, "attention_reason": R1_REASON}

    if has_tasks and analysis.get("priority") == "urgent":
        return {"needs_attention": True, "attention_reason": R2_REASON}

    return {"needs_attention": False, "attention_reason": ""}
