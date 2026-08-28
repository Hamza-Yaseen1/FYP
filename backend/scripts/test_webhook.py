"""
Test script to simulate a WhatsApp webhook delivery and debug issues.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database import connections_collection, messages_collection


async def check_setup():
    """Verify the webhook setup is correct."""
    print("=" * 60)
    print("WhatsApp Webhook Setup Check")
    print("=" * 60)
    
    # 1. Check for WhatsApp connection
    print("\n1. Checking for WhatsApp connection...")
    connection = await connections_collection.find_one(
        {"provider": "whatsapp", "status": "connected"}
    )
    
    if not connection:
        print("   ❌ No connected WhatsApp connection found!")
        print("   Run: python -m scripts.setup_whatsapp_connection")
        return False
    
    print(f"   ✓ WhatsApp connection found")
    print(f"     User ID: {connection['user_id']}")
    print(f"     Status: {connection['status']}")
    print(f"     Created: {connection['created_at']}")
    
    # 2. Check environment variables
    print("\n2. Checking environment variables...")
    import os
    
    phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN")
    app_secret = os.getenv("WHATSAPP_APP_SECRET")
    
    if not phone_id:
        print("   ❌ WHATSAPP_PHONE_NUMBER_ID not set")
    else:
        print(f"   ✓ WHATSAPP_PHONE_NUMBER_ID: {phone_id}")
    
    if not verify_token:
        print("   ❌ WHATSAPP_VERIFY_TOKEN not set")
    else:
        print(f"   ✓ WHATSAPP_VERIFY_TOKEN: {verify_token}")
    
    if not app_secret:
        print("   ❌ WHATSAPP_APP_SECRET not set")
    else:
        print(f"   ✓ WHATSAPP_APP_SECRET: {app_secret[:10]}...")
    
    # 3. Check recent messages
    print("\n3. Checking recent WhatsApp messages...")
    count = await messages_collection.count_documents({
        "user_id": connection['user_id'],
        "source": "whatsapp"
    })
    print(f"   Total WhatsApp messages: {count}")
    
    # Get the 5 most recent
    cursor = messages_collection.find({
        "user_id": connection['user_id'],
        "source": "whatsapp"
    }).sort("created_at", -1).limit(5)
    
    messages = await cursor.to_list(length=5)
    if messages:
        print(f"\n   Recent messages:")
        for msg in messages:
            print(f"     - {msg['sender']}: {msg['content'][:50]}... ({msg['created_at']})")
    else:
        print("   No WhatsApp messages found yet")
    
    print("\n" + "=" * 60)
    print("Setup Check Complete")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    asyncio.run(check_setup())
