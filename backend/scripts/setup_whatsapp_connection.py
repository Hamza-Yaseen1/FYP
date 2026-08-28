"""
Setup script to create a WhatsApp connection for the first user in the database.
This is required for the webhook to route incoming messages to the correct user.

Usage:
    python -m scripts.setup_whatsapp_connection
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path so we can import from backend
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import db
from services.connection import ConnectionService
from models.connection import Provider


async def main():
    """Create a WhatsApp connection for the first user in the database."""
    users_collection = db["users"]
    
    # Find the first user (or you can specify an email)
    user = await users_collection.find_one({})
    
    if not user:
        print("❌ No users found in database. Please create a user account first.")
        print("   You can do this by signing up through the web interface.")
        return
    
    user_id = str(user["_id"])
    print(f"✓ Found user: {user.get('email', user_id)}")
    
    # Check if WhatsApp connection already exists
    connection_service = ConnectionService(db)
    connections = await connection_service.get_user_connections(user_id)
    
    whatsapp_connection = next(
        (c for c in connections if c["provider"] == "whatsapp"),
        None
    )
    
    if whatsapp_connection:
        print(f"✓ WhatsApp connection already exists (ID: {whatsapp_connection['id']})")
        print(f"  Status: {whatsapp_connection['status']}")
        return
    
    # Create WhatsApp connection
    try:
        connection = await connection_service.create_connection(
            user_id,
            Provider.WHATSAPP
        )
        print(f"✓ WhatsApp connection created successfully!")
        print(f"  Connection ID: {connection['id']}")
        print(f"  Status: {connection['status']}")
        print(f"\n✓ Your webhook is now ready to receive messages!")
    except ValueError as e:
        print(f"❌ Error creating connection: {e}")


if __name__ == "__main__":
    asyncio.run(main())
