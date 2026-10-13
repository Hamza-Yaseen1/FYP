"""Input-token budgeting for the single Groq analysis call.

Groq's free tier answers an over-budget request with HTTP 413; a long email
plus up to five full thread messages used to blow past it and loop forever.
These pure unit tests (no network) pin the budgeting contract:

- short text passes through byte-identical;
- a big message keeps its HEAD (subject + opening body) and drops the tail;
- context is bounded per message AND in total;
- the assembled prompt always fits ``MAX_PROMPT_TOKENS``.
"""

from services.ai import token_budget
from services.ai.providers.groq import ANALYSIS_PROMPT, build_analysis_prompt
from services.ai.token_budget import (
    CHARS_PER_TOKEN,
    TRUNCATION_MARKER,
    budget_context_messages,
    budget_message,
    estimate_tokens,
    truncate_to_tokens,
)


# ── estimate / truncate ─────────────────────────────────────────────────────


def test_estimate_tokens_handles_empty_and_none():
    assert estimate_tokens(None) == 0
    assert estimate_tokens("") == 0
    assert estimate_tokens("a" * CHARS_PER_TOKEN) == 1


def test_truncate_keeps_short_text_byte_identical():
    text = "Subject: hi\n\nShort body"
    assert truncate_to_tokens(text, 100) == text
    assert TRUNCATION_MARKER not in truncate_to_tokens(text, 100)


def test_truncate_preserves_head_and_marks_tail():
    text = "HEAD-" + "x" * 4000 + "-TAIL"
    clipped = truncate_to_tokens(text, 50)
    assert clipped.startswith("HEAD-")
    assert clipped.endswith(TRUNCATION_MARKER)
    assert TRUNCATION_MARKER in clipped
    assert len(clipped) < len(text)


# ── message budgeting ───────────────────────────────────────────────────────


def test_budget_message_clips_oversized_message_but_keeps_subject():
    huge = "Subject: quarterly report\n\n" + ("body " * 5000)
    clipped = budget_message(huge)
    assert estimate_tokens(clipped) <= token_budget.MAX_MESSAGE_TOKENS + 1
    assert clipped.startswith("Subject: quarterly report")
    assert TRUNCATION_MARKER in clipped


def test_budget_message_short_message_untouched():
    short = "hello world"
    assert budget_message(short) == short


# ── context budgeting ───────────────────────────────────────────────────────


def test_budget_context_clips_each_message_and_total():
    messages = [
        {"handle": f"h{i}", "sender": f"s{i}", "content": "c" * 5000}
        for i in range(5)
    ]
    budgeted = budget_context_messages(
        messages, total_tokens=400, per_message_tokens=50
    )
    assert budgeted
    total = sum(estimate_tokens(m["content"]) for m in budgeted)
    assert total <= 400
    for m in budgeted:
        assert estimate_tokens(m["content"]) <= 51


def test_budget_context_does_not_mutate_originals():
    original = {"handle": "h", "sender": "s", "content": "small"}
    budgeted = budget_context_messages([original], total_tokens=1000)
    assert budgeted == [original]
    assert budgeted[0] is not original


# ── build_analysis_prompt ───────────────────────────────────────────────────


def test_prompt_short_message_byte_identical_to_template():
    prompt = build_analysis_prompt("hello world")
    assert prompt == ANALYSIS_PROMPT.replace("{message}", "hello world")


def test_prompt_stays_within_budget_for_huge_message_and_context():
    huge = "Subject: quarterly\n\n" + ("body line. " * 5000)
    context = [
        {"handle": f"h{i}", "sender": f"s{i}", "content": "c" * 5000}
        for i in range(5)
    ]
    prompt = build_analysis_prompt(huge, context, "m0")
    assert estimate_tokens(prompt) <= token_budget.MAX_PROMPT_TOKENS
    assert "Subject: quarterly" in prompt


def test_prompt_aggressive_is_shorter_and_within_budget():
    huge = "Subject: x\n\n" + ("body line. " * 5000)
    context = [{"handle": "h", "sender": "s", "content": "prior", "received_at": None}]
    normal = build_analysis_prompt(huge, context, "m0")
    aggressive = build_analysis_prompt(huge, context, "m0", aggressive=True)
    assert len(aggressive) < len(normal)
    assert estimate_tokens(aggressive) <= token_budget.MAX_PROMPT_TOKENS


def test_prompt_preserves_braces_in_message():
    # `.replace`, never `.format` — message braces must survive verbatim.
    prompt = build_analysis_prompt("json {like} {this}")
    assert "{like} {this}" in prompt
