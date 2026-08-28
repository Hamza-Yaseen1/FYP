"""
Complete AI Pipeline Tests (Day 14)

Unit tests for attention rules + integration tests against a live
server on localhost:8000.
Run: python test_attention_pipeline.py
"""

import asyncio
import json
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
    """Day23 (reworked from Day14): Re-delivering an identical signed Meta
    payload (same messages[].id) updates the existing message instead of
    creating a copy. Requires WHATSAPP_APP_SECRET to be set in .env."""
    import hashlib
    import hmac
    import os
    import time

    app_secret = os.getenv("WHATSAPP_APP_SECRET", "")
    if not app_secret:
        raise RuntimeError(
            "WHATSAPP_APP_SECRET is not set in .env — paste the real Meta App "
            "Secret before running integration tests against real traffic."
        )

    verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    if not phone_number_id:
        raise RuntimeError("WHATSAPP_PHONE_NUMBER_ID is not set in .env")

    wamid = f"wamid.dup.{int(time.time())}"

    def meta_payload():
        return {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "111111111111111",
                    "changes": [
                        {
                            "field": "messages",
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {
                                    "display_phone_number": "15550000000",
                                    "phone_number_id": phone_number_id,
                                },
                                "contacts": [
                                    {
                                        "profile": {"name": "Dup Tester"},
                                        "wa_id": "15551234567",
                                    }
                                ],
                                "messages": [
                                    {
                                        "from": "15551234567",
                                        "id": wamid,
                                        "timestamp": str(int(time.time())),
                                        "type": "text",
                                        "text": {
                                            "body": (
                                                "Duplicate guard check: send the "
                                                "FYP slides tonight."
                                            )
                                        },
                                    }
                                ],
                            },
                        }
                    ],
                }
            ],
        }

    def signed(raw):
        return hmac.new(
            app_secret.encode(), raw, hashlib.sha256
        ).hexdigest()

    async def deliver(raw):
        return await client.post(
            f"{BASE_URL}/webhooks/whatsapp",
            content=raw,
            headers={"X-Hub-Signature-256": f"sha256={signed(raw)}"},
        )

    async with httpx.AsyncClient(timeout=180.0) as client:
        register = await client.post(
            f"{BASE_URL}/auth/register",
            json={
                "name": f"Dup Tester {int(time.time())}",
                "email": f"dup{int(time.time())}@example.com",
                "password": "s3cretpass",
            },
        )
        assert register.status_code == 201, (
            f"Expected 201, got {register.status_code}: {register.text}"
        )

        # Ingested messages are attributed to the connected whatsapp owner,
        # so the test user must link the number server-side first.
        connect = await client.post(
            f"{BASE_URL}/connections", json={"provider": "whatsapp"}
        )
        assert connect.status_code == 201, (
            f"Expected 201, got {connect.status_code}: {connect.text}"
        )

        body = json.dumps(meta_payload()).encode()
        first = await deliver(body)
        assert first.status_code == 200, (
            f"Expected 200, got {first.status_code}: {first.text}"
        )
        assert first.json() == {"status": "ok"}

        second = await deliver(body)
        assert second.status_code == 200, (
            f"Expected 200, got {second.status_code}: {second.text}"
        )
        assert second.json() == {"status": "ok"}

        listing = await client.get(f"{BASE_URL}/messages")
        assert listing.status_code == 200
        matches = [
            m for m in listing.json()["messages"]
            if m.get("external_message_id") == wamid
        ]
        assert len(matches) == 1, f"Expected 1 document, found {len(matches)}"

        # AI runs as a background task after the ack, so poll briefly.
        status = None
        for _ in range(15):
            listing = await client.get(f"{BASE_URL}/messages")
            matches = [
                m for m in listing.json()["messages"]
                if m.get("external_message_id") == wamid
            ]
            assert len(matches) == 1, f"Expected 1 document, found {len(matches)}"
            status = (matches[0].get("ai_analysis") or {}).get("status")
            if status == "completed":
                break
            await asyncio.sleep(2)
        assert status == "completed", (
            f"Expected ai_analysis.status=completed, got {status}"
        )

        print(
            f"[PASS] Day23: Duplicate guard works under signed Meta payloads - "
            f"single document {wamid}, analysis updated in place"
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
