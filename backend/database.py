import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "communication_ai")

client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]

# Collections
messages_collection = db["messages"]
users_collection = db["users"]
ai_analysis_collection = db["ai_analysis"]
tasks_collection = db["tasks"]
connections_collection = db["connections"]
