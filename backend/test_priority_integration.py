"""
Priority Agent Integration Tests

Run: python test_priority_integration.py
"""

import asyncio
import sys
import os
import time
import httpx
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://localhost:8000"


async def test_post_whatsapp_source():
    """T030: Test POST /messages with WhatsApp source"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/messages",
            json={
                "sender": "Alice",
                "content": "Hey, can you review the document by tomorrow?",
                "source": "whatsapp",
            },
        )
        assert response.status_code == 201, f"Expected 201, got {response.status_code}"
        data = response.json()
        assert data["source"] == "whatsapp"
        assert "ai_analysis" in data
        print(f"[PASS] T030: WhatsApp message created - ID: {data['id']}")
        return data["id"]


async def test_post_gmail_source():
    """T031: Test POST /messages with Gmail source"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/messages",
            json={
                "sender": "Bob",
                "content": "Meeting scheduled for Friday at 3pm",
                "source": "gmail",
            },
        )
        assert response.status_code == 201, f"Expected 201, got {response.status_code}"
        data = response.json()
        assert data["source"] == "gmail"
        assert "ai_analysis" in data
        print(f"[PASS] T031: Gmail message created - ID: {data['id']}")
        return data["id"]


async def test_post_simulated_source():
    """T032: Test POST /messages with Simulated source"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/messages",
            json={
                "sender": "System",
                "content": "Test message from simulated channel",
                "source": "simulated",
            },
        )
        assert response.status_code == 201, f"Expected 201, got {response.status_code}"
        data = response.json()
        assert data["source"] == "simulated"
        assert "ai_analysis" in data
        print(f"[PASS] T032: Simulated message created - ID: {data['id']}")
        return data["id"]


async def test_priority_override_persists(message_id: str):
    """T033: Test priority override persists after page refresh"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Override priority
        response = await client.put(
            f"{BASE_URL}/messages/{message_id}/priority",
            params={"priority": "urgent"},
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data["ai_analysis"]["priority"] == "urgent"
        assert data["ai_analysis"]["confidence"] == 1.0
        assert data["ai_analysis"]["explanation"] == "User override"
        
        # Simulate page refresh by fetching the message
        response2 = await client.get(f"{BASE_URL}/messages/{message_id}")
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["ai_analysis"]["priority"] == "urgent"
        
        print(f"[PASS] T033: Priority override persists after refresh")


async def test_dashboard_auto_polls():
    """T034: Test dashboard auto-polls and shows new priorities"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Create a message
        response = await client.post(
            f"{BASE_URL}/messages",
            json={
                "sender": "PollTest",
                "content": "Testing auto-poll functionality",
                "source": "simulated",
            },
        )
        assert response.status_code == 201
        msg_id = response.json()["id"]
        
        # Wait a moment
        await asyncio.sleep(0.5)
        
        # Fetch all messages (simulating dashboard poll)
        response2 = await client.get(f"{BASE_URL}/messages")
        assert response2.status_code == 200
        messages = response2.json()
        
        # Verify our message is in the list
        found = any(m["id"] == msg_id for m in messages)
        assert found, "Message not found in dashboard list"
        
        print(f"[PASS] T034: Dashboard auto-polls and shows new priorities")


async def test_80_percent_accuracy():
    """T035: Verify 80% accuracy on test set"""
    test_cases = [
        ("URGENT: Client demo in 2 hours, need the final presentation now!", "urgent"),
        ("Server is down, all customers affected, need fix ASAP", "urgent"),
        ("Please send me the project report by Friday", "important"),
        ("We have a meeting tomorrow at 3pm, please prepare slides", "important"),
        ("Hey, want to grab lunch sometime this week?", "normal"),
        ("FYI, I updated the shared document", "normal"),
        ("Your subscription has been renewed", "low"),
        ("Weekly newsletter: Top 10 productivity tips", "low"),
    ]
    
    correct = 0
    total = len(test_cases)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for message, expected in test_cases:
            response = await client.post(
                f"{BASE_URL}/messages",
                json={
                    "sender": "TestUser",
                    "content": message,
                    "source": "simulated",
                },
            )
            if response.status_code == 201:
                data = response.json()
                actual = data["ai_analysis"]["priority"]
                if actual == expected:
                    correct += 1
                else:
                    print(f"  [MISS] '{message[:50]}...' - Expected: {expected}, Got: {actual}")
    
    accuracy = correct / total if total > 0 else 0
    print(f"[{'PASS' if accuracy >= 0.8 else 'FAIL'}] T035: Accuracy: {accuracy:.0%} ({correct}/{total})")
    
    return accuracy >= 0.8


async def test_response_time():
    """T036: Verify response time < 2 seconds"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        start = time.time()
        response = await client.post(
            f"{BASE_URL}/messages",
            json={
                "sender": "SpeedTest",
                "content": "Test response time",
                "source": "simulated",
            },
        )
        elapsed = time.time() - start
        
        assert response.status_code == 201
        print(f"[{'PASS' if elapsed < 2 else 'FAIL'}] T036: Response time: {elapsed:.2f}s")
        return elapsed < 2


async def test_graceful_ai_failure():
    """T037: Verify no crashes on AI failure"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        # This should not crash even if AI is unavailable
        response = await client.post(
            f"{BASE_URL}/messages",
            json={
                "sender": "FailTest",
                "content": "Testing AI failure handling",
                "source": "simulated",
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify graceful fallback
        assert data["ai_analysis"]["priority"] in ["normal", "pending"]
        assert data["ai_analysis"]["confidence"] == 0.0
        assert data["ai_analysis"]["status"] == "pending"
        
        print(f"[PASS] T037: Graceful AI failure handling works")
        return True


async def main():
    print("=" * 60)
    print("Priority Agent Integration Tests")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    # T030-T032: Source tests
    try:
        msg_id = await test_post_whatsapp_source()
        passed += 1
    except Exception as e:
        print(f"[FAIL] T030: {e}")
        failed += 1
        msg_id = None
    
    try:
        await test_post_gmail_source()
        passed += 1
    except Exception as e:
        print(f"[FAIL] T031: {e}")
        failed += 1
    
    try:
        await test_post_simulated_source()
        passed += 1
    except Exception as e:
        print(f"[FAIL] T032: {e}")
        failed += 1
    
    # T033: Override persistence
    if msg_id:
        try:
            await test_priority_override_persists(msg_id)
            passed += 1
        except Exception as e:
            print(f"[FAIL] T033: {e}")
            failed += 1
    else:
        print("[SKIP] T033: No message ID available")
    
    # T034: Auto-poll
    try:
        await test_dashboard_auto_polls()
        passed += 1
    except Exception as e:
        print(f"[FAIL] T034: {e}")
        failed += 1
    
    # T035: Accuracy
    try:
        await test_80_percent_accuracy()
        passed += 1
    except Exception as e:
        print(f"[FAIL] T035: {e}")
        failed += 1
    
    # T036: Response time
    try:
        await test_response_time()
        passed += 1
    except Exception as e:
        print(f"[FAIL] T036: {e}")
        failed += 1
    
    # T037: Graceful failure
    try:
        await test_graceful_ai_failure()
        passed += 1
    except Exception as e:
        print(f"[FAIL] T037: {e}")
        failed += 1
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
