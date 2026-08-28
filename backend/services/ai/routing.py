"""Rule-based AI message routing (Day 24).

Pure, deterministic decisions — no I/O, no LLM. The Orchestrator uses
``decide_routing`` to pick which of the five agents contribute to a message
and whether a single AI call is needed. Rules are keyword- and
script-based, with a fail-toward-completeness default (full analysis)
whenever signals cannot be trusted.
"""

import re
import unicodedata
from dataclasses import dataclass, field

from .attention import NEAR_TERM_KEYWORDS

# The five fixed agents (spec: Priority, Summary, Task Extraction,
# Deadline Detection, Recommended Action).
AGENT_IDS = [
    "priority",
    "summary",
    "task_extraction",
    "deadline_detection",
    "recommended_action",
]

# Keep the list strong and verb-first: a matched phrase implies an action
# directed at the recipient. Deliberately excludes soft/noun words
# ("report", "update", "share", "please") that would over-match FYI text.
TASK_TRIGGER_KEYWORDS = [
    "send",
    "call",
    "review",
    "submit",
    "prepare",
    "confirm",
    "reply",
    "fix",
    "finish",
    "book",
    "pay",
    "remind",
    "follow up",
    "let me know",
    "check",
    "draft",
    "create",
    "email",
]

# Reuses the attention near-term list (tonight, today, tomorrow, asap,
# right now, immediately) so Deadline Detection and the NEEDS ATTENTION
# rules stay consistent, plus longer-horizon expressions.
TIME_EXPRESSION_KEYWORDS = [
    *NEAR_TERM_KEYWORDS,
    "this week",
    "next week",
    "next month",
    "eod",
    "this weekend",
    "next weekend",
    "by monday",
    "by tuesday",
    "by wednesday",
    "by thursday",
    "by friday",
    "by saturday",
    "by sunday",
]

TRIVIAL_PHRASES = {
    "ok",
    "okay",
    "hi",
    "hello",
    "hey",
    "yes",
    "yeah",
    "yep",
    "no",
    "nope",
    "thanks",
    "thank you",
    "ty",
    "thx",
    "sure",
    "done",
    "bye",
    "k",
    "got it",
    "sounds good",
    "fine",
    "good",
    "great",
    "nice",
    "perfect",
    "cool",
    "mmhmm",
}

MAX_TRIVIAL_LENGTH = 20

_WORD_RE = re.compile(r"\w+", re.UNICODE)


def _translate_upper(raw: str) -> str:
    return raw.translate(str.maketrans("أإآ", "ااا")).lower()


def _normalize(content: str) -> str:
    return " ".join(_translate_upper(content).split())


def _tokens(content: str) -> str:
    return " ".join(_WORD_RE.findall(_normalize(content)))


def has_trigger(content: str, keywords: list[str]) -> list[str]:
    """Lowercased keyword matches against a whitespace-normalized, Arabic-
    canonicalized version of the content. Returns the matched triggers."""
    return [kw for kw in keywords if kw in _normalize(content)]


def has_non_latin_script(content: str) -> bool:
    """True when the content uses foreign letters (Arabic, Cyrillic, ...).

    Any non-ASCII letter forces the full-analysis default because the
    keyword rules are tuned for English. Emoji (non-letter symbols) do not
    trigger this.
    """
    for ch in content:
        if ord(ch) > 0x007F and unicodedata.category(ch).startswith("L"):
            return True
    return False


def looks_trivial(content: str, task_triggers: list[str], time_triggers: list[str]) -> bool:
    """Exact phrase match in TRIVIAL_PHRASES, or a very short message
    (<= MAX_TRIVIAL_LENGTH characters) carrying no task/time signals."""
    if _tokens(content) in TRIVIAL_PHRASES:
        return True
    if len(_normalize(content)) <= MAX_TRIVIAL_LENGTH and not task_triggers and not time_triggers:
        return True
    return False


@dataclass
class RoutingDecision:
    needs_analysis: bool = False
    needs_llm: bool = False
    run_summary: bool = False
    run_task_extraction: bool = False
    run_deadline_detection: bool = False
    run_recommended_action: bool = False
    reason: str = ""
    triggers: list[str] = field(default_factory=list)

    def agents_run(self) -> list[str]:
        run = ["priority"]
        if self.run_summary:
            run.append("summary")
        if self.run_task_extraction:
            run.append("task_extraction")
        if self.run_deadline_detection:
            run.append("deadline_detection")
        if self.run_recommended_action:
            run.append("recommended_action")
        return run

    def agents_skipped(self) -> list[str]:
        run = set(self.agents_run())
        return [agent for agent in AGENT_IDS if agent not in run]


def decide_routing(content: str, message_type: str = "text") -> RoutingDecision:
    """Pick the smallest sufficient agent subset for one message.

    Decision table:
    - no analyzable content / media-only  -> no analysis
    - trivial phrase or very short with no signals -> deterministic defaults,
      zero AI calls
    - task action requested              -> Task Extraction + Recommended Action
    - time expression present            -> Deadline Detection
    - task + time expression             -> full analysis (all five agents)
    - non-Latin script / ambiguity       -> full analysis default
    """
    if message_type != "text" or content is None or content.strip() == "":
        return RoutingDecision(
            needs_analysis=False,
            needs_llm=False,
            reason="no analyzable content",
            triggers=[],
        )

    task_triggers = has_trigger(content, TASK_TRIGGER_KEYWORDS)
    time_triggers = has_trigger(content, TIME_EXPRESSION_KEYWORDS)

    if has_non_latin_script(content):
        return RoutingDecision(
            needs_analysis=True,
            needs_llm=True,
            run_summary=True,
            run_task_extraction=True,
            run_deadline_detection=True,
            run_recommended_action=True,
            reason="non_latin_script",
            triggers=list(dict.fromkeys(["non_latin_script", *task_triggers, *time_triggers])),
        )

    if looks_trivial(content, task_triggers, time_triggers):
        return RoutingDecision(
            needs_analysis=True,
            needs_llm=False,
            run_summary=True,
            run_task_extraction=False,
            run_deadline_detection=False,
            run_recommended_action=False,
            reason="trivial",
            triggers=[],
        )

    return RoutingDecision(
        needs_analysis=True,
        needs_llm=True,
        run_summary=True,
        run_task_extraction=bool(task_triggers),
        run_deadline_detection=bool(time_triggers),
        run_recommended_action=bool(task_triggers),
        reason="action" if task_triggers and not time_triggers else (
            "deadline" if time_triggers and not task_triggers else "full"
        ),
        triggers=task_triggers + time_triggers,
    )