"""
Quick test script for AI analysis
Run with: python test_ai_analysis.py
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from services.ai import analyze_message


async def test_urgent_message():
    print("\n" + "="*60)
    print("🧪 TEST 1: URGENT MESSAGE")
    print("="*60)
    
    message = "Please send the FYP slides tonight. It's urgent."
    print(f"Message: {message}")
    
    result = await analyze_message(message)
    
    print("\n📊 RESULT:")
    print(f"  Priority: {result['priority']}")
    print(f"  Confidence: {result['confidence']}")
    print(f"  Explanation: {result['explanation']}")
    print(f"  Tasks: {result['tasks_extracted']}")
    print(f"  Deadlines: {result['deadlines']}")
    print(f"  Actions: {result['recommended_actions']}")
    print(f"  Status: {result['status']}")
    
    # Validate
    assert result['status'] == 'completed', f"Expected status='completed', got '{result['status']}'"
    assert result['priority'] == 'urgent', f"Expected priority='urgent', got '{result['priority']}'"
    assert result['confidence'] > 0.7, f"Expected confidence > 0.7, got {result['confidence']}"
    
    print("\n✅ TEST 1 PASSED!")
    return result


async def test_task_extraction():
    print("\n" + "="*60)
    print("🧪 TEST 2: TASK EXTRACTION")
    print("="*60)
    
    message = "Please review the document and send feedback by Friday. Also schedule a meeting."
    print(f"Message: {message}")
    
    result = await analyze_message(message)
    
    print("\n📊 RESULT:")
    print(f"  Priority: {result['priority']}")
    print(f"  Confidence: {result['confidence']}")
    print(f"  Tasks: {result['tasks_extracted']}")
    print(f"  Deadlines: {result['deadlines']}")
    print(f"  Status: {result['status']}")
    
    # Validate
    assert result['status'] == 'completed', f"Expected status='completed', got '{result['status']}'"
    assert len(result['tasks_extracted']) > 0, "Expected tasks to be extracted"
    
    print("\n✅ TEST 2 PASSED!")
    return result


async def test_normal_message():
    print("\n" + "="*60)
    print("🧪 TEST 3: NORMAL MESSAGE")
    print("="*60)
    
    message = "Hi! Just wanted to share this interesting article with you."
    print(f"Message: {message}")
    
    result = await analyze_message(message)
    
    print("\n📊 RESULT:")
    print(f"  Priority: {result['priority']}")
    print(f"  Confidence: {result['confidence']}")
    print(f"  Explanation: {result['explanation']}")
    print(f"  Status: {result['status']}")
    
    # Validate
    assert result['status'] == 'completed', f"Expected status='completed', got '{result['status']}'"
    
    print("\n✅ TEST 3 PASSED!")
    return result


async def main():
    print("\n🚀 STARTING AI ANALYSIS TESTS")
    print("="*60)
    
    try:
        await test_urgent_message()
        await test_task_extraction()
        await test_normal_message()
        
        print("\n" + "="*60)
        print("🎉 ALL TESTS PASSED!")
        print("="*60)
        print("\n✅ AI Analysis is working correctly!")
        print("✅ Priority classification works!")
        print("✅ Task extraction works!")
        print("✅ Urgent messages are detected!")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
