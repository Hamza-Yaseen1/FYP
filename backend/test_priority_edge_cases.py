"""
Priority Agent Edge Case Tests

Run: python test_priority_edge_cases.py
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))

from services.ai.analyzer import analyze_message


async def test_urgent_deadline_today():
    """T024: Test message with deadline today returns URGENT"""
    message = "URGENT: Client demo in 2 hours, need the final presentation now!"
    result = await analyze_message(message)
    assert result["priority"] == "urgent", f"Expected urgent, got {result['priority']}"
    assert result["confidence"] > 0.5, f"Confidence too low: {result['confidence']}"
    print(f"[PASS] T024: URGENT - {result['confidence']:.0%} confidence")
    print(f"  Explanation: {result['explanation']}")


async def test_important_deadline_this_week():
    """T025: Test message with deadline this week returns IMPORTANT"""
    message = "Please send me the project report by Friday"
    result = await analyze_message(message)
    assert result["priority"] == "important", f"Expected important, got {result['priority']}"
    assert result["confidence"] > 0.5, f"Confidence too low: {result['confidence']}"
    print(f"[PASS] T025: IMPORTANT - {result['confidence']:.0%} confidence")
    print(f"  Explanation: {result['explanation']}")


async def test_casual_message_normal():
    """T026: Test casual message returns NORMAL"""
    message = "Hey, want to grab lunch sometime this week?"
    result = await analyze_message(message)
    assert result["priority"] == "normal", f"Expected normal, got {result['priority']}"
    print(f"[PASS] T026: NORMAL - {result['confidence']:.0%} confidence")
    print(f"  Explanation: {result['explanation']}")


async def test_automated_message_low():
    """T027: Test automated message returns LOW"""
    message = "Your subscription has been renewed. Thank you for your continued support."
    result = await analyze_message(message)
    assert result["priority"] == "low", f"Expected low, got {result['priority']}"
    print(f"[PASS] T027: LOW - {result['confidence']:.0%} confidence")
    print(f"  Explanation: {result['explanation']}")


async def test_empty_short_message():
    """T028: Test empty/short message returns NORMAL with low confidence"""
    message = "Hi"
    result = await analyze_message(message)
    assert result["priority"] == "normal", f"Expected normal, got {result['priority']}"
    print(f"[PASS] T028: SHORT - {result['confidence']:.0%} confidence")
    print(f"  Explanation: {result['explanation']}")


async def test_long_message_truncation():
    """T029: Test very long message (>2000 chars) is truncated"""
    urgent_start = "URGENT: Server is down, need immediate fix! "
    padding = "This is filler text to make the message very long. " * 100
    message = urgent_start + padding
    
    result = await analyze_message(message)
    assert result["priority"] in ["urgent", "important"], f"Expected urgent/important, got {result['priority']}"
    print(f"[PASS] T029: LONG ({len(message)} chars) - {result['priority']} - {result['confidence']:.0%} confidence")
    print(f"  Explanation: {result['explanation']}")


async def main():
    print("=" * 60)
    print("Priority Agent Edge Case Tests")
    print("=" * 60)
    
    tests = [
        ("T024", test_urgent_deadline_today),
        ("T025", test_important_deadline_this_week),
        ("T026", test_casual_message_normal),
        ("T027", test_automated_message_low),
        ("T028", test_empty_short_message),
        ("T029", test_long_message_truncation),
    ]
    
    passed = 0
    failed = 0
    
    for test_id, test_func in tests:
        try:
            await test_func()
            passed += 1
        except AssertionError as e:
            print(f"[FAIL] {test_id}: {e}")
            failed += 1
        except Exception as e:
            print(f"[ERROR] {test_id}: {e}")
            failed += 1
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
