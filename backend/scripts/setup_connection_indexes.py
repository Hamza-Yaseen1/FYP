import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "communication_ai")


async def create_indexes():
    client = AsyncIOMotorClient(MONGO_URI, tz_aware=True)
    db = client[DB_NAME]
    connections = db["connections"]

    await connections.create_index(
        [("user_id", 1), ("provider", 1)],
        unique=True,
        name="user_provider_unique"
    )
    await connections.create_index(
        [("user_id", 1)],
        name="user_id_index"
    )
    print("Indexes created successfully")
    client.close()


if __name__ == "__main__":
    asyncio.run(create_indexes())
