import logging
from datetime import datetime
from typing import List, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from models.connection import ConnectionInDB, ConnectionStatus, Provider
from utils.encryption import encrypt

logger = logging.getLogger(__name__)


class ConnectionService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["connections"]

    async def get_user_connections(self, user_id: str) -> List[dict]:
        logger.debug(f"Fetching connections for user {user_id}")
        cursor = self.collection.find({"user_id": user_id})
        connections = []
        async for doc in cursor:
            connections.append({
                "id": str(doc["_id"]),
                "provider": doc["provider"],
                "status": doc["status"],
                "created_at": doc["created_at"],
            })
        logger.debug(f"Found {len(connections)} connections for user {user_id}")
        return connections

    async def get_connection_by_id(self, connection_id: str, user_id: str) -> Optional[dict]:
        if not ObjectId.is_valid(connection_id):
            return None

        doc = await self.collection.find_one({
            "_id": ObjectId(connection_id),
            "user_id": user_id
        })

        if not doc:
            logger.debug(f"Connection {connection_id} not found for user {user_id}")
            return None

        return {
            "id": str(doc["_id"]),
            "provider": doc["provider"],
            "status": doc["status"],
            "created_at": doc["created_at"],
        }

    async def get_connection_with_tokens(self, connection_id: str, user_id: str) -> Optional[dict]:
        if not ObjectId.is_valid(connection_id):
            return None

        logger.debug(f"Accessing tokens for connection {connection_id} by user {user_id}")
        doc = await self.collection.find_one({
            "_id": ObjectId(connection_id),
            "user_id": user_id
        })

        if not doc:
            logger.debug(f"Connection {connection_id} not found for user {user_id}")
            return None

        logger.debug(f"Tokens accessed for connection {connection_id}")
        return {
            "id": str(doc["_id"]),
            "user_id": doc["user_id"],
            "provider": doc["provider"],
            "status": doc["status"],
            "access_token": doc.get("access_token"),
            "refresh_token": doc.get("refresh_token"),
            "created_at": doc["created_at"],
            "updated_at": doc["updated_at"],
        }

    async def create_connection(self, user_id: str, provider: Provider) -> dict:
        existing = await self.collection.find_one({
            "user_id": user_id,
            "provider": provider.value
        })

        if existing:
            raise ValueError("This account is already connected")

        logger.info(f"Creating connection for user {user_id}, provider {provider.value}")
        now = datetime.utcnow()
        doc = {
            "user_id": user_id,
            "provider": provider.value,
            "status": ConnectionStatus.CONNECTED.value,
            "access_token": encrypt("mock_access_token"),
            "refresh_token": encrypt("mock_refresh_token"),
            "created_at": now,
            "updated_at": now,
        }

        result = await self.collection.insert_one(doc)
        doc["_id"] = result.inserted_id

        logger.info(f"Connection created: {result.inserted_id}")
        return {
            "id": str(doc["_id"]),
            "provider": doc["provider"],
            "status": doc["status"],
            "created_at": doc["created_at"],
        }

    async def delete_connection(self, connection_id: str, user_id: str) -> bool:
        if not ObjectId.is_valid(connection_id):
            return False

        logger.info(f"Deleting connection {connection_id} for user {user_id}")
        result = await self.collection.delete_one({
            "_id": ObjectId(connection_id),
            "user_id": user_id
        })

        if result.deleted_count > 0:
            logger.info(f"Connection {connection_id} deleted")
        else:
            logger.debug(f"Connection {connection_id} not found for deletion")

        return result.deleted_count > 0
