"""
Complete AI Pipeline Tests (Day 14)

Unit tests for attention rules + integration tests against a live
server on localhost:8000.
Run: python test_attention_pipeline.py
"""

import asyncio
import sys
import httpx
from dotenv import load_dotenv

from services.ai.attention import (
    R1_REASON,
    R2_REASON,
    evaluate_attention,
)

load_dotenv()

BASE_URL = "http://localhost:8000"


def _analysis(priority="normal", tasks=None, deadlines=None):
    return {
        "priority": priority,
        "tasks_extracted": tasks or [],
        "deadlines": deadlines or [],
    }


# ---------------------------------------------------------------------------
# Unit tests: evaluate_attention rules (constitution R1/R2)
# ---------------------------------------------------------------------------

def test_r1_task_with_near_deadline_is_flagged():
    result = evaluate_attention(
        _analysis(
            tasks=[{"description": "Send FYP slides", "deadline": "Tonight"}],
            deadlines=["Tonight"],
        )
    )
    assert result["needs_attention"] is True
    assert result["attention_reason"] == R1_REASON
    print("[PASS] R1: task + near deadline -> flagged")


def test_r2_urgent_with_task_no_deadline_is_flagged():
    result = evaluate_attention(
        _analysis(
            priority="urgent",
            tasks=[{"description": "Call the client", "deadline": None}],
        )
    )
    assert result["needs_attention"] is True
    assert result["attention_reason"] == R2_REASON
    print("[PASS] R2: urgent + task -> flagged")


def test_r1_text_wins_when_both_rules_match():
    result = evaluate_attention(
        _analysis(
            priority="urgent",
            tasks=[{"description": "Send FYP slides", "deadline": "tonight"}],
            deadlines=["tonight"],
        )
    )
    assert result["needs_attention"] is True
    assert result["attention_reason"] == R1_REASON
    print("[PASS] R1+R2: near-deadline reason takes precedence")


def test_urgent_without_task_is_not_flagged():
    result = evaluate_attention(_analysis(priority="urgent"))
    assert result["needs_attention"] is False
    assert result["attention_reason"] == ""
    print("[PASS] Urgent alone -> not flagged")


def test_near_deadline_without_task_is_not_flagged():
    result = evaluate_attention(_analysis(deadlines=["Tonight"]))
    assert result["needs_attention"] is False
    assert result["attention_reason"] == ""
    print("[PASS] Deadline alone -> not flagged")


def test_no_signals_is_not_flagged():
    result = evaluate_attention(_analysis())
    assert result["needs_attention"] is False
    assert result["attention_reason"] == ""
    print("[PASS] No signals -> not flagged")


def test_far_future_deadline_is_not_near_term():
    result = evaluate_attention(
        _analysis(
            tasks=[{"description": "Prepare slides", "deadline": "next month"}],
            deadlines=["next month"],
        )
    )
    assert result["needs_attention"] is False
    print("[PASS] Far-future deadline -> not flagged")


def test_reason_invariant_holds():
    cases = [
        _analysis(),
        _analysis(priority="urgent"),
        _analysis(deadlines=["ASAP"]),
        _analysis(tasks=[{"description": "X", "deadline": "tomorrow"}]),
    ]
    for analysis in cases:
        result = evaluate_attention(analysis)
        assert result["needs_attention"] == bool(result["attention_reason"])
    print("[PASS] Invariant: reason non-empty iff flagged")


def test_failed_analysis_is_never_flagged():
    """The analyzer exception-fallback dict (status pending, no signals)
    must pass through evaluate_attention as unflagged."""
    fallback = {
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
    result = evaluate_attention(fallback)
    assert result["needs_attention"] is False
    assert result["attention_reason"] == ""
    print("[PASS] Failed analysis fallback -> never flagged")


def run_unit_tests():
    print("-" * 60)
    print("Unit tests: evaluate_attention")
    print("-" * 60)
    passed = 0
    failed = 0
    for test in [
        test_r1_task_with_near_deadline_is_flagged,
        test_r2_urgent_with_task_no_deadline_is_flagged,
        test_r1_text_wins_when_both_rules_match,
        test_urgent_without_task_is_not_flagged,
        test_near_deadline_without_task_is_not_flagged,
        test_no_signals_is_not_flagged,
        test_far_future_deadline_is_not_near_term,
        test_reason_invariant_holds,
        test_failed_analysis_is_never_flagged,
    ]:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"[FAIL] {test.__name__}: {e}")
            failed += 1
    return passed, failed


async def test_duplicate_message_updates_not_inserts():
    """Day14: Re-sending an identical WhatsApp payload updates the existing
    message instead of creating a copy."""
    import time

    payload = {
        "sender": f"Dup Tester {int(time.time())}",
        "message": "Duplicate guard check: send the FYP slides tonight.",
        "timestamp": None,
    }

    async with httpx.AsyncClient(timeout=180.0) as client:
        first = await client.post(f"{BASE_URL}/webhooks/whatsapp", json=payload)
        assert first.status_code == 200, f"Expected 200, got {first.status_code}"
        first_id = first.json()["data"]["id"]

        second = await client.post(f"{BASE_URL}/webhooks/whatsapp", json=payload)
        assert second.status_code == 200, f"Expected 200, got {second.status_code}"
        second_id = second.json()["data"]["id"]

        assert first_id == second_id, (
            f"Duplicate created new message: {first_id} != {second_id}"
        )

        listing = await client.get(f"{BASE_URL}/messages")
        assert listing.status_code == 200
        matches = [
            m
            for m in listing.json()
            if m["sender"] == payload["sender"] and m["content"] == payload["message"]
        ]
        assert len(matches) == 1, f"Expected 1 document, found {len(matches)}"
        assert matches[0]["ai_analysis"]["status"] == "completed"

        print(
            f"[PASS] Day14: Duplicate guard works - single document {first_id}, "
            "analysis updated in place"
        )


async def main():
    print("=" * 60)
    print("Complete AI Pipeline Tests")
    print("=" * 60)

    passed, failed = run_unit_tests()

    print("-" * 60)
    print("Integration tests")
    print("-" * 60)

    try:
        await test_duplicate_message_updates_not_inserts()
        passed += 1
    except Exception as e:
        print(f"[FAIL] Day14 duplicate guard: {e}")
        failed += 1

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
