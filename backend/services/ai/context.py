"""Bounded same-thread context for AI analysis (Day 25).

Three responsibilities:
1. ``fetch_thread_context``  — the ≤5 most recent same-user messages in a
   thread, excluding the message currently being analyzed.
2. ``build_context_block``   — render those messages (with short handles) as
   the CONTEXT section injected into the existing single AI call.
3. ``validate_context_updates`` / ``apply_context_updates`` — drop any
   model-suggested revision that cannot be proven against the fetched thread
   and apply the survivors as additive, reason-named revisions on earlier
   messages ("0 tolerance for unlabelled influence").

Every query/update is scoped by ``user_id`` (+ ``threadId``), so a context
effect can never touch another user's or another thread's documents.
"""

import logging
from datetime import datetime, timezone

from bson import ObjectId

from database import messages_collection

logger = logging.getLogger(__name__)

CONTEXT_HEADER = (
    "CONTEXT — PREVIOUS MESSAGES IN THIS CONVERSATION "
    "(from the same sender, same channel):"
)

CONTEXT_RULES = """RULES:
- Use context ONLY to supply a missing deadline/urgency to the CURRENT message
  or to report how an EARLIER message's analysis should change.
- NEVER override a fact explicitly stated IN THE CURRENT MESSAGE
  (a stated deadline always wins).
- The optional "context_updates" key targets EARLIER messages in this same
  conversation using their handles from the CONTEXT block above.
- "source_message_id" MUST be the handle of an EARLIER context message OR the
  current message's own handle (labeled above) — and the "value" must appear
  verbatim in that source message's content.
- NEVER invent values that do not appear in the linked messages."""

ALLOWED_CONTEXT_FIELDS = {"deadline", "priority", "note"}


async def fetch_thread_context(
    user_id: str,
    thread_id: str,
    exclude_message_id: str | None = None,
    limit: int = 5,
) -> list[dict]:
    """Return the ≤ ``limit`` most recent same-user messages of the thread,
    sorted by ``received_at`` desc, each enriched with a short ``handle``
    (the last 7 chars of its ``_id``, used by prompt-referenced updates).
    """
    flt = {"user_id": user_id, "threadId": thread_id}
    if exclude_message_id:
        flt["_id"] = {"$ne": ObjectId(exclude_message_id)}
    cursor = messages_collection.find(flt).sort([("received_at", -1)]).limit(limit)
    docs = await cursor.to_list(length=limit)
    for doc in docs:
        doc["handle"] = str(doc["_id"])[-7:]
    return docs


def build_context_block(
    messages: list[dict] | None, current_message_id: str | None = None
) -> str | None:
    """Render the full CONTEXT section, or ``None`` when there is nothing to
    add (an empty result keeps the prompt byte-identical to Day 24).

    When ``current_message_id`` is given, the message being analyzed is
    labeled with its own handle so the model can reference it as a
    ``context_updates`` source (the two-message flow: a follow-up enriches
    the anchor naming itself as the source).
    """
    if not messages:
        return None
    lines = [CONTEXT_HEADER]
    for msg in messages:
        received = msg.get("received_at")
        received_iso = received.isoformat() if received else ""
        lines.append(
            f"[{msg['handle']}] {msg.get('sender', '')} ({received_iso}): "
            f"{msg.get('content', '')}"
        )
    if current_message_id:
        lines.append(
            f"[{str(current_message_id)[-7:]}] (THIS message being analyzed — "
            "usable as a context_updates source handle)"
        )
    lines.append(CONTEXT_RULES)
    return "\n".join(lines)


def _handle_to_id(handle: str, thread_messages: list[dict]) -> str | None:
    """Exact-match a context handle back to a real message ``_id``.

    Mapping happens only against the fetched thread messages (already scoped
    by user + thread), so a forged handle cannot reach an arbitrary document.
    """
    for msg in thread_messages:
        if msg.get("handle") == handle:
            return str(msg["_id"])
    return None


def validate_context_updates(
    candidates: list[dict] | None,
    thread_messages: list[dict],
    current_message_id: str,
    current_content: str | None = None,
) -> list[dict]:
    """Drop any suggested revision that cannot be proven against the thread.

    A candidate survives ONLY when EVERY check passes:
    - ``target_message_id`` handle maps to a message in THIS thread fetch
    - the target is not the message currently being analyzed
    - ``field`` ∈ {deadline, priority, note}
    - ``source_message_id`` is the handle of a thread message OR of the
      current message itself (the two-message flow: a follow-up enriches the
      anchor naming itself as the source)
    - ``value`` appears verbatim in the source message's (or current
      message's) ``content``

    Rejected entries are logged with their reason and never reach storage.
    """
    if not candidates:
        return []
    valid: list[dict] = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            logger.info("Context update dropped: candidate is not an object")
            continue

        target_id = _handle_to_id(
            str(candidate.get("target_message_id") or ""), thread_messages
        )
        if target_id is None:
            logger.info(
                "Context update dropped: unknown target handle %r",
                candidate.get("target_message_id"),
            )
            continue
        if target_id == current_message_id:
            logger.info(
                "Context update dropped: target is the message being analyzed (%s)",
                target_id,
            )
            continue

        field = str(candidate.get("field") or "")
        if field not in ALLOWED_CONTEXT_FIELDS:
            logger.info(
                "Context update dropped: disallowed field %r", candidate.get("field")
            )
            continue

        source_handle = str(candidate.get("source_message_id") or "")
        source_id = _handle_to_id(source_handle, thread_messages)
        source_content = None
        if source_id is None and source_handle and current_message_id:
            if source_handle == str(current_message_id)[-7:]:
                source_id = current_message_id
                source_content = current_content or ""
        if source_id is None:
            logger.info(
                "Context update dropped: unknown source handle %r",
                candidate.get("source_message_id"),
            )
            continue
        if source_content is None:
            source_content = next(
                (
                    msg.get("content") or ""
                    for msg in thread_messages
                    if str(msg["_id"]) == source_id
                ),
                "",
            )

        value = str(candidate.get("value") or "")
        if not value or value not in source_content:
            logger.info(
                "Context update dropped: value %r not verbatim in source message",
                value,
            )
            continue

        valid.append(
            {
                "target_message_id": target_id,
                "field": field,
                "value": value,
                "source_message_id": source_id,
                "reason": str(candidate.get("reason") or ""),
            }
        )
    return valid


async def apply_context_updates(
    valid_updates: list[dict], current_message_id: str, user_id: str
) -> int:
    """Apply valid revisions onto their target messages as additive,
    reason-named ``ai_analysis.context_updates`` entries.

    Each write is scoped to ``{"_id": target, "user_id": user}`` and is a
    ``$push`` of a NEW revision — original analysis fields are never touched.
    Errors are caught and logged; they never raise into ``process_message``.
    """
    applied = 0
    for update in valid_updates:
        try:
            result = await messages_collection.update_one(
                {"_id": ObjectId(update["target_message_id"]), "user_id": user_id},
                {
                    "$push": {
                        "ai_analysis.context_updates": {
                            "field": update["field"],
                            "value": update["value"],
                            "source_message_id": update["source_message_id"],
                            "reason": update["reason"],
                            "applied_at": datetime.now(timezone.utc),
                        }
                    }
                },
            )
            if result.modified_count:
                applied += 1
        except Exception as exc:  # pragma: no cover - safety net
            logger.warning(
                "Failed to apply context update on %s: %s",
                update["target_message_id"],
                exc,
            )
    return applied