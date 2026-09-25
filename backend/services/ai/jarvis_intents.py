"""JARVIS Phase 3 - natural-language intent layer (backend).

Two layers, both executed before Phase 1's legacy ``route_command``:

- ``detect_intent``: a deterministic superset of Phase 1's navigation + info
  matchers. It understands natural phrasings the legacy keyword matchers missed
  ("Do I have any new messages?", "What's waiting for me?", "I want to see my
  attention items.") and maps them to the same safe handlers the agent already
  owns. It never performs I/O and never invokes the LLM.
- ``llm_info_intent``: an *optional* Groq classifier for phrases the
  deterministic layer still cannot resolve. Security rule (Phase 3.9): the LLM
  may only label an intent from a fixed whitelist of *information* intents - it
  can never provide parameters, navigation targets, database operations, or any
  command the deterministic parsers already own. On any parse failure, unknown
  label, or network error the function silently degrades to ``None`` and the
  agent falls back to the Phase 1 general-chat path.

The agent alone decides whether a phrase reaches the LLM: it calls
``llm_info_intent`` only for messages Phase 1 classified as ``unknown``, so
greetings, help, and successful deterministic routes never cost an LLM call.
"""

import logging
import os
import re

from services.ai.providers.groq import GroqProvider, is_groq_available

logger = logging.getLogger(__name__)

# ── Shared navigation vocabulary (single source for agent + intent layer) ────

NAV_TARGETS = [
    (("inbox", "mail"), "/inbox", "your inbox"),
    (("task", "todo"), "/tasks", "your tasks"),
    (("attention",), "/attention", "your attention list"),
    (("connection", "gmail", "whatsapp"), "/connections", "your connections"),
    (("dashboard", "home", "overview"), "/dashboard", "the dashboard"),
    (("analytics", "charts", "reports"), "/analytics", "analytics"),
    (("settings", "profile", "account"), "/settings", "settings"),
]

NAV_VERBS = (
    "open",
    "navigate",
    "go to",
    "go into",
    "take me to",
    "show me",
    "bring up",
    "launch",
    "display",
    "visit",
    "switch to",
    "head to",
)

# Phase 3 natural-language superset: things people actually say out loud.
NATURAL_NAV_VERBS = NAV_VERBS + (
    "see",
    "view",
    "want to see",
    "want to view",
    "want to open",
    "want to go",
    "take me",
    "show",
    "get",
    "pull up",
    "open up",
    "navigate me to",
)

# ── Whitelisted information intents the LLM may return ──────────────────────

INFO_INTENT_KEYS = (
    "GET_UNREAD_MESSAGES",
    "GET_TODAYS_MESSAGES",
    "GET_PENDING_TASKS",
    "GET_ATTENTION",
    "GET_DASHBOARD_SUMMARY",
)

# ── Whitelisted message intents the LLM may return (Phase 6) ────────────────

MESSAGE_INTENT_KEYS = (
    "MESSAGE_COUNT",
    "LIST_MESSAGES",
    "SEARCH_MESSAGES",
    "SUMMARIZE_MESSAGES",
    "IMPORTANT_MESSAGES",
    "URGENT_MESSAGES",
    "GET_TODAYS_MESSAGES",
    "GET_YESTERDAYS_MESSAGES",
    "GET_MESSAGES_BY_DATE",
    "MESSAGE_BY_SENDER",
    "MESSAGE_BY_KEYWORD",
    "READ_MESSAGES",
    "FILTER_MESSAGES",
)


def _normalize(message: str) -> str:
    return " ".join(str(message or "").lower().split())


def _match_target(text: str):
    for keywords, path, label in NAV_TARGETS:
        if any(kw in text for kw in keywords):
            return path, label
    return None


def _is_bare_target(text: str) -> bool:
    """A very short utterance that names a screen ("inbox")."""
    return len(text.split()) <= 2


# ── Deterministic information matchers (most specific first) ────────────────

_TODAY_TOKENS = ("message", "inbox", "mail", "came in", "received", "recieved")
_UNREAD_PATTERNS = (
    r"\bunread\b",
    r"\bany new messages?\b",
    r"\bnew messages\b",
    r"\bany more messages?\b",
    r"\bhow many messages\b",
    r"\bdo i have messages\b",
    r"\bmessages waiting\b",
    r"\bnew mail\b",
    r"\bhow's (my |the )?inbox\b",
    r"\binbox\b",
)
_TASKS_PATTERNS = (
    r"\bpending tasks?\b",
    r"\bpending\b",
    r"\bto-do\b",
    r"\bto do\b",
    r"\btodos\b",
    r"\bhow many tasks?\b",
    r"\bany (open |incomplete |pending )?tasks?\b",
)
_ATTENTION_PHRASES = (
    "attention",
    "on my plate",
    "waiting for me",
    "waiting on me",
    "what should i work on",
    "what do i need to",
    "need to deal",
    "deal with",
    "handle first",
    "should i handle",
    "should i do first",
    "should i prioritize",
    "what's next for me",
    "whats next for me",
    "work on first",
    "the biggest priority",
)
_DASHBOARD_PHRASES = (
    "dashboard",
    "summary",
    "overview",
    "rundown",
    "big picture",
    "status report",
    "how's everything",
    "how is everything",
    "what's happening",
    "the gist",
)


def _todays_messages_query(text: str) -> bool:
    return "today" in text and any(token in text for token in _TODAY_TOKENS)


def _unread_query(text: str) -> bool:
    return any(re.search(pattern, text) for pattern in _UNREAD_PATTERNS)


def _pending_tasks_query(text: str) -> bool:
    return any(re.search(pattern, text) for pattern in _TASKS_PATTERNS)


def _attention_query(text: str) -> bool:
    return any(phrase in text for phrase in _ATTENTION_PHRASES)


def _dashboard_query(text: str) -> bool:
    return any(phrase in text for phrase in _DASHBOARD_PHRASES)


# ── Public intent detection ────────────────────────────────────────────────

def detect_intent(message: str) -> dict | None:
    """Return a structured intent or ``None`` (route with Phase 1 instead).

    ``None`` is reserved for phrases the legacy router owns (greetings, help,
    legacy navigation/info synonyms, unknown chatter), so routing behaviour for
    every existing Phase 1 command is preserved byte-for-byte.
    """
    text = _normalize(message)
    if not text:
        return None

    target = _match_target(text)
    has_nav_verb = any(verb in text for verb in NATURAL_NAV_VERBS)

    if has_nav_verb or target is not None and _is_bare_target(text):
        if target is not None:
            return {
                "intent": "NAVIGATE",
                "params": {"target": target[0], "label": target[1]},
            }

    if _todays_messages_query(text):
        return {"intent": "GET_TODAYS_MESSAGES", "params": {}}
    if _unread_query(text):
        return {"intent": "GET_UNREAD_MESSAGES", "params": {}}
    if _pending_tasks_query(text):
        return {"intent": "GET_PENDING_TASKS", "params": {}}
    if _attention_query(text):
        return {"intent": "GET_ATTENTION", "params": {}}
    if _dashboard_query(text):
        return {"intent": "GET_DASHBOARD_SUMMARY", "params": {}}

    return None


# ── Optional LLM intent classifier (whitelist-only, no DB access) ───────────

CLASSIFIER_PROMPT = (
    'You are the intent layer of a personal communication assistant. A user '
    'typed a request. Classify which of the available data intents it matches. '
    'Reply with ONLY JSON of the form {"intent": "GET_UNREAD_MESSAGES"}. The '
    'intent field must be exactly one of: GET_UNREAD_MESSAGES, '
    'GET_TODAYS_MESSAGES, GET_PENDING_TASKS, GET_ATTENTION, '
    'GET_DASHBOARD_SUMMARY, GENERAL_CHAT. Use GET_* only when the user asks '
    'about their own unread messages, messages received today, pending tasks, '
    'items needing their attention, or an overall dashboard summary. Anything '
    'else (small talk, greetings, or questions not about those four data '
    'sources) is GENERAL_CHAT.\n\nUser request: "%s"'
)


def _llm_configured() -> bool:
    # A key alone is not enough: during a circuit-breaker cooldown (daily
    # quota exhausted) Groq must not be consulted at all.
    return bool(os.getenv("GROQ_API_KEY")) and is_groq_available()


async def llm_info_intent(message: str) -> dict | None:
    """Label a previously-unknown phrase with a whitelisted info intent.

    Never raises and never invents parameters: only the pre-defined intent key
    from the LLM JSON is honoured; anything else degrades to ``None``.
    """
    if not _llm_configured():
        return None

    prompt = CLASSIFIER_PROMPT % str(message or "").strip()
    try:
        result = await GroqProvider().chat(prompt)
    except Exception as exc:
        logger.warning("JARVIS intent classifier failed: %s", exc)
        return None

    if not isinstance(result, dict):
        return None
    label = result.get("intent")
    if isinstance(label, str) and label in INFO_INTENT_KEYS:
        return {"intent": label, "params": {}}
    return None


# ── Optional LLM message intent classifier (whitelist-only, no DB access) ───

MESSAGE_CLASSIFIER_PROMPT = (
    'You are the message intent layer of a personal communication assistant. '
    'A user typed a request about their messages. Classify which of the '
    'available message intents it matches. Reply with ONLY JSON of the form '
    '{"intent": "MESSAGE_COUNT", "params": {"sender": "Marketing Team", "when": "today"}}. '
    'The intent field must be exactly one of: MESSAGE_COUNT, LIST_MESSAGES, '
    'SEARCH_MESSAGES, SUMMARIZE_MESSAGES, IMPORTANT_MESSAGES, URGENT_MESSAGES, '
    'GET_TODAYS_MESSAGES, GET_YESTERDAYS_MESSAGES, GET_MESSAGES_BY_DATE, '
    'MESSAGE_BY_SENDER, MESSAGE_BY_KEYWORD, READ_MESSAGES, FILTER_MESSAGES, '
    'GENERAL_CHAT. '
    'Params may include: "sender" (sender name), "keyword" (search term), '
    '"when" (today, yesterday, this week, last week, this month, last month, '
    'or a weekday), "count_only" (true for count-only requests), "list" (true for listing), '
    '"summarize" (true for summary requests). '
    'Use MESSAGE_BY_SENDER for "show me messages from X", MESSAGE_BY_KEYWORD for '
    '"search for X", FILTER_MESSAGES for combined filters. '
    'Anything not about the user\'s messages (small talk, greetings, general questions) '
    'is GENERAL_CHAT.\n\nUser request: "%s"'
)


async def llm_message_intent(message: str) -> dict | None:
    """Label a previously-unknown phrase with a whitelisted message intent.

    Never raises and never invents parameters beyond the whitelist: only the
    pre-defined intent key and allowed params from the LLM JSON are honoured;
    anything else degrades to ``None``.
    """
    if not _llm_configured():
        return None

    prompt = MESSAGE_CLASSIFIER_PROMPT % str(message or "").strip()
    try:
        result = await GroqProvider().chat(prompt)
    except Exception as exc:
        logger.warning("JARVIS message intent classifier failed: %s", exc)
        return None

    if not isinstance(result, dict):
        return None
    label = result.get("intent")
    if isinstance(label, str) and label in MESSAGE_INTENT_KEYS:
        params = result.get("params", {})
        # Validate params - only allow whitelisted keys
        allowed_params = {"sender", "keyword", "when", "count_only", "list", "summarize"}
        filtered_params = {k: v for k, v in params.items() if k in allowed_params}
        return {"intent": label, "params": filtered_params}
    return None


# ── Consolidated single-call classifier (Phase 3 + Phase 6) ─────────────────
#
# One ambiguous, non-app-vocabulary phrase must cost AT MOST ONE LLM call.
# This prompt asks the model to choose from BOTH whitelists (info intents and
# message intents) or GENERAL_CHAT. ``llm_intent`` then validates the label
# against those whitelists — anything else (hostile label, malformed JSON,
# provider failure, no key, breaker cooldown) degrades to ``None`` so the
# agent answers deterministically. It never invents parameters.

COMBINED_CLASSIFIER_PROMPT = (
    'You are the intent layer of a personal communication assistant. A user '
    'typed a request. Classify which available intent it matches. Reply with '
    'ONLY JSON of the form {"intent": "INTENT_NAME"} or, for message intents, '
    '{"intent": "INTENT_NAME", "params": {"sender": "..."}}. The intent field '
    'must be exactly one of: GET_UNREAD_MESSAGES, GET_TODAYS_MESSAGES, '
    'GET_PENDING_TASKS, GET_ATTENTION, GET_DASHBOARD_SUMMARY, MESSAGE_COUNT, '
    'LIST_MESSAGES, SEARCH_MESSAGES, SUMMARIZE_MESSAGES, IMPORTANT_MESSAGES, '
    'URGENT_MESSAGES, GET_YESTERDAYS_MESSAGES, GET_MESSAGES_BY_DATE, '
    'MESSAGE_BY_SENDER, MESSAGE_BY_KEYWORD, READ_MESSAGES, FILTER_MESSAGES, '
    'GENERAL_CHAT. Use the GET_* data intents only when the user asks about '
    'their own unread messages, messages received today, pending tasks, '
    'items needing attention, or an overall dashboard summary. Message '
    'params may be: "sender" (sender name), "keyword" (search term), "when" '
    '(today, yesterday, this week, last week, this month, last month, or a '
    'weekday), "count_only" (true for count-only requests), "list" (true for '
    'listing), "summarize" (true for summary requests). Use MESSAGE_BY_SENDER '
    'for "show me messages from X", SEARCH_MESSAGES for looking things up. '
    'Anything else (small talk, greetings, or questions not about those data '
    'sources) is GENERAL_CHAT.\n\nUser request: "%s"'
)


async def llm_intent(message: str) -> dict | None:
    """Label a previously-unknown phrase with ONE Groq call.

    The returned intent is validated against the info AND message whitelists,
    and ``params`` only ever contain the whitelisted keys. Any miss degrades
    to ``None`` — the caller routes deterministically or chats.
    """
    if not _llm_configured():
        return None

    prompt = COMBINED_CLASSIFIER_PROMPT % str(message or "").strip()
    try:
        result = await GroqProvider().chat(prompt)
    except Exception as exc:
        logger.warning("JARVIS intent classifier failed: %s", exc)
        return None

    if not isinstance(result, dict):
        return None
    label = result.get("intent")
    if not isinstance(label, str):
        return None
    if label in INFO_INTENT_KEYS:
        return {"intent": label, "params": {}}
    if label in MESSAGE_INTENT_KEYS:
        params = result.get("params", {})
        allowed_params = {"sender", "keyword", "when", "count_only", "list", "summarize"}
        if not isinstance(params, dict):
            params = {}
        filtered_params = {k: v for k, v in params.items() if k in allowed_params}
        return {"intent": label, "params": filtered_params}
    return None