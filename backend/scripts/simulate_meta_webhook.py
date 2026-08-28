"""
Simulate a real Meta WhatsApp webhook POST request to test the endpoint locally.
"""
import hashlib
import hmac
import json
import os
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parent.parent))


def create_signature(payload: str, app_secret: str) -> str:
    """Create Meta's X-Hub-Signature-256 header."""
    signature = hmac.new(
        app_secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"


async def test_webhook():
    """Send a test webhook POST to the local backend."""
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    app_secret = os.getenv("WHATSAPP_APP_SECRET")
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    
    if not app_secret or not phone_number_id:
        print("❌ Missing environment variables!")
        return
    
    # Create a sample Meta webhook payload
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "+15556608724",
                                "phone_number_id": phone_number_id
                            },
                            "contacts": [
                                {
                                    "profile": {
                                        "name": "Test User"
                                    },
                                    "wa_id": "1234567890"
                                }
                            ],
                            "messages": [
                                {
                                    "from": "1234567890",
                                    "id": "wamid.TEST123",
                                    "timestamp": "1234567890",
                                    "text": {
                                        "body": "Hello from test script!"
                                    },
                                    "type": "text"
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }
    
    payload_str = json.dumps(payload)
    signature = create_signature(payload_str, app_secret)
    
    print("=" * 60)
    print("Testing WhatsApp Webhook POST")
    print("=" * 60)
    print(f"\nPayload: {payload_str[:100]}...")
    print(f"Signature: {signature[:30]}...")
    
    # Test against local backend
    url = "http://localhost:8000/webhooks/whatsapp"
    
    headers = {
        "Content-Type": "application/json",
        "X-Hub-Signature-256": signature
    }
    
    print(f"\nSending POST to: {url}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, content=payload_str, headers=headers, timeout=10.0)
            print(f"\n✓ Response Status: {response.status_code}")
            print(f"✓ Response Body: {response.text}")
            
            if response.status_code == 200:
                print("\n✅ Webhook test PASSED!")
                print("Now check your database for the new message:")
                print("  python -m scripts.test_webhook")
            else:
                print(f"\n❌ Webhook test FAILED with status {response.status_code}")
                
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Make sure your backend is running on localhost:8000")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_webhook())
