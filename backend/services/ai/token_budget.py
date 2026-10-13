"""Input-token budgeting for the single Groq analysis call.

Groq's free tier enforces a small input-tokens-per-minute (ITPM) budget and
answers an over-budget request with HTTP 413 ("Request too large"). A long
Gmail email plus up to five full thread messages can blow past it, which used
to leave the message stuck forever: 413 -> stored ``pending`` -> the retry
sweep re-runs it every cycle -> 413 again.

This module keeps every analysis request inside a safe input budget:

- ``estimate_tokens`` / ``truncate_to_tokens``: dependency-free (~4 chars per
  token) estimates, close enough to the provider's billing to stay safe.
- ``budget_message``: keep the head of the text — the ``Subject:`` line and
  the opening of the body, where the actionable content lives — and drop the
  tail (quoted reply chains, signatures).
- ``budget_context_messages``: bound BOTH each prior-thread message and the
  total context, so memory/context enrichment can never dominate the prompt.

The static analysis template is ~1k tokens, so the defaults leave ample room
for real content while staying well under a ~7k ITPM free-tier cap. All limits
are env-tunable. Short messages pass through byte-identical (no truncation).
"""

import math
import os

# Rough English ratio used by every major tokenizer heuristic. Good enough to
# stay safely under a hard cap; we deliberately over-estimate slightly.
CHARS_PER_TOKEN = 4

TRUNCATION_MARKER = "\n\n[... content truncated to fit the AI input limit ...]"


def _int_env(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default
    return value if value > 0 else default


# Total INPUT budget for one analysis request. The static template (~1k) plus
# context plus message must fit here; output tokens are capped separately.
MAX_PROMPT_TOKENS = _int_env("GROQ_MAX_PROMPT_TOKENS", 5000)
# Largest single (current) message we will send.
MAX_MESSAGE_TOKENS = _int_env("GROQ_MESSAGE_MAX_TOKENS", 2500)
# Total budget for the injected CONTEXT block (header + rules + messages).
MAX_CONTEXT_TOKENS = _int_env("GROQ_CONTEXT_MAX_TOKENS", 1200)
# Per prior-thread message clip inside the context block.
CONTEXT_MESSAGE_TOKENS = _int_env("GROQ_CONTEXT_MESSAGE_TOKENS", 200)


def estimate_tokens(text: str | None) -> int:
    """Estimate the token count of ``text`` (never raises on odd input)."""
    if not text:
        return 0
    return max(1, math.ceil(len(text) / CHARS_PER_TOKEN))


def chars_for_tokens(tokens: int) -> int:
    return max(0, tokens * CHARS_PER_TOKEN)


def truncate_to_tokens(
    text: str, max_tokens: int, marker: str = TRUNCATION_MARKER
) -> str:
    """Return ``text`` unchanged when it fits, else a head-preserving clip.

    The tail is dropped and a marker appended so the model knows the content is
    incomplete (it must not invent facts from missing text).
    """
    if not text:
        return text
    limit = chars_for_tokens(max_tokens)
    if limit <= 0:
        return ""
    if len(text) <= limit:
        return text
    keep = max(0, limit - len(marker))
    return text[:keep].rstrip() + marker


def budget_message(message: str | None, max_tokens: int | None = None) -> str:
    """Clip the message being analyzed to the per-message budget."""
    if not message:
        return message or ""
    return truncate_to_tokens(message, max_tokens or MAX_MESSAGE_TOKENS)


def budget_context_messages(
    messages: list[dict] | None,
    total_tokens: int | None = None,
    per_message_tokens: int | None = None,
) -> list[dict] | None:
    """Clip each prior-thread message and cap the total context size.

    Returns a NEW list of shallow copies (originals are never mutated); each
    ``content`` is clipped and later messages are dropped once the total budget
    is spent. The input is expected newest-first, so the most relevant context
    survives. Short contexts pass through byte-identical.
    """
    if not messages:
        return messages
    total_budget = total_tokens or MAX_CONTEXT_TOKENS
    per_budget = per_message_tokens or CONTEXT_MESSAGE_TOKENS
    budgeted: list[dict] = []
    used = 0
    for message in messages:
        remaining = total_budget - used
        if remaining <= 0:
            break
        per = min(per_budget, remaining)
        clipped = truncate_to_tokens(str(message.get("content") or ""), per)
        copy = dict(message)
        copy["content"] = clipped
        budgeted.append(copy)
        used += estimate_tokens(clipped)
    return budgeted
