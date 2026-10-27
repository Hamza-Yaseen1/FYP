"""JARVIS — voice assistant agent (backend).

Phase 1: deterministic command routing first, real application data second,
and the existing Groq integration third (general conversation only).

Phase 2 (actions) lives in ``jarvis_actions`` and is detected *before* Phase 1
routing so real agent actions (create/complete/delete tasks, message search,
attention analysis, reply drafting) win over the simpler Phase 1 matchers.
The two conflict-everything rules that keep routing reliable:

- navigation commands  -> structured ``action`` (never touches the LLM)
- information commands -> real, user-scoped reads of the messages/tasks
   collections, answered with concise deterministic replies (never invented)
- general conversation (greetings, help, unknown chatter) -> Groq when
   ``GROQ_API_KEY`` is configured, a static professional reply otherwise

Phase 3 (jarvis_intents) sits between Phase 2 and Phase 1: a deterministic
natural-language layer understands phrasings Phase 1's keyword matchers miss,
plus an optional whitelisted Groq intent label for phrases that would otherwise
fall to general chat. Greetings, help, and every pre-existing command keep
their exact replies.

Phase 4 (jarvis_messages) sits before Phase 2: a deterministic message-content
layer owns the *message* questions the earlier layers could not answer well
("how many messages do I have?", "what messages came in today?", "show me
yesterday's messages", "summarize my messages", "which messages are
urgent?"). It returns None for every phrase Phases 1-3 already own, so their
replies (and tests) stay byte-identical. Groq is consulted only for the
message summary, and only ever sees a digest of the user's own messages.

Phase 5 (conversation + context): general questions ("what is AI?") route to
the existing Groq chat integration when a key is configured, so they get a
natural answer instead of a static "don't support" reply. A tiny in-memory,
per-user record keeps the last few turns and is injected into the Groq prompt;
a ``last_data_topic`` marker (messages or tasks) gates pronoun follow-ups
("which ones?", "summarize them"), date follow-ups ("what about yesterday?",
"which day had more?"), corrections ("No, I mean …") and task-aware references
("which one is due first?", "delete that one" — always behind the signed
confirmation) onto the right deterministic layer. The conversational LLM never
executes actions, never queries the database, and never sees any user's data —
application behaviour stays fully deterministic.

Phase 6 (enhanced intelligence): Improved message filtering by sender,
combined date+sender+keyword filters, read-message enumeration, safe message
deletion with confirmation, and LLM-assisted intent classification for
ambiguous natural-language requests.
"""

import logging
import os
import re
from collections import deque
from datetime import datetime, timezone

from database import messages_collection, tasks_collection
from services.ai import jarvis_actions
from services.ai.jarvis_intents import (
    NAV_TARGETS,
    NAV_VERBS,
    detect_intent,
    llm_intent,
)
from services.ai.jarvis_messages import (
    detect_message_intent,
    range_when,
    resolve_context_follow_up,
    run_message_intent,
)
from services.ai.providers.groq import GroqProvider, is_groq_available

logger = logging.getLogger(__name__)

# ── Static copy that must not drift from the user-visible capabilities ─────

CAPABILITIES = (
    "I can open your inbox, tasks, attention, connections, dashboard, "
    "analytics, and settings. I can also tell you how many unread messages "
    "you have, what your pending tasks are, what needs your attention, and "
    "give you a dashboard summary. I can answer questions about your "
    "messages: how many you have, what came in today or yesterday, important "
    "or urgent messages, and a summary of what your recent messages cover. "
    "I can show messages from specific senders, search messages by keyword, "
    "read your messages aloud, and safely delete messages with confirmation."
)

GREETING_REPLY = (
    "At your service. I am JARVIS, your communication assistant. "
    "Tell me what you need — or say \"help\" to see what I can do."
)

UNKNOWN_REPLY = (
    f"I'm afraid I don't support that command yet. {CAPABILITIES}"
)

CONVERSATION_UNAVAILABLE_REPLY = (
    "I can handle your application tasks and message information, but my "
    "conversational AI service is currently unavailable."
)

# When the user's phrase carries application vocabulary, the deterministic
# layers own it — the LLM intent classifiers must never be consulted for it
# (their whitelist labels are for genuinely ambiguous, non-app phrasing only).
_APP_HINT_RE = re.compile(
    r"\b(?:unread|messages?|emails?|mails?|inbox|tasks?|to[- ]?dos?|attention|"
    r"dashboard|summary|overview|urgent|important|pending|sender|deadline|"
    r"priority|respond)\b",
    re.IGNORECASE,
)

ERROR_REPLY = (
    "I ran into an unexpected issue while answering. Please try again in a moment."
)

EMPTY_REPLY = (
    "I didn't catch a command. Press the microphone and try again, or type a command below."
)

JARVIS_SYSTEM_PROMPT = (
    "You are JARVIS, the personal assistant of the owner of a "
    "communication-management platform called Signal Desk. Be professional, "
    "concise, and a little formal. Reply in at most two short sentences. "
    'Respond with ONLY a JSON object of the form {"reply": "your reply text"}'
)

# ── Short conversation context (in-memory, per authenticated user) ─────────

_HISTORY_TURNS = 8
_DATA_RANGES = 2


class _ConversationContext:
    __slots__ = (
        "history",
        "last_data_topic",
        "last_message_intent",
        "ranges",
        "last_tasks",
    )

    def __init__(self) -> None:
        self.history = deque(maxlen=_HISTORY_TURNS)
        self.last_data_topic: str | None = None
        self.last_message_intent: dict | None = None
        self.ranges = deque(maxlen=_DATA_RANGES)
        self.last_tasks: list[dict] = []


_CONTEXTS: dict[str, _ConversationContext] = {}


def _get_context(user_id: str) -> _ConversationContext:
    ctx = _CONTEXTS.get(user_id)
    if ctx is None:
        ctx = _ConversationContext()
        _CONTEXTS[user_id] = ctx
    return ctx


def _remember_message_intent(ctx: _ConversationContext, intent: dict) -> None:
    """Remember the last message-data intent and any date span it covered.

    The span history (max two) lets "Which day had more?" / "Compare them."
    answer deterministically from the dates the user actually asked about.
    """
    ctx.last_message_intent = {"intent": intent.get("intent"), "params": intent.get("params") or {}}
    when = range_when(ctx.last_message_intent)
    if when:
        ctx.ranges.append({"when": when})


def _remember_tasks(ctx: _ConversationContext, tasks: list[dict]) -> None:
    """Remember the tasks shown in the last pending-task listing."""
    ctx.last_tasks = tasks or []


def _clip_text(text: str, limit: int = 240) -> str:
    text = " ".join(str(text or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _record_turn(user_id: str, message: str, reply: str, topic: str | None) -> None:
    """Stash the latest user/assistant turn plus the data-topic marker.

    ``last_data_topic == "messages"`` makes the next turn eligible for message
    follow-up resolution; anything else resets it so unrelated chatter never
    leaks context into a later question.
    """
    ctx = _get_context(user_id)
    ctx.history.append({"role": "user", "text": _clip_text(message)})
    if reply:
        ctx.history.append({"role": "assistant", "text": _clip_text(reply)})
    ctx.last_data_topic = topic


def _history_block(user_id: str) -> str:
    ctx = _CONTEXTS.get(user_id)
    if not ctx or not ctx.history:
        return ""
    return "\n".join(
        f"{'User' if turn['role'] == 'user' else 'JARVIS'}: {turn['text']}"
        for turn in ctx.history
    )


def _last_data_topic(user_id: str) -> str | None:
    ctx = _CONTEXTS.get(user_id)
    return ctx.last_data_topic if ctx else None


def _topic_for_intent(kind: str) -> str | None:
    """Which data-topic a Phase 3 structured intent opens for follow-ups.

    ``messages`` makes pronoun follow-ups ("which ones?", "summarize them") and
    date follow-ups eligible; ``tasks`` allows task-aware references ("which one
    is due first?", "delete that one"). Anything else resets the data topic so
    unrelated chatter never leaks context into a later question.
    """
    if kind in {"GET_TODAYS_MESSAGES", "GET_UNREAD_MESSAGES"}:
        return "messages"
    if kind == "GET_PENDING_TASKS":
        return "tasks"
    return None


def _topic_for_info(info: str) -> str | None:
    if info == "unread":
        return "messages"
    if info == "tasks":
        return "tasks"
    return None


_MESSAGE_ACTIONS = {
    "list_important_messages",
    "summarize_messages",
    "search_messages",
    "read_messages",
    "delete_messages",
    "filter_messages",
}

_ACTION_TO_INTENT = {
    "list_important_messages": "IMPORTANT_MESSAGES",
    "summarize_messages": "SUMMARIZE_MESSAGES",
    "search_messages": "LIST_MESSAGES",
    "read_messages": "READ_MESSAGES",
    "delete_messages": "DELETE_MESSAGES",
    "filter_messages": "FILTER_MESSAGES",
}


def _topic_for_action(action_type: str) -> str | None:
    """Message-data Phase 2 actions keep the conversation on the messages topic."""
    if action_type in _MESSAGE_ACTIONS:
        return "messages"
    if action_type == "list_completed_tasks":
        return "tasks"
    return None


# ── Intent model ────────────────────────────────────────────────────────────

# NAV_TARGETS / NAV_VERBS live in ``jarvis_intents`` (the single source shared
# with the Phase 3 natural-language layer) — imported at the top of this file.

INFO_MATCHERS = [
    ("dashboard", ("dashboard summary", "summary", "overview")),
    ("attention", ("attention",)),
    ("unread", ("unread", "inbox")),
    ("tasks", ("pending task", "task", "todo", "to do")),
]

GREETING_EXACT = {
    "hi",
    "hello",
    "hey",
    "hey there",
    "hi jarvis",
    "hello jarvis",
    "hey jarvis",
    "good morning",
    "good afternoon",
    "good evening",
}

HELP_MARKERS = (
    "help",
    "what can you do",
    "what can you help",
    "what do you do",
    "capabilities",
    "commands",
)


def route_command(message: str) -> dict:
    """Classify one command into a navigation / info / chat intent.

    Pure and deterministic — no I/O, no LLM. Returns a dict with a ``kind``
    plus the fields needed downstream (``target``/``label`` for navigation,
    ``info`` for information commands, or ``topic`` for chat).
    """
    text = _normalize(message)

    target = _match_target(text)
    has_nav_verb = any(verb in text for verb in NAV_VERBS)

    if has_nav_verb or target is not None and _is_bare_target(text):
        if target is not None:
            return {"kind": "navigation", "target": target[0], "label": target[1]}
        return {"kind": "chat", "topic": "unknown"}

    info = _match_info(text)
    if info is not None:
        return {"kind": "info", "info": info}

    if text in GREETING_EXACT or text.startswith("hello") or text.startswith("hey"):
        return {"kind": "chat", "topic": "greeting"}

    if any(marker in text for marker in HELP_MARKERS):
        return {"kind": "chat", "topic": "help"}

    return {"kind": "chat", "topic": "unknown"}


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


def _match_info(text: str):
    for info_key, keywords in INFO_MATCHERS:
        if any(kw in text for kw in keywords):
            return info_key
    return None


# ── Entry point ─────────────────────────────────────────────────────────────

async def process_command(user_id: str, message: str) -> dict:
    """Route one JARVIS command for an authenticated user.

    Never raises: every branch degrades to a safe static reply. The returned
    dict matches the ``/jarvis/chat`` response contract:
    ``{"reply": str, "action": {type, target, ...} | None, "used_ai": bool}``.

    Phase 2 actions (jarvis_actions) are detected first so their deterministic
    parsers win over Phase 1's navigation/info matchers; everything the parser
    does not claim keeps its exact Phase 1 behaviour.

    Phase 3 adds a natural-language layer between the two: ``detect_intent``
    (deterministic) runs before the legacy router and resolves natural phrasings
    that Phase 1 missed; ``llm_info_intent`` (whitelisted info labels only) is
    consulted for phrases Phase 1 would call unknown. Greetings, help, legacy
    navigation, and every existing Phase 1 command keep identical replies.

    Phase 4 (message content) runs first so the message questions the earlier
    layers could not answer well resolve deterministically; it returns None
    for every phrase Phases 1-3 own, so nothing below changes behaviour. When
    the raw phrase is unseen, ``resolve_message_follow_up`` maps short
    follow-ups ("which ones?", "summarize them") and corrections ("No, I mean
    …") onto the same whitelisted message intents — and only when the previous
    turn was a message question.

    Phase 5: everything unclaimed falls to general conversation, answered by
    Groq when configured (natural replies, current-turn context injected) or a
    clear availability note otherwise. Every turn (user + assistant text) is
    recorded in a small in-memory per-user buffer, purely as conversation text —
    the LLM never gains DB/action access from it.

    Phase 6 (enhanced intelligence): message delete detection (NOT task deletion),
    read-message enumeration, LLM-assisted message intent classification for
    ambiguous natural-language requests.

    Context resolution order (conversational Part 4): date-span and pronoun
    follow-ups are resolved against the user's own short context first, then the
    deterministic message-content matcher, then task-aware references ("which one
    is due first?", "delete that one" — the latter only ever asks for the signed
    confirmation). Real application data is read fresh and user-scoped every time;
    context never holds message bodies or another user's data.
    """
    if not message or not message.strip():
        return {"reply": EMPTY_REPLY, "action": None, "used_ai": False}

    ctx = _get_context(user_id)

    try:
        # Phase 4: Message content follow-ups (context-aware)
        msg_intent = resolve_context_follow_up(message, ctx)
        if msg_intent is None:
            msg_intent = detect_message_intent(message)
        if msg_intent is not None:
            reply = await run_message_intent(user_id, msg_intent)
            _remember_message_intent(ctx, msg_intent)
            _record_turn(user_id, message, reply["reply"], "messages")
            return reply

        # Phase 5: Task follow-ups (context-aware)
        task_reply = await _resolve_task_follow_up(user_id, message, ctx)
        if task_reply is not None:
            _record_turn(user_id, message, task_reply["reply"], "tasks")
            return task_reply

        # Phase 6: Message delete detection (MUST come before Phase 2 task deletion)
        msg_delete = _detect_message_delete(message, ctx)
        if msg_delete is not None:
            reply = await _handle_message_delete(user_id, msg_delete, ctx)
            _record_turn(user_id, message, reply["reply"], "messages")
            return reply

        # Phase 6: Read messages detection
        msg_read = _detect_read_messages(message)
        if msg_read is not None:
            reply = await _handle_read_messages(user_id, msg_read)
            _record_turn(user_id, message, reply["reply"], "messages")
            return reply

        # Phase 2: Actions (create/complete/delete tasks, search, summarize, etc.)
        phase2 = jarvis_actions.detect_action(message)
        if phase2 is not None:
            reply = await jarvis_actions.run_action(user_id, phase2)
            action_type = phase2.get("type")
            if action_type in _MESSAGE_ACTIONS:
                _remember_message_intent(
                    ctx, {"intent": _ACTION_TO_INTENT[action_type], "params": {}}
                )
            _record_turn(user_id, message, reply.get("reply", ""), _topic_for_action(action_type))
            return reply

        # Phase 3: Natural language intents (deterministic)
        nlu = detect_intent(message)
        intent = None
        if nlu is None:
            intent = route_command(message)

        if nlu is not None:
            reply = await _dispatch_intent(user_id, nlu)
            if nlu["intent"] in ("GET_TODAYS_MESSAGES", "GET_UNREAD_MESSAGES"):
                _remember_message_intent(
                    ctx, {"intent": nlu["intent"], "params": nlu.get("params") or {}}
                )
            _record_turn(
                user_id, message, reply["reply"], _topic_for_intent(nlu["intent"])
            )
            return reply

        # Phases 3 + 6 (consolidated, single classifier call): an ambiguous
        # phrase WITH NO application vocabulary gets at most ONE Groq call.
        # ``llm_intent`` checks the reply label against BOTH whitelists (info
        # + message), so every previously reachable label still resolves —
        # but one request can never spend two classifier round-trips. Any
        # miss/failure/cooldown degrades to the deterministic routes below.
        if (
            intent is not None
            and intent["kind"] == "chat"
            and intent.get("topic") == "unknown"
            and not _APP_HINT_RE.search(message)
        ):
            nlu = await llm_intent(message)
            if nlu is not None:
                if nlu["intent"] in (
                    "GET_UNREAD_MESSAGES",
                    "GET_TODAYS_MESSAGES",
                    "GET_PENDING_TASKS",
                    "GET_ATTENTION",
                    "GET_DASHBOARD_SUMMARY",
                ):
                    reply = await _dispatch_intent(user_id, nlu)
                    topic = _topic_for_intent(nlu["intent"])
                else:
                    reply = await _dispatch_message_intent(user_id, nlu)
                    topic = "messages"
                if nlu["intent"] in ("GET_TODAYS_MESSAGES", "GET_UNREAD_MESSAGES"):
                    _remember_message_intent(
                        ctx, {"intent": nlu["intent"], "params": nlu.get("params") or {}}
                    )
                _record_turn(user_id, message, reply["reply"], topic)
                return reply

        if intent["kind"] == "navigation":
            reply = {
                "reply": f"Opening {intent['label']} now.",
                "action": {"type": "navigation", "target": intent["target"]},
                "used_ai": False,
            }
            _record_turn(user_id, message, reply["reply"], None)
            return reply

        if intent["kind"] == "info":
            reply = await _handle_info(user_id, intent["info"])
            if intent["info"] == "unread":
                _remember_message_intent(
                    ctx, {"intent": "GET_UNREAD_MESSAGES", "params": {}}
                )
            _record_turn(
                user_id,
                message,
                reply["reply"],
                _topic_for_info(intent["info"]),
            )
            return reply

        # General conversation (greeting, help, unknown) - ALWAYS uses Groq when configured
        reply = await _handle_chat(user_id, message, intent.get("topic"))
        _record_turn(user_id, message, reply["reply"], None)
        return reply
    except Exception as exc:  # pragma: no cover - defensive last resort
        logger.exception("JARVIS command failed for user %s: %s", user_id, exc)
        return {"reply": ERROR_REPLY, "action": None, "used_ai": False}


async def process_confirmation(user_id: str, token: str, confirmed: bool = True) -> dict:
    """Validate a confirmation token and execute the pending action (Phase 2).

    Called by the /jarvis/chat route when the frontend round-trips the token
    after the user taps Confirm (or Cancel). The token is signed, bound to the
    authenticated user, and short-lived; invalid tokens degrade to a safe reply.
    """
    return await jarvis_actions.run_confirmation(user_id, token, confirmed)


# ── Phase 3 structured intents ──────────────────────────────────────────────

async def _dispatch_intent(user_id: str, nlu: dict) -> dict:
    """Execute one Phase 3 structured intent through safe, user-scoped handlers.

    The intent dict only ever carries a whitelisted label plus (for navigation)
    a target resolved deterministically — never DB operations or values produced
    by an LLM.
    """
    kind = nlu["intent"]

    if kind == "NAVIGATE":
        params = nlu["params"]
        return {
            "reply": f"Opening {params['label']} now.",
            "action": {"type": "navigation", "target": params["target"]},
            "used_ai": False,
        }

    if kind == "GET_TODAYS_MESSAGES":
        return await _handle_todays_messages(user_id)

    info_by_intent = {
        "GET_UNREAD_MESSAGES": "unread",
        "GET_PENDING_TASKS": "tasks",
        "GET_ATTENTION": "attention",
        "GET_DASHBOARD_SUMMARY": "dashboard",
    }
    info = info_by_intent.get(kind)
    if info is not None:
        return await _handle_info(user_id, info)

    return {"reply": UNKNOWN_REPLY, "action": None, "used_ai": False}


# ── Information commands (real, user-scoped data) ──────────────────────────

async def _handle_info(user_id: str, info: str) -> dict:
    if info == "unread":
        n = await messages_collection.count_documents(
            {"user_id": user_id, "status": "unread"}
        )
        return {"reply": _unread_reply(n), "action": None, "used_ai": False}

    if info == "tasks":
        tasks = await _fetch_pending_tasks(user_id)
        _remember_tasks(_get_context(user_id), tasks)
        return {"reply": _tasks_reply(tasks), "action": None, "used_ai": False}

    if info == "attention":
        items = await _fetch_attention_items(user_id)
        return {"reply": _attention_reply(items), "action": None, "used_ai": False}

    if info == "dashboard":
        summary = await _fetch_dashboard_summary(user_id)
        return {"reply": _dashboard_reply(summary), "action": None, "used_ai": False}

    return {"reply": UNKNOWN_REPLY, "action": None, "used_ai": False}


async def _handle_todays_messages(user_id: str) -> dict:
    summary = await _fetch_todays_summary(user_id)
    return {"reply": _todays_messages_reply(summary), "action": None, "used_ai": False}


async def _fetch_todays_summary(user_id: str) -> dict:
    """Count today's messages (UTC calendar day, the app-wide convention)."""
    now = datetime.now(timezone.utc)
    start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    query = {"user_id": user_id, "created_at": {"$gte": start_of_today}}
    total = await messages_collection.count_documents(query)
    unread = await messages_collection.count_documents(
        {**query, "status": "unread"}
    )
    important = await messages_collection.count_documents(
        {**query, "ai_analysis.priority": "important"}
    )
    urgent = await messages_collection.count_documents(
        {**query, "ai_analysis.priority": "urgent"}
    )
    return {"total": total, "unread": unread, "important": important, "urgent": urgent}


async def _fetch_pending_tasks(user_id: str, limit: int = 5) -> list[dict]:
    now = datetime.now(timezone.utc)
    query = {
        "user_id": user_id,
        "status": {"$ne": "completed"},
        "$or": [
            {"snoozed_until": {"$exists": False}},
            {"snoozed_until": {"$lte": now}},
        ],
    }
    cursor = tasks_collection.find(query).sort("created_at", -1).limit(limit)
    return await cursor.to_list(length=limit)


async def _fetch_attention_items(user_id: str, limit: int = 5) -> list[dict]:
    query = {"user_id": user_id, "ai_analysis.needs_attention": True}
    cursor = messages_collection.find(query).sort("created_at", -1).limit(limit)
    return await cursor.to_list(length=limit)


async def _fetch_dashboard_summary(user_id: str) -> dict:
    unread = await messages_collection.count_documents(
        {"user_id": user_id, "status": "unread"}
    )
    urgent = await messages_collection.count_documents(
        {"user_id": user_id, "ai_analysis.priority": "urgent"}
    )
    total = await messages_collection.count_documents({"user_id": user_id})
    attention = await messages_collection.count_documents(
        {"user_id": user_id, "ai_analysis.needs_attention": True}
    )
    pending_tasks = len(await _fetch_pending_tasks(user_id, limit=9))
    return {
        "total": total,
        "unread": unread,
        "urgent": urgent,
        "attention": attention,
        "pending_tasks": pending_tasks,
    }


# ── Task-aware conversation follow-ups (references, never guessed) ─────────

_TASK_DUE_FIRST_RE = re.compile(
    r"^\s*(?:which\s+one\s+is\s+due\s+first"
    r"|what['\u2019]?s\s+due\s+first"
    r"|which\s+(?:one\s+)?should\s+i\s+(?:do|start|tackle|handle)\s+(?:on\s+)?first"
    r"|which\s+one\s+is\s+(?:the\s+)?most\s+urgent)\s*[.!?]*$"
)

_TASK_DELETE_REF_RE = re.compile(
    r"^\s*(?:please\s+)?(?:delete|remove|erase|discard|drop|get rid of)\s+"
    r"(?:that\s+one|this\s+one|it|the\s+first\s+one|the\s+second\s+one|"
    r"the\s+third\s+one|the\s+last\s+one|the\s+next\s+one)\s*[.!?]*$"
)

_TASK_COMPLETE_REF_RE = re.compile(
    r"^\s*(?:please\s+)?(?:complete|finish|mark|check off|tick off)\s+"
    r"(?:that\s+one|this\s+one|it|the\s+first\s+one|the\s+second\s+one|"
    r"the\s+third\s+one|the\s+last\s+one|the\s+next\s+one)\s*[.!?]*$"
)

_TASK_CORRECTED_RE = re.compile(
    r"\b(?:completed|done|finished|pending|open)\b"
)

_DEADLINE_RANK = [
    ("asap", 0), ("now", 0), ("today", 0), ("soon", 0),
    ("tonight", 1), ("tomorrow", 1), ("end of the day", 2), ("end of day", 2),
    ("this week", 3), ("weekend", 4),
    ("friday", 5), ("thursday", 6), ("wednesday", 7), ("tuesday", 8), ("monday", 9),
    ("next week", 10), ("next month", 11),
]


def _deadline_rank(deadline: str | None) -> int:
    text = (deadline or "").strip().casefold()
    if not text:
        return 100
    for token, rank in _DEADLINE_RANK:
        if token in text:
            return rank
    return 50


def _earliest_due_task(tasks: list[dict]) -> dict:
    """Deterministic, safe pick among the user's own pending tasks."""
    def sort_key(task: dict):
        return (
            _deadline_rank(task.get("deadline")),
            (task.get("deadline") or "").strip().casefold(),
            str(task.get("created_at") or ""),
        )
    return sorted(tasks, key=sort_key)[0]


def _select_ref_task(tasks: list[dict], text: str) -> dict | None:
    """Resolve "that one" / "the first one" / "the last one" to a task.

    Returns None when the reference is ambiguous (a bare "that one" with several
    tasks in context) so the caller can ask for clarification instead of guessing.
    """
    if not tasks:
        return None
    if re.search(r"\bthe\s+first\s+one\b", text):
        return tasks[0]
    if re.search(r"\bthe\s+second\s+one\b", text) and len(tasks) > 1:
        return tasks[1]
    if re.search(r"\bthe\s+third\s+one\b", text) and len(tasks) > 2:
        return tasks[2]
    if re.search(r"\b(?:the\s+last\s+one|the\s+next\s+one)\b", text):
        return tasks[-1]
    if len(tasks) == 1:
        return tasks[0]
    return None


async def _resolve_task_follow_up(user_id: str, message: str, ctx: _ConversationContext) -> dict | None:
    """Resolve task-aware follow-ups from the user's own short context.

    - "which one is due first?" -> the deterministic earliest-deadline pick.
    - "delete that one" -> asks for the existing signed confirmation when the
      reference is unambiguous; otherwise asks which task. Never auto-deletes.
    - "No, I meant completed tasks." -> switches to the completed-task listing.

    Every read stays scoped by ``user_id``; task ids from the context are
    revalidated against the current user before any confirmation is minted.
    """
    text = _normalize(message)
    if not text:
        return None
    if ctx.last_data_topic == "messages":
        # A reference after a message conversation is about messages — the
        # task layer must not hijack it into a task deletion.
        return None
    if re.search(r"\bmessages?\b|\binbox\b", text):
        return None

    if re.search(r"^\s*(?:no|wait|actually|sorry|hold on)\b.{0,20}\bi\s+(?:mean|meant)\s+", text):
        if "tasks" in text or _TASK_CORRECTED_RE.search(text):
            if _TASK_CORRECTED_RE.search(text) and not re.search(r"\bpending\b", text):
                reply = await jarvis_actions.run_action(user_id, {"type": "list_completed_tasks", "params": {}})
                return reply
            tasks = await _fetch_pending_tasks(user_id)
            _remember_tasks(_get_context(user_id), tasks)
            return {"reply": _tasks_reply(tasks), "action": None, "used_ai": False}

    if _TASK_DUE_FIRST_RE.search(text):
        tasks = ctx.last_tasks or await _fetch_pending_tasks(user_id)
        if not tasks:
            return {"reply": "You have no pending tasks, so nothing is due first.", "action": None, "used_ai": False}
        chosen = _earliest_due_task(tasks)
        desc = (chosen.get("description") or "an unnamed task").strip()
        due = f" by {chosen['deadline']}" if chosen.get("deadline") else ""
        return {"reply": f"You should start with \"{desc}\"{due} first.", "action": None, "used_ai": False}

    deleting = _TASK_DELETE_REF_RE.search(text) is not None
    completing = _TASK_COMPLETE_REF_RE.search(text) is not None
    if deleting or completing:
        tasks = ctx.last_tasks or await _fetch_pending_tasks(user_id)
        task = _select_ref_task(tasks, text)
        if task is None:
            if not tasks:
                return {"reply": "I don't have a task in context to work with. Try \"show my tasks\" first.", "action": None, "used_ai": False}
            bites = "; ".join((t.get("description") or "an unnamed task").strip() for t in tasks[:5])
            return {"reply": f"Which task do you mean? Your pending tasks are: {bites}. Say the exact task name, or \"the first one\".", "action": None, "used_ai": False}

        params = {"task_id": str(task["_id"]), "name": (task.get("description") or "").strip() or None}
        if deleting:
            return await jarvis_actions.run_delete_task(user_id, params)
        return await jarvis_actions.run_complete_task(user_id, params)

    return None


# ── Phase 6: Message delete detection ────────────────────────────────────────
#
# Message deletion is confirmation-gated through the shared signed-token system
# (jarvis_actions.run_delete_messages + CONFIRM_EXECUTORS["delete_messages"]).
# Detection never claims task phrasing: every spec below requires a message
# word, so "delete my task call the vendor" keeps flowing to Phase 2 task
# deletion. Context references ("delete that one") resolve against the user's
# own last message intent and are gated by last_data_topic == "messages".

_DELETE_VERB = (
    r"(?:please\s+)?(?:delete|remove|erase|clear|wipe|discard|throw away|get rid of)"
)

_DELETE_STATUS_RE = re.compile(
    rf"^\s*{_DELETE_VERB}\s+(?:all\s+|every\s+)?(?:the\s+|my\s+)?"
    rf"(?P<status>unread|read)\s+(?:messages?|emails?|mails?)\s*$"
)

_DELETE_PRIORITY_RE = re.compile(
    rf"^\s*{_DELETE_VERB}\s+(?:all\s+|every\s+)?(?:the\s+|my\s+)?"
    rf"(?P<priority>urgent|important)\s+(?:messages?|emails?|mails?)\s*$"
)

_DELETE_WHEN_RE = re.compile(
    rf"^\s*{_DELETE_VERB}\s+(?:all\s+|every\s+)?(?:the\s+|my\s+)?"
    rf"(?P<span>today|yesterday)['\u2019]s\s+(?:messages?|emails?|mails?)\s*$"
    rf"|^\s*{_DELETE_VERB}\s+(?:all\s+|every\s+)?(?:the\s+|my\s+)?"
    rf"(?:messages?|emails?|mails?)\s+(?:from|for)\s+"
    rf"(?P<span2>today|yesterday|this\s+week|last\s+week|this\s+month|last\s+month|"
    rf"monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s*$"
)

_DELETE_FROM_RE = re.compile(
    rf"^\s*{_DELETE_VERB}\s+(?:all\s+|every\s+)?(?:the\s+|my\s+)?"
    rf"(?:only\s+|just\s+)?(?:messages?|emails?|mails?)\s+from\s+(?P<sender>.+?)\s*$"
)

_DELETE_TOPIC_RE = re.compile(
    rf"^\s*{_DELETE_VERB}\s+(?:all\s+|every\s+)?(?:the\s+|my\s+)?"
    rf"(?:messages?|emails?|mails?)\s+(?:about|regarding|concerning|mentioning|containing|matching)\s+"
    rf"(?P<keyword>.+?)\s*$"
)

_DELETE_FILTER_RE = re.compile(
    rf"^\s*{_DELETE_VERB}\s+(?P<filter>.+?)\s+(?:messages?|emails?|mails?)\s*$"
)

_DELETE_ALL_RE = re.compile(
    rf"^\s*{_DELETE_VERB}\s+(?:all\s+|every\s+)?(?:the\s+|my\s+)?"
    rf"(?:messages?|emails?|mails?|inbox)\s*$"
)

_DELETE_CONTEXT_RE = re.compile(
    r"^\s*(?:please\s+)?(?:delete|remove|erase|discard|throw away|get rid of)\s+"
    r"(?:that\s+one|this\s+one|it|them|those|these|that\s+message|this\s+message)\s*[.!?]*$"
)

_DELETE_SPAN_WORDS = (
    "this week", "last week", "this month", "last month",
    "today", "yesterday",
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
)


def _classify_delete_filter(value: str) -> dict | None:
    """Classify a filter captured before the message word into a delete spec.

    "delete the marketing team messages" -> sender; "delete the urgent
    messages" -> priority; "delete this week's messages" -> when; anything
    that isn't clearly one of those still resolves to a sender/keyword-like
    filter so the delete stays explicit and confirmation-gated.
    """
    cleaned = value.strip()
    while True:
        m = re.match(r"^\s*(?:all|every|the|my|these|those)(?=\s|$)", cleaned)
        if not m:
            break
        cleaned = cleaned[m.end():].strip()
    if not cleaned or not re.search(r"[A-Za-z]", cleaned):
        return {"type": "all"}
    if re.search(r"\burgent\b", cleaned):
        return {"type": "priority", "value": "urgent"}
    if re.search(r"\bimportant\b", cleaned):
        return {"type": "priority", "value": "important"}
    if re.search(r"\bunread\b", cleaned):
        return {"type": "status", "value": "unread"}
    if re.search(r"\bread\b", cleaned):
        return {"type": "status", "value": "read"}
    for span in _DELETE_SPAN_WORDS:
        if span in cleaned:
            return {"type": "when", "value": span}
    cleaned = cleaned.rstrip(" ,.!?;:'\"").strip()
    if not cleaned:
        return {"type": "all"}
    if re.search(r"\b(?:messages?|emails?|mails?|inbox)\b", cleaned):
        return {"type": "all"}
    return {"type": "sender", "value": cleaned}


def _params_from_last_message_intent(last_intent: dict | None) -> dict | None:
    """Map the last message intent's params onto a delete spec, or None."""
    if not last_intent:
        return None
    params = last_intent.get("params") or {}
    if params.get("sender"):
        return {"type": "sender", "value": params["sender"]}
    if params.get("keyword"):
        return {"type": "keyword", "value": params["keyword"]}
    if params.get("priority"):
        return {"type": "priority", "value": params["priority"]}
    if params.get("unread_only"):
        return {"type": "status", "value": "unread"}
    if params.get("when"):
        return {"type": "when", "value": params["when"]}
    return None


def _detect_message_delete(message: str, ctx: "_ConversationContext") -> dict | None:
    """Detect message deletion requests (confirmation-gated, user-scoped).

    Returns a delete spec, or None when the phrase is not a message deletion
    (task phrasing always falls through to Phase 2 / Phase 5 first).
    """
    text = _normalize(message)
    if not text:
        return None

    m = _DELETE_STATUS_RE.search(text)
    if m:
        return {"type": "status", "value": m.group("status")}

    m = _DELETE_PRIORITY_RE.search(text)
    if m:
        return {"type": "priority", "value": m.group("priority")}

    m = _DELETE_WHEN_RE.search(text)
    if m:
        span = (m.group("span") or m.group("span2") or "today").strip()
        return {"type": "when", "value": span}

    m = _DELETE_FROM_RE.search(text)
    if m:
        sender = m.group("sender").strip().rstrip(" ,.!?;:")
        if not sender:
            sender = None
        if sender:
            return {"type": "sender", "value": sender}

    m = _DELETE_TOPIC_RE.search(text)
    if m:
        keyword = m.group("keyword").strip().rstrip(" ,.!?;:")
        if keyword and not re.search(r"\b(?:messages?|emails?|mails?|inbox)\b", keyword):
            return {"type": "keyword", "value": keyword}

    m = _DELETE_ALL_RE.search(text)
    if m:
        return {"type": "all"}

    m = _DELETE_FILTER_RE.search(text)
    if m:
        spec = _classify_delete_filter(m.group("filter"))
        if spec is not None:
            return spec

    # "delete that one" is a message delete only when the last data topic was
    # messages; the task layer owns the identical phrase for task context.
    if _DELETE_CONTEXT_RE.search(text) and ctx.last_data_topic == "messages":
        return {"type": "context"}
    return None


def _message_bite_label(doc: dict) -> str:
    ai = doc.get("ai_analysis")
    summary = ai.get("summary") if isinstance(ai, dict) else None
    label = (
        (doc.get("subject") or "")
        or (doc.get("content") or "")
        or str(summary or "no text")
    )
    label = " ".join(str(label).split())
    if len(label) > 60:
        label = label[:57] + "..."
    return f"\"{label}\" from {doc.get('sender') or 'unknown'}"


async def _handle_message_delete(user_id: str, spec: dict, ctx: "_ConversationContext") -> dict:
    """Route a delete spec through the shared confirmation-gated pipeline."""
    if spec.get("type") == "context":
        params = _params_from_last_message_intent(ctx.last_message_intent)
        if params is None:
            docs = (
                await messages_collection.find({"user_id": user_id})
                .sort("created_at", -1)
                .to_list(length=5)
            )
            if not docs:
                return {
                    "reply": "I don't have a message in context to delete. Try \"show my messages\" first.",
                    "action": None,
                    "used_ai": False,
                }
            bites = "; ".join(_message_bite_label(doc) for doc in docs)
            return {
                "reply": (
                    "Which message do you mean? Your recent messages are: "
                    f"{bites}. Tell me the sender or subject and I'll delete exactly that one."
                ),
                "action": None,
                "used_ai": False,
            }
        return await jarvis_actions.run_delete_messages(user_id, params, require_single=True)
    return await jarvis_actions.run_delete_messages(user_id, spec)


# ── Phase 6: Read messages detection ─────────────────────────────────────────

_READ_MESSAGES_RE = re.compile(
    r"\b(?:read|go through)\b.{0,30}\b(?:messages?|emails?|mails?|inbox)\b"
    r"|\b(?:read|go through)\b.{0,10}\b(?:them|those|these)\b"
    r"|\bread\s+(?:my\s+)?(?:messages?|emails?|mails?)\b"
    r"|\bread\s+them\s+(?:one\s+by\s+one|out\s+loud|aloud)\b"
    r"|\b(?:read|tell me)\s+(?:what'?s\s+in|what\s+is\s+in)\s+(?:these|the|my)\s+(?:messages?|emails?|mails?)\b"
)


def _detect_read_messages(message: str) -> dict | None:
    """Detect requests to read messages aloud or list them one by one."""
    text = _normalize(message)
    if not text:
        return None
    
    if _READ_MESSAGES_RE.search(text):
        return {"type": "read_messages"}
    
    return None


async def _handle_read_messages(user_id: str, read_spec: dict) -> dict:
    """Handle requests to read messages - returns actual message content."""
    from database import messages_collection
    
    # Fetch recent messages (up to 10 for reading)
    docs = await messages_collection.find({"user_id": user_id}).sort("created_at", -1).limit(10).to_list(length=10)
    
    if not docs:
        return {
            "reply": "You have no messages to read.",
            "action": None,
            "used_ai": False,
        }
    
    total = await messages_collection.count_documents({"user_id": user_id})
    
    if total > 10:
        reply = f"You have {total} messages. I'll read the 10 most recent ones:\n\n"
    else:
        reply = f"You have {total} {_plural(total, 'message')}. I'll read them:\n\n"
    
    for i, doc in enumerate(docs, 1):
        sender = doc.get("sender") or "Unknown sender"
        subject = doc.get("subject")
        content = doc.get("content") or ""
        status = "unread" if doc.get("status") == "unread" else "read"
        
        line = f"{i}. From {sender} ({status})"
        if subject:
            line += f" - {subject}"
        if content:
            # Truncate content for reading
            short_content = " ".join(content.split())[:200]
            if len(content) > 200:
                short_content += "..."
            line += f": {short_content}"
        
        reply += line + "\n"
    
    if total > 10:
        reply += f"\n... and {total - 10} more messages."
    
    return {
        "reply": reply,
        "action": None,
        "used_ai": False,
    }


# ── Phase 6: LLM-assisted message intent dispatch ────────────────────────────

async def _dispatch_message_intent(user_id: str, nlu: dict) -> dict:
    """Execute a message intent from LLM classification.
    
    The intent dict only carries a whitelisted label plus parameters resolved
    deterministically — never DB operations or values produced by an LLM.
    """
    kind = nlu["intent"]
    params = nlu.get("params", {})
    
    # Map LLM message intents to Phase 4 handlers
    from services.ai.jarvis_messages import run_message_intent
    
    # Convert LLM intent format to Phase 4 format
    phase4_intent = {"intent": kind, "params": params}
    return await run_message_intent(user_id, phase4_intent)


# ── Deterministic reply builders (concise, professional) ───────────────────

def _plural(count: int, singular: str, plural: str | None = None) -> str:
    return singular if count == 1 else (plural or f"{singular}s")


def _unread_reply(count: int) -> str:
    if count == 0:
        return "You have no unread messages. Your inbox is clear."
    return (
        f"You have {count} unread {_plural(count, 'message')} in your inbox."
    )


def _tasks_reply(tasks: list[dict]) -> str:
    if not tasks:
        return "You have no pending tasks. You're all caught up."
    top = tasks[:3]
    pieces = []
    for task in top:
        description = task.get("description") or "an unnamed task"
        deadline = task.get("deadline")
        if deadline:
            description = f"{description} (by {deadline})"
        pieces.append(description)
    joined = "; ".join(pieces)
    if len(tasks) > 3:
        joined = f"{joined}; and {len(tasks) - 3} more"
    return f"You have {len(tasks)} pending {_plural(len(tasks), 'task')}: {joined}."


def _attention_reply(items: list[dict]) -> str:
    if not items:
        return "Nothing is currently flagged as needing your attention."
    senders = []
    for item in items[:3]:
        sender = item.get("sender") or "an unknown sender"
        if item.get("subject"):
            sender = f"{sender} (\"{item['subject']}\")"
        senders.append(sender)
    joined = ", ".join(senders)
    if len(items) > 3:
        joined = f"{joined}, and {len(items) - 3} more"
    return (
        f"You have {len(items)} item{'' if len(items) == 1 else 's'} needing "
        f"attention: {joined}."
    )


def _dashboard_reply(summary: dict) -> str:
    return (
        f"Here is your summary: {summary['total']} total messages, "
        f"{summary['unread']} unread, {summary['urgent']} urgent, "
        f"{summary['pending_tasks']} pending tasks, and "
        f"{summary['attention']} item{'' if summary['attention'] == 1 else 's'} "
        f"needing attention."
    )


def _todays_messages_reply(summary: dict) -> str:
    total = summary["total"]
    if total == 0:
        return "You have no messages today."
    pieces = [f"You received {total} {_plural(total, 'message')} today."]
    detail = []
    if summary["unread"]:
        detail.append(f"{summary['unread']} unread")
    if summary["important"]:
        detail.append(f"{summary['important']} important")
    if summary["urgent"]:
        detail.append(f"{summary['urgent']} urgent")
    if detail:
        pieces.append(" and ".join(detail) + ".")
    return " ".join(pieces)


# ── General conversation (Groq when configured, static fallback otherwise) ─

def _chat_fallback(topic: str | None) -> str:
    if topic == "help":
        return CAPABILITIES
    if topic == "greeting":
        return GREETING_REPLY
    return CONVERSATION_UNAVAILABLE_REPLY


def _llm_configured() -> bool:
    # A key alone is not enough: during a circuit-breaker cooldown Groq must
    # not be consulted, so JARVIS answers deterministically instead.
    return bool(os.getenv("GROQ_API_KEY")) and is_groq_available()


async def _handle_chat(user_id: str, message: str, topic: str | None) -> dict:
    """Handle general conversation using Groq when configured.
    
    When GROQ_API_KEY is set, ALL conversation topics (greeting, help, unknown)
    route through Groq for natural responses. Only when Groq is unavailable
    do we use static fallbacks.
    """
    if _llm_configured():
        prompt = f"{JARVIS_SYSTEM_PROMPT}"
        history = _history_block(user_id)
        if history:
            prompt += f"\n\nConversation history:\n{history}"
        prompt += f'\n\nUser command: "{message}"'
        try:
            result = await GroqProvider().chat(prompt)
            reply = result.get("reply") if isinstance(result, dict) else None
            if isinstance(reply, str) and reply.strip():
                return {"reply": reply.strip(), "action": None, "used_ai": True}
        except Exception as exc:
            logger.warning("JARVIS chat failed, using fallback: %s", exc)
    
    fallback = _chat_fallback(topic)
    return {"reply": fallback, "action": None, "used_ai": False}