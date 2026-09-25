import os
import re
import json
import time
import asyncio
import logging
from groq import (
    AsyncGroq,
    APIConnectionError,
    APITimeoutError,
    APIStatusError,
    RateLimitError,
)
from .base import BaseLLMProvider, AIAnalysisResult
from ..context import build_context_block

logger = logging.getLogger(__name__)

PROMPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts")

MODEL_NAME = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")

# Output-token budget for ONE analysis. Reasoning is disabled (see
# ``reasoning_effort="none"`` below), so the whole answer is a compact JSON
# object (~150-400 tokens incl. tasks). 400 leaves headroom while staying far
# under the free-tier OTPM limit (1000/min), so parallel analyses do not trip
# Groq's 429 "output tokens per minute" guard. NOTE: max_tokens only caps the
# OUTPUT; the prompt's input tokens are trimmed separately (see ``_digest`` /
# ``build_context_block`` / JARVIS history clipping) so we never bill unused
# context.
MAX_OUTPUT_TOKENS = int(os.getenv("GROQ_MAX_OUTPUT_TOKENS", "400"))

# ── Controlled 429 / rate-limit handling ────────────────────────────────────
# Two very different kinds of 429 exist, and they must be treated differently:
# - TRANSIENT (OTPM "output tokens per minute", connection blips, 5xx): retry
#   at most once, waiting never more than ~1s, then fall back gracefully.
# - DAILY QUOTA (TPD "tokens per day" with Limit/Used/Requested, daily limit):
#   NEVER retried — waiting 1s (or hours) cannot create quota. This error
#   trips the circuit breaker so the app stops hammering an exhausted API.
#
# The SDK's default retry (max_retries=2) sleeps for a full Retry-After (up to
# 60s), which is what caused the 5-25s stalls in the logs. We disable SDK
# retries and run our own bounded loop: respect Groq's Retry-After only when it
# is sane, cap every wait at 1s, and give up so the pipeline can fall back.
RETRY_ATTEMPTS = max(1, int(os.getenv("GROQ_RETRY_ATTEMPTS", "2")))
INITIAL_RETRY_DELAY = float(os.getenv("GROQ_INITIAL_RETRY_DELAY", "0.3"))
MAX_RETRY_WAIT = min(float(os.getenv("GROQ_MAX_RETRY_WAIT", "1.0")), 1.0)

# Circuit-breaker cooldown after a hard quota (TPD) error. During the cooldown
# NO Groq request is attempted; every call raises ``GroqUnavailableError`` so
# callers fall back instantly. After the cooldown a single probe request is
# allowed: success closes the breaker, a quota error re-opens it.
GROQ_COOLDOWN_SECONDS = float(os.getenv("GROQ_COOLDOWN_SECONDS", "600"))

# How many Groq calls may be in flight at once (analysis + JARVIS + summary).
# A tiny concurrency cap prevents a burst of ingested messages from tripping
# the OTPM budget all at once.
MAX_CONCURRENT_GROQ_CALLS = max(1, int(os.getenv("GROQ_MAX_CONCURRENT", "2")))

# Per-request timeout so a hung call cannot hold a limiter slot forever.
GROQ_TIMEOUT = float(os.getenv("GROQ_TIMEOUT", "30"))

# Retriable HTTP statuses for TRANSIENT failures (SDK raises APIStatusError for
# these). 429 is retried ONLY when it is not a TPD quota error
# (``_is_tpd_quota``) — everything else (400/401/403/404/422...) is a caller
# bug and must fail fast.
_RETRYABLE_STATUSES = {408, 409, 423, 425}

# Token-per-day / daily-quota markers. A 429 whose body/message contains these
# cannot be fixed by a retry and must open the circuit breaker immediately.
_TPD_RE = re.compile(r"tokens\s*per\s*day|\btpd\b", re.IGNORECASE)
_DAILY_QUOTA_RE = re.compile(
    r"\bdaily\b|\bper\s+day\b|\bquota\b", re.IGNORECASE
)

# Reused per event loop: tests spin up a fresh loop per asyncio.run while the
# app runs one long-lived loop, so the semaphore/lock are (re)created lazily
# per running loop and stay singletons in production.
_rate_limit_state: dict = {"loop": None, "semaphore": None}
_probe_lock_state: dict = {"loop": None, "lock": None}


class GroqUnavailableError(RuntimeError):
    """Raised when Groq is out of service (quota cooldown / no key).

    Callers treat this as "fall back now": it must never reach the frontend
    and never trigger another network attempt.
    """


# ── Circuit breaker (in-memory, process-local) ─────────────────────────────

_CIRCUIT: dict = {"unavailable_until": 0.0, "reason": None}


def _now() -> float:
    return time.monotonic()


def breaker_state() -> str:
    """One of ``"closed"`` (available), ``"open"`` (cooldown) or
    ``"half_open"`` (cooldown elapsed; one probe request allowed)."""
    until = _CIRCUIT["unavailable_until"]
    if until <= 0:
        return "closed"
    if _now() >= until:
        return "half_open"
    return "open"


def is_groq_available() -> bool:
    """True when new Groq requests are allowed right now.

    Guards the JARVIS deterministic layers and the background retry sweep so a
    cooldown costs zero LLM attempts instead of one per request.
    """
    return breaker_state() != "open"


def open_breaker(reason: str) -> None:
    """Mark Groq unavailable for ``GROQ_COOLDOWN_SECONDS`` (idempotent)."""
    if breaker_state() == "open":
        return
    _CIRCUIT["unavailable_until"] = _now() + GROQ_COOLDOWN_SECONDS
    _CIRCUIT["reason"] = reason
    logger.error(
        "Groq quota exhausted. Circuit breaker enabled for %ds. Using local fallback.",
        int(GROQ_COOLDOWN_SECONDS),
    )


def close_breaker() -> None:
    """Mark Groq available again (called when a probe request succeeds)."""
    if _CIRCUIT["unavailable_until"] > 0:
        logger.info("Groq recovered. Circuit breaker closed - AI back online.")
    _CIRCUIT["unavailable_until"] = 0.0
    _CIRCUIT["reason"] = None


def reset_breaker_for_tests() -> None:
    """Test helper: force the breaker back to ``"closed"``."""
    _CIRCUIT["unavailable_until"] = 0.0
    _CIRCUIT["reason"] = None


def _get_probe_lock() -> asyncio.Lock:
    """Serializes probe requests so only ONE test request crosses half-open."""
    loop = asyncio.get_running_loop()
    if _probe_lock_state["lock"] is None or _probe_lock_state["loop"] is not loop:
        _probe_lock_state["loop"] = loop
        _probe_lock_state["lock"] = asyncio.Lock()
    return _probe_lock_state["lock"]


def _acquire_limiter() -> asyncio.Semaphore:
    """Return the shared concurrency semaphore for the running loop."""
    loop = asyncio.get_running_loop()
    if _rate_limit_state["semaphore"] is None or _rate_limit_state["loop"] is not loop:
        _rate_limit_state["loop"] = loop
        _rate_limit_state["semaphore"] = asyncio.Semaphore(MAX_CONCURRENT_GROQ_CALLS)
    return _rate_limit_state["semaphore"]


def _error_text(exc: BaseException) -> str:
    """Text of a provider error incl. the parsed JSON body (no headers/keys)."""
    text = str(exc) or ""
    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        err = body.get("error")
        if isinstance(err, dict):
            text = " ".join(
                part for part in (text, err.get("message"), err.get("type")) if part
            )
        else:
            text = f"{text} {body}"
    elif body is not None:
        text = f"{text} {body}"
    return text


def _is_tpd_quota(exc: BaseException) -> bool:
    """True when a 429 means the DAILY token-per-day quota is exhausted.

    TPD cannot be fixed by retrying a few seconds later (it resets on the next
    day), so callers must skip retries and trip the circuit breaker instead.
    """
    if not isinstance(exc, APIStatusError):
        return False
    text = _error_text(exc)
    if not text:
        return False
    if _TPD_RE.search(text):
        return True
    if _DAILY_QUOTA_RE.search(text) and re.search(
        r"\b(?:limit|used|requested|exceeded|exhausted)\b", text, re.IGNORECASE
    ):
        return True
    return False


def _is_retryable(exc: BaseException) -> bool:
    """True only for TRANSIENT failures worth one short retry.

    A TPD 429 is deliberately NOT retryable: it is a hard daily-quota error
    that also trips the circuit breaker.
    """
    if isinstance(exc, (APITimeoutError, APIConnectionError)):
        return True
    if isinstance(exc, APIStatusError):
        if exc.status_code == 429:
            return not _is_tpd_quota(exc)
        return exc.status_code in _RETRYABLE_STATUSES or exc.status_code >= 500
    return False


def _retry_wait(exc: BaseException, attempt: int) -> float:
    """Backoff for one retry attempt, bounded by ``MAX_RETRY_WAIT`` (≤1s).

    Respects Groq's ``Retry-After`` header when present but caps it so we never
    block for tens of seconds and the user always gets a fallback fast;
    otherwise exponential backoff from ``INITIAL_RETRY_DELAY``.
    """
    wait = INITIAL_RETRY_DELAY * (2 ** attempt)
    if isinstance(exc, RateLimitError) and exc.response is not None:
        try:
            header = exc.response.headers.get("retry-after")
            if header is not None and float(header) > 0:
                wait = float(header)
        except (TypeError, ValueError, AttributeError):
            pass
    return min(wait, MAX_RETRY_WAIT)


def _apply_circuit_rules(exc: BaseException | None) -> None:
    """Open the breaker when a final failure is a daily-quota (TPD) error."""
    if exc is not None and _is_tpd_quota(exc):
        open_breaker("tokens_per_day")


# Single-call analysis prompt: priority + tasks + deadlines + summary +
# recommended action in ONE response. One message must never cost more
# than one LLM round-trip (constitution: single LLM call).
ANALYSIS_PROMPT = """You are a communication analysis engine. Analyze the message below and complete ALL FOUR jobs:

1. CLASSIFY PRIORITY
2. EXTRACT ACTIONABLE TASKS WITH DEADLINES
3. WRITE A ONE-SENTENCE SUMMARY
4. RECOMMEND ONE NEXT ACTION FOR THE RECIPIENT

OUTPUT FORMAT RULES (STRICT):
- Return ONLY ONE compact JSON object. NEVER include reasoning, chain-of-thought, explanations, markdown, or any text inside or outside the JSON.
- Every field must be SHORT and concrete. Do not be verbose.
- "explanation": at most one short sentence (under 15 words).
- "summary": one sentence, under 20 words.
- "recommended_action": one verb-first sentence, under 15 words.
- "tasks_extracted" and "deadlines": use [] when there is nothing to report — never null, never omit.

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

Return ONLY a compact JSON object with exactly these fields (no other keys, no text outside):
{{"priority": "urgent", "confidence": 0.9, "explanation": "short reason", "summary": "one sentence", "tasks_extracted": [{{"description": "concise action", "deadline": "expression or null", "priority_indicator": "word or null", "requires_action": true}}], "deadlines": ["expression"], "recommended_action": "verb-first sentence"}}"""

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
    text = re.sub(r" thinking.*? response", "", text, flags=re.DOTALL)
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
            # NEVER log any part of the API key.
            logger.info(
                "GroqProvider initialized with model=%s (API key configured)",
                self.model,
            )
        # max_retries=0: the SDK's automatic retries sleep for Groq's full
        # Retry-After (5-25s+); we run our own bounded retry loop instead.
        self.client = AsyncGroq(
            api_key=api_key, max_retries=0, timeout=GROQ_TIMEOUT
        )

    async def _call_once(self, prompt: str) -> dict:
        """A single transport attempt: one API call, parsed JSON result.

        No retries, no circuit logic — just the one call under the shared
        concurrency cap. Raising here lets ``_complete``/``_probe_once`` apply
        their retry and breaker policy uniformly.
        """
        async with _acquire_limiter():
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt + "\n/no_think"}],
                temperature=0.3,
                max_tokens=MAX_OUTPUT_TOKENS,
                # Disable reasoning entirely for classification /
                # extraction: no chain-of-thought, no long thinking
                # blocks, minimal output tokens. The JSON answer is
                # produced directly and stays within budget.
                reasoning_effort="none",
                response_format={"type": "json_object"},
            )
        raw_content = response.choices[0].message.content
        cleaned = clean_response(raw_content)
        return json.loads(cleaned)

    async def _complete(self, prompt: str) -> dict:
        """One LLM call with circuit-breaker + bounded transient retry.

        Policy (showcase-safe):
        - breaker OPEN  -> raise ``GroqUnavailableError`` instantly, no API call.
        - breaker half-open (cooldown elapsed) -> ONE probe request via
          ``_probe_once``; success closes the breaker, a TPD error re-opens it.
        - normal (closed) -> one call; a TRANSIENT failure (OTPM 429, 408/409/
          5xx, connection/timeout) is retried at most once with a ≤1s wait; a
          TPD 429 is never retried and opens the breaker.
        """
        state = breaker_state()
        if state == "open":
            raise GroqUnavailableError(
                "Groq is in cooldown after a quota error; using local fallback."
            )
        if state == "half_open":
            return await self._probe_once(prompt)

        last_error: BaseException | None = None
        for attempt in range(RETRY_ATTEMPTS):
            try:
                return await self._call_once(prompt)
            except Exception as exc:
                last_error = exc
                if not _is_retryable(exc) or attempt + 1 >= RETRY_ATTEMPTS:
                    break
                wait = _retry_wait(exc, attempt)
                logger.warning(
                    "Groq API transient failure on attempt %d/%d (%s): retrying in %.2fs",
                    attempt + 1,
                    RETRY_ATTEMPTS,
                    type(exc).__name__,
                    wait,
                )
                await asyncio.sleep(wait)
        _apply_circuit_rules(last_error)
        raise last_error

    async def _probe_once(self, prompt: str) -> dict:
        """Single test request allowed after the cooldown elapsed.

        Guarded by a per-loop lock so only ONE probe crosses while half-open;
        other arrivals wait and then either observe a recovered (closed)
        breaker or fail fast on a re-opened one.
        """
        async with _get_probe_lock():
            if breaker_state() == "open":
                raise GroqUnavailableError(
                    "Groq is in cooldown after a quota error; using local fallback."
                )
            try:
                result = await self._call_once(prompt)
                close_breaker()
                return result
            except Exception as exc:
                last_error: BaseException = exc
                if not _is_tpd_quota(exc) and _is_retryable(exc):
                    await asyncio.sleep(_retry_wait(exc, 0))
                    try:
                        result = await self._call_once(prompt)
                        close_breaker()
                        return result
                    except Exception as exc2:
                        last_error = exc2
                _apply_circuit_rules(last_error)
                raise last_error

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

    async def chat(self, prompt: str) -> dict:
        """One-shot assistant chat completion returning parsed JSON (JARVIS).

        Reuses ``_complete`` (the transport/JSON handling above) so API-key
        handling, model selection, reasoning control, circuit breaking and
        output-token budgeting stay in one place. The caller composes a prompt
        that asks for a ``{"reply": "..."}`` JSON object and reads
        ``result["reply"]``. Always returns a dict (`{}` on any failure) and
        NEVER re-throws: callers degrade to their deterministic fallback.
        """
        try:
            return await self._complete(prompt)
        except Exception as exc:
            logger.warning(
                "JARVIS chat completion failed, using fallback: %s",
                _error_text(exc)[:200],
            )
            return {}

    async def generate_summary(self, message_content: str) -> str | None:
        """Legacy standalone call. The pipeline no longer uses this —
        kept only for backward compatibility."""
        try:
            prompt_template = self._load_prompt("summary.txt")
            prompt = prompt_template.replace("{message}", message_content)
            result = await self._complete(prompt)
            return result.get("summary")
        except Exception as exc:
            logger.warning("Summary generation failed: %s", _error_text(exc)[:200])
            return None

    async def generate_recommendation(self, message_content: str) -> str:
        """Legacy standalone call. The pipeline no longer uses this —
        kept only for backward compatibility."""
        try:
            prompt_template = self._load_prompt("actions.txt")
            prompt = prompt_template.replace("{message}", message_content)
            result = await self._complete(prompt)
            return result.get("recommended_action", "")
        except Exception as exc:
            logger.warning("Recommendation generation failed: %s", _error_text(exc)[:200])
            return ""