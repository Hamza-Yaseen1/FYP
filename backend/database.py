import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

import dns.resolver

# Configure dnspython with public DNS resolvers (Google & Cloudflare).
# Local Wi-Fi/ISP/university DNS servers often time out on MongoDB SRV queries.
try:
    resolver = dns.resolver.Resolver(configure=False)
    resolver.nameservers = ["8.8.8.8", "1.1.1.1", "8.8.4.4"]
    dns.resolver.default_resolver = resolver
except Exception:
    pass

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "communication_ai")

# Add connection options for better reliability
client = AsyncIOMotorClient(
    MONGO_URI, 
    tz_aware=True,
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=5000,
)
db = client[DB_NAME]

# Collections
messages_collection = db["messages"]
users_collection = db["users"]
ai_analysis_collection = db["ai_analysis"]
tasks_collection = db["tasks"]
connections_collection = db["connections"]

# Indexes
async def create_indexes():
    # Tasks indexes for priority-based sorting and snooze queries
    await tasks_collection.create_index([("user_id", 1), ("priority_indicator", 1), ("created_at", -1)])
    await tasks_collection.create_index([("user_id", 1), ("snoozed_until", 1)])
