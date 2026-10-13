"""JARVIS Phase 2 — real agent actions (backend).

Extends Phase 1's deterministic routing with safe, actionable commands:

- task actions:     create / complete / delete / list (completed) tasks
- message actions:  search (by sender / keyword) / summarize unread /
                    list important messages
- attention analysis: rank what to handle first and explain *why* a message
                      is important, using stored ``ai_analysis`` data only
- reply drafting:   compose a professional draft (never auto-sent)

Confirmation model
------------------
Destructive or externally-visible actions (``create_task``, ``delete_task``)
never execute straight away. Instead they return an action of type
``request_confirmation`` carrying a short-lived, signed confirmation token
(HS256, bound to the authenticated user, ~2 minute expiry). The frontend shows
the pending action with Confirm/Cancel buttons; Confirm round-trips the token
back to ``run_confirmation`` which re-validates it and only then executes.

Security
--------
Every read/write is scoped by the authenticated ``user_id`` resolved from the
session — a user-supplied id is never trusted. All matchers are deterministic
so the assistant never has to parse an LLM's natural-language output; Groq is
used (only when ``GROQ_API_KEY`` is configured) purely to compose reply drafts.
"""

import logging
import os
import re

from datetime import datetime, timedelta, timezone

import jwt
from bson import ObjectId

from database import messages_collection, tasks_collection
from services.ai.providers.groq import is_groq_available
from services.security import JWT_SECRET

logger = logging.getLogger(__name__)

CONFIRM_TTL_MINUTES = 2
CONFIRM_PURPOSE = "jarvis_confirm"

# ── Reply constants (plain, professional) ──────────────────────────────────

ACTION_ERROR_REPLY = (
    "I hit a problem while running that action. Please try again in a moment."
)

CONFIRM_INVALID_REPLY = (
    "That confirmation has expired or is invalid. Please run the command again."
)

CONFIRM_CANCELLED_REPLY = (
    "Understood — I have not made any changes."
)

CREATE_CLARIFICATION_REPLY = (
    "I need a title to create that task. Try something like "
    "\u201cCreate a task called submit the report\u201d, and add a due date "
    "or priority if you like."
)

COMPLETE_CLARIFICATION_REPLY = (
    "Which task would you like to complete? Tell me the task name, for "
    "example \u201cComplete my task call the vendor\u201d."
)

DELETE_CLARIFICATION_REPLY = (
    "Which task would you like to delete? Tell me the task name, for "
    "example \u201cDelete my task call the vendor\u201d."
)

REPLY_DRAFT_FOOTER = (
    "This is only a draft — I won't send anything unless you ask me to."
)

# ── Favourite words / keywords (all lowercase matching) ────────────────────

CREATE_TASK_VERBS = ("create", "add", "make", "set up", "schedule")
COMPLETE_TASK_VERBS = ("complete", "finish", "mark", "check off", "tick off")
DELETE_TASK_VERBS = ("delete", "remove", "erase", "discard", "get rid of", "drop")

TASK_KEYWORDS = ("to-dos", "to dos", "to-do", "to do", "todo", "todos", "tasks", "task")

PRIORITY_WORDS = {
    "urgent": "urgent",
    "critical": "urgent",
    "high": "important",
    "important": "important",
    "medium": "normal",
    "normal": "normal",
    "low": "low",
}

DATE_WORDS = (
    "end of the day",
    "end of day",
    "this week",
    "next week",
    "next month",
    "tomorrow",
    "tonight",
    "today",
    "asap",
    "soon",
    "weekend",
    "friday",
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "saturday",
    "sunday",
)

DEADLINE_CONNECTORS = "by|due|before|for|on"

# ── Detection regexes (deterministic, no LLM) ──────────────────────────────

SENDER_SEARCH_RE = re.compile(
    r"^\s*(?:please\s+)?(?:find|search|show|list|get|fetch)\s+"
    r"(?:my\s+|the\s+|me\s+)?messages?\s+from\s+"
    r"(?:the\s+sender\s+)?(?P<name>.+?)\s*$"
)

KEYWORD_SEARCH_RE = [
    re.compile(
        r"^\s*(?:please\s+)?(?:search|find)\s+(?:my\s+)?messages?\s+"
        r"(?:for|about|containing|regarding|with)\s+(?P<term>.+?)\s*$"
    ),
    re.compile(r"^\s*(?:please\s+)?(?:search|find)\s+for\s+(?P<term>.+?)\s*$"),
    re.compile(
        r"^\s*(?:please\s+)?(?:show|list)\s+(?:me\s+)?(?:the\s+)?messages?\s+"
        r"(?:about|containing|mentioning|matching)\s+(?P<term>.+?)\s*$"
    ),
]

TRAILING_TOPIC_RE = re.compile(r"\s+(?:about|regarding|concerning|mentioning)\s+.*$")

IMPORTANT_MESSAGES_RE = re.compile(
    r"(?:show|list|display|get|give|fetch|what are)\b.{0,25}"
    r"\b(?:important|urgent|high[-\s]?priority)\b.{0,25}\bmessages?\b"
)

COMPLETED_TASKS_RE = re.compile(
    r"(?:show|list|display|get|what are|which)\b.{0,25}"
    r"\b(?:completed|done|finished)\b.{0,25}\b(?:tasks?|to[- ]?dos?|checklist)\b"
)

CREATE_TASK_RE = re.compile(
    r"\b(?:create|add|make|set up|schedule)\b.{0,20}\b(?:task|to do|to-do|todo)\b"
)

DRAFT_INTENT_RE = re.compile(
    r"\b(?:draft|write|compose|prepare)\b.{0,25}\breply\b|\breply\s+to\b"
)

EXPLAIN_IMPORTANT_RE = re.compile(
    r"\bwhy\b.{0,40}\b(?:important|urgent)\b|\bwhy\b.{0,40}\battention\b"
)

ATTENTION_RANK_RES = [
    re.compile(r"\bwhich\b.{0,40}\b(?:messages?|ones|inbox|items?)\b.{0,40}\b(?:handle|prioritize|look at)\b"),
    re.compile(r"\b(?:handle|deal with)\b.{0,30}\bfirst\b"),
    re.compile(r"\bprioritize\b.{0,40}\bmessages?\b"),
    re.compile(r"\bhelp me prioritize\b"),
]

DRAFT_SYSTEM_PROMPT = (
    "You are JARVIS. Write a professional, polite email or message reply "
    "draft in the same language as the original message. Keep it under 60 "
    "words. Respond with ONLY a JSON object of the form "
    '{"draft": "your draft text"}'
)


# ── Low-level text helpers ─────────────────────────────────────────────────

def _normalize(message: str) -> str:
    return " ".join(str(message or "").lower().split())


def _clean_extract(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"[.!?]+$", "", value.strip()).strip(" \t,;:\"'“”’‘-")


def _has_word(text: str, words: tuple[str, ...]) -> bool:
    return any(re.search(rf"\b{re.escape(w)}\b", text) for w in words)


# ── Intent detection (runs before Phase 1 routing) ─────────────────────────

def detect_action(message: str) -> dict | None:
    """Classify a command into a Phase 2 action, or None to keep Phase 1.

    Ordering matters: list/search phrasing is inspected before create/complete/
    delete so phrases like "show my completed tasks" are not misread as a
    "complete task" command.
    """
    text = _normalize(message)
    if not text:
        return None

    draft = _parse_draft_reply(text)
    if draft is not None:
        return {"type": "draft_reply", "params": draft}

    sender = _parse_sender_search(text)
    if sender is not None:
        return {"type": "search_messages", "params": {"sender": sender}}

    keyword = _parse_keyword_search(text)
    if keyword is not None:
        return {"type": "search_messages", "params": {"keyword": keyword}}

    if re.search(r"\bsummarize\b", text) and ("message" in text or "inbox" in text):
        return {"type": "summarize_messages", "params": {}}

    if IMPORTANT_MESSAGES_RE.search(text):
        return {"type": "list_important_messages", "params": {}}

    if COMPLETED_TASKS_RE.search(text):
        return {"type": "list_completed_tasks", "params": {}}

    if CREATE_TASK_RE.search(text):
        return {"type": "create_task", "params": _parse_create_task(text)}

    complete_name = _parse_task_action(text, "complete")
    if complete_name is not None:
        return {"type": "complete_task", "params": {"name": complete_name}}

    delete_name = _parse_task_action(text, "delete")
    if delete_name is not None:
        return {"type": "delete_task", "params": {"name": delete_name}}

    if any(p.search(text) for p in ATTENTION_RANK_RES):
        return {"type": "analyze_attention", "params": {}}

    if EXPLAIN_IMPORTANT_RE.search(text):
        return {"type": "explain_attention", "params": {}}

    return None


def _parse_sender_search(text: str) -> str | None:
    m = SENDER_SEARCH_RE.search(text)
    if not m:
        return None
    name = _clean_extract(m.group("name"))
    name = TRAILING_TOPIC_RE.sub("", name).strip(" ,;:")
    return name or None


def _parse_keyword_search(text: str) -> str | None:
    for pattern in KEYWORD_SEARCH_RE:
        m = pattern.search(text)
        if m:
            term = _clean_extract(m.group("term"))
            if term:
                return term
    return None


def _parse_draft_reply(text: str) -> dict | None:
    if not DRAFT_INTENT_RE.search(text):
        return None
    params: dict = {"target": None, "instruction": None}
    m = re.search(r"\b(?:saying|say|tell them|mentioning)\s+(.+?)\s*$", text)
    if m:
        params["instruction"] = _clean_extract(m.group(1))
    m = re.search(r"\breply\s+to\s+(.+?)\s*$", text)
    if m:
        who = _clean_extract(m.group(1))
        who = re.sub(r"\b(?:saying|say|tell them|mentioning)\b.*$", "", who).strip(" ,;:")
        if who and who not in ("this message", "this email", "this", "the message", "the email"):
            params["target"] = who
    return params


def _parse_task_action(text: str, kind: str) -> str | None:
    verbs = COMPLETE_TASK_VERBS if kind == "complete" else DELETE_TASK_VERBS
    if not _has_word(text, verbs):
        return None
    return _extract_task_name(text, verbs)


def _extract_task_name(text: str, verbs: tuple[str, ...]) -> str | None:
    body = text
    for verb in sorted(verbs, key=len, reverse=True):
        pattern = re.compile(rf"^\s*(?:please\s+)?{re.escape(verb)}\b")
        if pattern.search(body):
            body = pattern.sub(" ", body)
            break
    body = re.sub(r"^\s*(?:my|the|this)\s+", "", body)
    for kw in sorted(TASK_KEYWORDS, key=len, reverse=True):
        m = re.search(rf"\b{re.escape(kw)}\b\s*", body)
        if m:
            body = body[: m.start()] + " " + body[m.end():]
            break
    m = re.search(r"\b(?:called|named|titled)\s+", body)
    if m:
        body = body[m.end():]
    body = re.sub(r"\s+as\s+(?:completed|done|finished|complete)\s*$", "", body)
    body = re.sub(r"\s+(?:completed|done|finished)\s*$", "", body)
    body = _clean_extract(body)
    return body


def _find_task_keyword(text: str) -> tuple[int | None, str | None]:
    best_idx, best_kw = None, None
    for kw in TASK_KEYWORDS:
        idx = text.find(kw)
        if idx != -1 and (best_idx is None or idx < best_idx):
            best_idx, best_kw = idx, kw
    return best_idx, best_kw


def _find_word(text: str, word: str) -> int | None:
    m = re.search(rf"\b{re.escape(word)}\b", text)
    return m.start() if m else None


def _parse_create_task(text: str) -> dict:
    params = {"title": None, "description": None, "deadline": None, "priority": None}

    task_idx, matched_kw = _find_task_keyword(text)
    if task_idx is None:
        return params

    for word, mapped in PRIORITY_WORDS.items():
        word_idx = _find_word(text, word)
        if word_idx is not None and word_idx < task_idx:
            params["priority"] = mapped
            break

    remainder = text[task_idx + len(matched_kw or ""):]
    labelled = re.match(r"^\s*(?:called|named|titled)\s+(.+)$", remainder)
    if labelled:
        title_raw = labelled.group(1)
    else:
        title_raw = re.sub(r"^\s*(?:a|an|the|to|:)\s*", "", remainder)

    title_raw, deadline = _pull_deadline(title_raw)
    title = _clean_extract(title_raw)
    params["title"] = title or None
    params["description"] = title or None
    params["deadline"] = deadline
    return params


def _pull_deadline(raw: str) -> tuple[str, str | None]:
    raw = raw.strip()
    m = re.search(
        rf"\s+(?:{DEADLINE_CONNECTORS})\s+(?P<d>.+?)\s*$", raw
    )
    if m:
        deadline = _clean_extract(m.group("d"))
        if deadline:
            return raw[: m.start()].strip(), deadline
    for token in DATE_WORDS:
        if re.search(rf"\s+{re.escape(token)}\s*$", raw):
            return raw[: -(len(token))].strip(), token
    return raw, None


# ── Confirmation tokens (signed, user-bound, short-lived) ──────────────────

def create_confirmation_token(user_id: str, action_type: str, params: dict) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "purpose": CONFIRM_PURPOSE,
        "sub": user_id,
        "action": action_type,
        "params": params,
        "iat": now,
        "exp": now + timedelta(minutes=CONFIRM_TTL_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def _verify_confirmation_token(user_id: str, token: str) -> dict | None:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.InvalidTokenError:
        return None
    if payload.get("purpose") != CONFIRM_PURPOSE:
        return None
    if payload.get("sub") != user_id:
        return None
    return payload


# ── Reply builders ─────────────────────────────────────────────────────────

def _message_bites(docs: list[dict]) -> list[str]:
    bites = []
    for doc in docs:
        label = (
            doc.get("subject")
            or (doc.get("ai_analysis") or {}).get("summary")
            or doc.get("content")
        )
        label = str(label or "no text").strip()
        if len(label) > 60:
            label = label[:57] + "..."
        bites.append(f"\"{label}\" from {doc.get('sender') or 'unknown'}")
    return bites


def _task_bites(docs: list[dict]) -> list[str]:
    bites = []
    for doc in docs:
        desc = (doc.get("description") or "an unnamed task").strip()
        if doc.get("deadline"):
            desc = f"{desc} (by {doc['deadline']})"
        bites.append(desc)
    return bites


def _task_summary_lines(params: dict) -> str:
    lines = [params["title"].strip()]
    if params.get("deadline"):
        lines.append(f"Due: {params['deadline']}")
    if params.get("priority"):
        lines.append(f"Priority: {params['priority']}")
    return "\n".join(lines)


def _request_confirmation(reply: str, user_id: str, action_type: str, params: dict, summary: str) -> dict:
    token = create_confirmation_token(user_id, action_type, params)
    return {
        "reply": reply,
        "action": {
            "type": "request_confirmation",
            "confirmation_token": token,
            "detail": {"pending_type": action_type, "summary": summary},
        },
        "used_ai": False,
    }


# ── Action executors ───────────────────────────────────────────────────────

async def _resolve_task_by_name(user_id: str, name: str, include_completed: bool = True) -> list[dict]:
    query: dict = {"user_id": user_id}
    if not include_completed:
        query["status"] = {"$ne": "completed"}
    tasks = await tasks_collection.find(query).sort("created_at", -1).to_list(length=200)

    name_l = name.casefold()
    name_tokens = set(re.findall(r"[a-z0-9']+", name_l))

    exact: list[dict] = []
    partial: list[dict] = []
    fuzzy: list[dict] = []
    for task in tasks:
        desc = (task.get("description") or "").casefold()
        if not desc:
            continue
        if desc == name_l:
            exact.append(task)
        elif name_l in desc or desc in name_l:
            partial.append(task)
        else:
            tokens = set(re.findall(r"[a-z0-9']+", desc))
            if name_tokens and (len(name_tokens & tokens) / len(name_tokens)) >= 0.6:
                fuzzy.append(task)
    return exact or partial or fuzzy


def _ambiguous_tasks_reply(name: str, matches: list[dict]) -> str:
    listing = "; ".join(_task_bites(matches[:5]))
    return (
        f"I found a few tasks matching \"{name}\": {listing}. "
        "Please tell me the exact task name so I know which one you mean."
    )


async def run_create_task(user_id: str, params: dict) -> dict:
    title = (params.get("title") or "").strip()
    if not title:
        return {"reply": CREATE_CLARIFICATION_REPLY, "action": None, "used_ai": False}

    summary = f"Create task: {title}"
    extras = []
    if params.get("deadline"):
        extras.append(f"due {params['deadline']}")
    if params.get("priority"):
        extras.append(f"priority {params['priority']}")
    if extras:
        summary += f" ({', '.join(extras)})"

    reply = (
        "I found these task details:\n"
        f"{_task_summary_lines(params)}\n\n"
        "Should I create it?"
    )
    return _request_confirmation(reply, user_id, "create_task", params, summary)


async def _execute_create_task(user_id: str, params: dict) -> dict:
    title = (params.get("title") or "").strip()
    now = datetime.now(timezone.utc)
    doc = {
        "user_id": user_id,
        "description": title,
        "deadline": params.get("deadline"),
        "priority_indicator": params.get("priority"),
        "requires_action": True,
        "status": "pending",
        "source_message_id": "",
        "source_message_preview": "",
        "created_at": now,
    }
    result = await tasks_collection.insert_one(doc)
    return {
        "reply": f"Done. I've created the task \"{title}\".",
        "action": {
            "type": "create_task",
            "detail": {"task_id": str(result.inserted_id), "title": title},
        },
        "used_ai": False,
    }


async def run_complete_task(user_id: str, params: dict) -> dict:
    task_id = (params.get("task_id") or "").strip()
    if task_id:
        if not ObjectId.is_valid(task_id):
            return {"reply": COMPLETE_CLARIFICATION_REPLY, "action": None, "used_ai": False}
        task = await tasks_collection.find_one({"_id": ObjectId(task_id), "user_id": user_id})
        if task is None:
            return {
                "reply": "I couldn't find that task to complete.",
                "action": None,
                "used_ai": False,
            }
        if task.get("status") == "completed":
            return {
                "reply": "That task is already completed.",
                "action": None,
                "used_ai": False,
            }
        return await _execute_complete(user_id, task)

    name = (params.get("name") or "").strip()
    if not name:
        return {"reply": COMPLETE_CLARIFICATION_REPLY, "action": None, "used_ai": False}

    matches = await _resolve_task_by_name(user_id, name, include_completed=False)
    if not matches:
        return {
            "reply": f"I couldn't find a pending task matching \"{name}\".",
            "action": None,
            "used_ai": False,
        }
    if len(matches) > 1:
        return {"reply": _ambiguous_tasks_reply(name, matches), "action": None, "used_ai": False}

    return await _execute_complete(user_id, matches[0])


async def _execute_complete(user_id: str, task: dict) -> dict:
    now = datetime.now(timezone.utc)
    result = await tasks_collection.find_one_and_update(
        {"_id": task["_id"], "user_id": user_id},
        {"$set": {"status": "completed", "updated_at": now}},
        return_document=True,
    )
    if not result:
        return {
            "reply": "That task could not be updated. It may have been removed.",
            "action": None,
            "used_ai": False,
        }
    desc = (result.get("description") or "that task").strip()
    return {
        "reply": f"Done — the task \"{desc}\" is now completed.",
        "action": {
            "type": "complete_task",
            "detail": {"task_id": str(result["_id"]), "title": desc},
        },
        "used_ai": False,
    }


async def run_delete_task(user_id: str, params: dict) -> dict:
    task_id = (params.get("task_id") or "").strip()
    if task_id:
        if not ObjectId.is_valid(task_id):
            return {"reply": DELETE_CLARIFICATION_REPLY, "action": None, "used_ai": False}
        task = await tasks_collection.find_one({"_id": ObjectId(task_id), "user_id": user_id})
        if task is None:
            return {
                "reply": "I couldn't find that task to delete. It may already be gone.",
                "action": None,
                "used_ai": False,
            }
        return await _request_delete_confirmation(user_id, task)

    name = (params.get("name") or "").strip()
    if not name:
        return {"reply": DELETE_CLARIFICATION_REPLY, "action": None, "used_ai": False}

    matches = await _resolve_task_by_name(user_id, name, include_completed=True)
    if not matches:
        return {
            "reply": f"I couldn't find a task matching \"{name}\".",
            "action": None,
            "used_ai": False,
        }
    if len(matches) > 1:
        return {"reply": _ambiguous_tasks_reply(name, matches), "action": None, "used_ai": False}

    return await _request_delete_confirmation(user_id, matches[0])


async def _request_delete_confirmation(user_id: str, task: dict) -> dict:
    """Ask for confirmation before deleting one concrete, user-owned task."""
    desc = (task.get("description") or "that task").strip()
    return _request_confirmation(
        f'Do you want me to delete the task "{desc}"?',
        user_id,
        "delete_task",
        {"task_id": str(task["_id"])},
        f"Delete task: {desc}",
    )


async def _execute_delete_task(user_id: str, params: dict) -> dict:
    task_id = (params.get("task_id") or "").strip()
    if not ObjectId.is_valid(task_id):
        return {"reply": CONFIRM_INVALID_REPLY, "action": None, "used_ai": False}

    result = await tasks_collection.find_one_and_delete(
        {"_id": ObjectId(task_id), "user_id": user_id}
    )
    if not result:
        return {
            "reply": "That task no longer exists. Nothing was deleted.",
            "action": None,
            "used_ai": False,
        }
    desc = (result.get("description") or "that task").strip()
    return {
        "reply": f"Deleted the task \"{desc}\".",
        "action": {
            "type": "delete_task",
            "detail": {"task_id": task_id, "title": desc},
        },
        "used_ai": False,
    }


async def _run_list_completed_tasks(user_id: str) -> dict:
    docs = (
        await tasks_collection.find({"user_id": user_id, "status": "completed"})
        .sort("updated_at", -1)
        .to_list(length=10)
    )
    if not docs:
        return {
            "reply": "You have no completed tasks yet.",
            "action": {"type": "get_data", "detail": {"list": "completed_tasks", "count": 0}},
            "used_ai": False,
        }
    bites = _task_bites(docs[:5])
    extra = f"\n…and {len(docs) - 5} more." if len(docs) > 5 else ""
    return {
        "reply": f"You have {len(docs)} completed task{'' if len(docs) == 1 else 's'}:\n"
        + "\n".join(f"• {b}" for b in bites)
        + extra,
        "action": {"type": "get_data", "detail": {"list": "completed_tasks", "count": len(docs)}},
        "used_ai": False,
    }


# ── Message deletion (confirmation-gated) ───────────────────────────────────
#
# Deletion specs mirror the Phase 4 / Phase 6 filter params so every delete is
# explicit and user-scoped: {"type": "all|sender|keyword|priority|status|when|ids",
# "value": ...}. Bulk deletes count the affected rows first, then ask for the
# signed confirmation; the executor re-runs the same query after the token
# round-trip so nothing ever deletes outside the user's own messages.

_MATCH_NOTHING = {"_id": {"$in": []}}


def _message_delete_query(params: dict) -> dict:
    """Mongo filter for a delete spec (always combined with the caller's user_id)."""
    kind = params.get("type")
    value = str(params.get("value") or "").strip()
    if kind == "ids":
        ids = [i for i in (params.get("ids") or []) if ObjectId.is_valid(str(i))]
        return {"_id": {"$in": [ObjectId(str(i)) for i in ids]}} if ids else _MATCH_NOTHING
    if kind == "sender":
        return {"sender": {"$regex": re.escape(value), "$options": "i"}}
    if kind == "keyword":
        regex = {"$regex": re.escape(value), "$options": "i"}
        return {
            "$or": [
                {"sender": regex},
                {"content": regex},
                {"subject": regex},
                {"ai_analysis.summary": regex},
            ]
        }
    if kind == "priority":
        values = ["urgent", "important"] if value == "important" else ["urgent"]
        return {"ai_analysis.priority": {"$in": values}}
    if kind == "status":
        return {"status": value if value in ("unread", "read") else "unread"}
    if kind == "when":
        from services.ai.jarvis_messages import _date_range  # lazy: avoids circular import

        gte, lt = _date_range(value)
        if gte is None:
            return _MATCH_NOTHING
        return (
            {"created_at": {"$gte": gte}}
            if lt is None
            else {"created_at": {"$gte": gte, "$lt": lt}}
        )
    return {}


def _message_delete_desc(params: dict, count: int) -> str:
    """Human-readable summary of a delete spec (shown before confirmation)."""
    kind = params.get("type") or "all"
    value = str(params.get("value") or "").strip()
    if kind == "ids":
        return "that message"
    if kind == "sender":
        head = f"all messages from {value}"
    elif kind == "keyword":
        head = f'all messages about "{value}"'
    elif kind == "priority":
        head = f"all {value} messages"
    elif kind == "status":
        head = f"all {value} messages"
    elif kind == "when":
        head = f"all messages from {value}"
    else:
        head = "all your messages"
    return f"{head} ({count} " + ("message" if count == 1 else "messages") + ")"


def _request_message_delete(user_id: str, params: dict, count: int) -> dict:
    return _request_confirmation(
        f"Do you want me to delete {_message_delete_desc(params, count)}?",
        user_id,
        "delete_messages",
        params,
        _message_delete_desc(params, count),
    )


async def _ambiguous_delete_reply(user_id: str, query: dict) -> dict:
    docs = (
        await messages_collection.find({**query, "user_id": user_id})
        .sort("created_at", -1)
        .to_list(length=5)
    )
    bites = "; ".join(_message_bites(docs)) if docs else "none that I can see"
    return {
        "reply": (
            "Which message do you mean? Your recent matching messages are: "
            f"{bites}. Tell me the sender or subject and I'll delete exactly that one."
        ),
        "action": None,
        "used_ai": False,
    }


async def run_delete_messages(user_id: str, params: dict, require_single: bool = False) -> dict:
    """Delete the user's own messages behind the signed confirmation.

    ``params`` is a delete spec (see above). With ``require_single`` the spec
    must resolve to exactly one message for context references ("delete that
    one"); anything else produces a clarification instead of guessing.
    """
    if params.get("type") == "ids":
        query = _message_delete_query(params)
        count = await messages_collection.count_documents({**query, "user_id": user_id})
        if count == 0:
            return {
                "reply": "I couldn't find any messages matching that to delete.",
                "action": None,
                "used_ai": False,
            }
        return _request_message_delete(user_id, params, count)

    query: dict = {"user_id": user_id, **_message_delete_query(params)}
    count = await messages_collection.count_documents(query)
    if count == 0:
        return {
            "reply": "I couldn't find any messages matching that to delete.",
            "action": None,
            "used_ai": False,
        }
    if require_single:
        if count > 1:
            return await _ambiguous_delete_reply(user_id, query)
        docs = (
            await messages_collection.find(query).sort("created_at", -1).to_list(length=1)
        )
        if not docs:
            return {
                "reply": "I couldn't find any messages matching that to delete.",
                "action": None,
                "used_ai": False,
            }
        return _request_message_delete(
            user_id, {"type": "ids", "ids": [str(docs[0]["_id"])]}, 1
        )
    return _request_message_delete(user_id, params, count)


async def _execute_delete_messages(user_id: str, params: dict) -> dict:
    query = {"user_id": user_id, **_message_delete_query(params)}
    result = await messages_collection.delete_many(query)
    deleted = result.deleted_count
    if deleted == 0:
        return {
            "reply": "I couldn't find any messages matching that to delete.",
            "action": None,
            "used_ai": False,
        }
    return {
        "reply": f"Done. I deleted {deleted} " + ("message." if deleted == 1 else "messages."),
        "action": {"type": "delete_messages", "detail": {"count": deleted}},
        "used_ai": False,
    }


async def run_list_important_messages(user_id: str) -> dict:
    docs = (
        await messages_collection.find(
            {"user_id": user_id, "ai_analysis.priority": {"$in": ["urgent", "important"]}}
        )
        .sort("created_at", -1)
        .to_list(length=10)
    )
    if not docs:
        return {
            "reply": "No important or urgent messages are currently flagged.",
            "action": {"type": "get_data", "detail": {"list": "important_messages", "count": 0}},
            "used_ai": False,
        }
    bites = _message_bites(docs[:3])
    extra = f"\n…and {len(docs) - 3} more." if len(docs) > 3 else ""
    return {
        "reply": f"You have {len(docs)} important or urgent message{'' if len(docs) == 1 else 's'}:\n"
        + "\n".join(f"• {b}" for b in bites)
        + extra,
        "action": {"type": "get_data", "detail": {"list": "important_messages", "count": len(docs)}},
        "used_ai": False,
    }


async def run_summarize_unread(user_id: str) -> dict:
    docs = (
        await messages_collection.find({"user_id": user_id, "status": "unread"})
        .sort("created_at", -1)
        .to_list(length=10)
    )
    if not docs:
        return {
            "reply": "You have no unread messages to summarize.",
            "action": {"type": "summarize_messages", "detail": {"count": 0}},
            "used_ai": False,
        }
    bites = _message_bites(docs[:3])
    extra = f"\n…and {len(docs) - 3} more." if len(docs) > 3 else ""
    return {
        "reply": f"You have {len(docs)} unread message{'' if len(docs) == 1 else 's'}:\n"
        + "\n".join(f"• {b}" for b in bites)
        + extra,
        "action": {"type": "summarize_messages", "detail": {"count": len(docs)}},
        "used_ai": False,
    }


async def run_search_messages(user_id: str, params: dict) -> dict:
    query: dict = {"user_id": user_id}
    kind, value = "", ""
    if params.get("sender"):
        kind, value = "from", params["sender"]
        query["sender"] = {"$regex": re.escape(value), "$options": "i"}
    elif params.get("keyword"):
        kind, value = "about", params["keyword"]
        regex = {"$regex": re.escape(value), "$options": "i"}
        query["$or"] = [
            {"sender": regex},
            {"content": regex},
            {"subject": regex},
            {"ai_analysis.summary": regex},
        ]
    else:
        return {"reply": CREATE_CLARIFICATION_REPLY, "action": None, "used_ai": False}

    docs = (
        await messages_collection.find(query)
        .sort("created_at", -1)
        .to_list(length=8)
    )
    if not docs:
        return {
            "reply": f"No messages {kind} \"{value}\" were found.",
            "action": {"type": "search_messages", "detail": {"query": value, "count": 0}},
            "used_ai": False,
        }
    bites = _message_bites(docs[:3])
    extra = f"\n…and {len(docs) - 3} more." if len(docs) > 3 else ""
    return {
        "reply": f"I found {len(docs)} message{'' if len(docs) == 1 else 's'} {kind} \"{value}\":\n"
        + "\n".join(f"• {b}" for b in bites)
        + extra,
        "action": {"type": "search_messages", "detail": {"query": value, "count": len(docs)}},
        "used_ai": False,
    }


async def run_attention_ranking(user_id: str) -> dict:
    docs = (
        await messages_collection.find(
            {
                "user_id": user_id,
                "$or": [
                    {"ai_analysis.priority": {"$in": ["urgent", "important"]}},
                    {"ai_analysis.needs_attention": True},
                ],
            }
        )
        .sort("created_at", -1)
        .to_list(length=10)
    )

    def _sort_key(doc: dict):
        priority = (doc.get("ai_analysis") or {}).get("priority", "")
        order = {"urgent": 0, "important": 1}.get(priority, 2)
        flagged = 0 if (doc.get("ai_analysis") or {}).get("needs_attention") else 1
        return order, flagged, doc.get("created_at") or datetime.min

    docs.sort(key=_sort_key)

    if not docs:
        return {
            "reply": "Nothing is currently flagged as needing your attention.",
            "action": {"type": "analyze_attention", "detail": {"count": 0}},
            "used_ai": False,
        }
    bites = []
    for doc in docs[:3]:
        priority = (doc.get("ai_analysis") or {}).get("priority")
        tag = f"[{priority}]" if priority in ("urgent", "important") else "[flagged]"
        bites.append(f"{tag} " + _message_bites([doc])[0])
    extra = f"\n…and {len(docs) - 3} more." if len(docs) > 3 else ""
    return {
        "reply": (
            f"Here's what I'd handle first — {len(docs)} message{'' if len(docs) == 1 else 's'} need attention:\n"
            + "\n".join(f"• {b}" for b in bites)
            + extra
        ),
        "action": {"type": "analyze_attention", "detail": {"count": len(docs)}},
        "used_ai": False,
    }


async def run_explain_important(user_id: str) -> dict:
    docs = (
        await messages_collection.find(
            {
                "user_id": user_id,
                "ai_analysis.priority": {"$in": ["urgent", "important"]},
            }
        )
        .sort("created_at", -1)
        .to_list(length=5)
    )
    if not docs:
        return {
            "reply": "Nothing is currently flagged as important or urgent.",
            "action": {"type": "analyze_attention", "detail": {"count": 0}},
            "used_ai": False,
        }
    doc = docs[0]
    ai = doc.get("ai_analysis") or {}
    priority = ai.get("priority", "important")
    sender = doc.get("sender") or "an unknown sender"
    explanation = ai.get("explanation") or ai.get("summary")
    subject = doc.get("subject")
    if subject:
        sender = f"{sender} (\"{subject}\")"
    bits = [
        f"This message from {sender} is flagged as {priority}.",
    ]
    if explanation:
        bits.append(str(explanation))
    review = ai.get("recommended_action") or ai.get("recommended_actions")
    if isinstance(review, list):
        review = " ".join(str(r) for r in review) or None
    if review:
        bits.append(f"Suggested next step: {review}")
    return {
        "reply": " ".join(bits),
        "action": {
            "type": "analyze_attention",
            "detail": {"message_id": str(doc["_id"]), "priority": priority},
        },
        "used_ai": False,
    }


# ── Reply drafting ─────────────────────────────────────────────────────────

def _llm_configured() -> bool:
    # A key alone is not enough: during a circuit-breaker cooldown Groq must
    # not be consulted, so drafts degrade to the deterministic template.
    return bool(os.getenv("GROQ_API_KEY")) and is_groq_available()


def _fallback_draft(sender: str | None, subject: str | None, instruction: str | None) -> str:
    greeting = f"Dear {sender}," if sender else "Hello,"
    if instruction:
        body = instruction.capitalize()
    elif subject:
        body = f"Thank you for your message regarding \"{subject}\"."
    else:
        body = "Thank you for your message."
    return f"{greeting}\n\n{body}.\n\nBest regards"


async def _resolve_reply_target(user_id: str, target: str | None) -> dict | None:
    if target:
        regex = {"$regex": re.escape(target), "$options": "i"}
        docs = await (
            messages_collection.find(
                {"user_id": user_id, "$or": [{"sender": regex}, {"subject": regex}]}
            )
            .sort("created_at", -1)
            .to_list(length=5)
        )
        return docs[0] if docs else None
    docs = await (
        messages_collection.find({"user_id": user_id, "status": "unread"})
        .sort("created_at", -1)
        .to_list(length=5)
    )
    return docs[0] if docs else None


async def run_draft_reply(user_id: str, params: dict) -> dict:
    target = (params.get("target") or "").strip() or None
    instruction = (params.get("instruction") or "").strip() or None

    doc = await _resolve_reply_target(user_id, target)
    if doc is None:
        if target:
            return {
                "reply": f"I couldn't find a message from \"{target}\" to reply to.",
                "action": None,
                "used_ai": False,
            }
        return {
            "reply": "There are no unread messages to reply to. Tell me which "
            "message (by sender or subject) and I'll draft a reply.",
            "action": None,
            "used_ai": False,
        }

    sender = doc.get("sender") or "the sender"
    subject = doc.get("subject")
    content = doc.get("content") or ""

    draft = None
    used_ai = False
    if _llm_configured():
        from services.ai.providers.groq import GroqProvider

        prompt_parts = [
            DRAFT_SYSTEM_PROMPT,
            f"\n\nOriginal message from {sender}:",
            f"\"{subject}\" — " if subject else "",
            f"\"{str(content)[:400]}\"",
        ]
        if instruction:
            prompt_parts.append(f"\n\nRequirement from the recipient: \"{instruction}\"")
        try:
            result = await GroqProvider().chat("".join(prompt_parts))
            candidate = result.get("draft") if isinstance(result, dict) else None
            if isinstance(candidate, str) and candidate.strip():
                draft = candidate.strip()
                used_ai = True
        except Exception as exc:
            logger.warning("JARVIS draft generation failed, using fallback: %s", exc)

    if not draft:
        draft = _fallback_draft(sender, subject, instruction)

    reply = (
        f"I've drafted a reply to {sender}:\n\n{draft}\n\n{REPLY_DRAFT_FOOTER}"
    )
    return {
        "reply": reply,
        "action": {
            "type": "draft_reply",
            "detail": {
                "message_id": str(doc["_id"]),
                "sender": sender,
                "subject": subject,
                "instruction": instruction,
                "draft": draft,
            },
        },
        "used_ai": used_ai,
    }


# ── Central dispatch ───────────────────────────────────────────────────────

ACTION_HANDLERS = {
    "create_task": run_create_task,
    "complete_task": run_complete_task,
    "delete_task": run_delete_task,
    "list_completed_tasks": lambda uid, params: _run_list_completed_tasks(uid),
    "list_important_messages": lambda uid, params: run_list_important_messages(uid),
    "summarize_messages": lambda uid, params: run_summarize_unread(uid),
    "search_messages": run_search_messages,
    "analyze_attention": lambda uid, params: run_attention_ranking(uid),
    "explain_attention": lambda uid, params: run_explain_important(uid),
    "draft_reply": run_draft_reply,
}

CONFIRM_EXECUTORS = {
    "create_task": _execute_create_task,
    "delete_task": _execute_delete_task,
    "delete_messages": _execute_delete_messages,
}


async def run_action(user_id: str, action: dict) -> dict:
    """Execute one detected Phase 2 action for the authenticated user."""
    action_type = action.get("type")
    handler = ACTION_HANDLERS.get(action_type)
    if handler is None:
        return {"reply": CONFIRM_INVALID_REPLY, "action": None, "used_ai": False}
    try:
        return await handler(user_id, action.get("params") or {})
    except Exception as exc:  # pragma: no cover - defensive last resort
        logger.exception(
            "JARVIS action %s failed for user %s: %s", action_type, user_id, exc
        )
        return {"reply": ACTION_ERROR_REPLY, "action": None, "used_ai": False}


async def run_confirmation(user_id: str, token: str, confirmed: bool = True) -> dict:
    """Validate a confirmation token and (if confirmed) execute its action."""
    payload = _verify_confirmation_token(user_id, token)
    if payload is None:
        return {"reply": CONFIRM_INVALID_REPLY, "action": None, "used_ai": False}
    if not confirmed:
        return {"reply": CONFIRM_CANCELLED_REPLY, "action": None, "used_ai": False}

    action_type = payload.get("action")
    executor = CONFIRM_EXECUTORS.get(action_type)
    if executor is None:
        return {"reply": CONFIRM_INVALID_REPLY, "action": None, "used_ai": False}
    try:
        return await executor(user_id, payload.get("params") or {})
    except Exception as exc:  # pragma: no cover - defensive last resort
        logger.exception(
            "JARVIS confirmation %s failed for user %s: %s", action_type, user_id, exc
        )
        return {"reply": ACTION_ERROR_REPLY, "action": None, "used_ai": False}