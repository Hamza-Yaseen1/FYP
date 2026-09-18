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
                "gmail_email": doc.get("gmail_email"),
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
            "gmail_email": doc.get("gmail_email"),
        }

    async def upsert_gmail_connection(
        self,
        user_id: str,
        access_token: str,
        refresh_token: str,
        token_expires_at: datetime,
        gmail_email: Optional[str] = None,
    ) -> None:
        """Create or replace the user's Gmail connection with new tokens.

        Tokens must already be encrypted by the caller. Gmail is single
        connection per user, so a prior row for the same user is overwritten
        (spec assumption: connecting again re-establishes the connection).
        """
        now = datetime.utcnow()
        await self.collection.update_one(
            {"user_id": user_id, "provider": Provider.GMAIL.value},
            {
                "$set": {
                    "status": ConnectionStatus.CONNECTED.value,
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "token_expires_at": token_expires_at,
                    "gmail_email": gmail_email,
                    "updated_at": now,
                },
                "$setOnInsert": {
                    "created_at": now,
                },
            },
            upsert=True,
        )
        logger.info(
            f"Gmail connection upserted for user {user_id} "
            f"(email={gmail_email or 'unknown'})"
        )

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

    async def update_gmail_tokens(
        self,
        connection_id: str,
        user_id: str,
        access_token: str,
        token_expires_at: datetime,
    ) -> bool:
        """Refresh the stored (already-encrypted) access token in place."""
        if not ObjectId.is_valid(connection_id):
            return False
        result = await self.collection.update_one(
            {"_id": ObjectId(connection_id), "user_id": user_id},
            {
                "$set": {
                    "access_token": access_token,
                    "token_expires_at": token_expires_at,
                    "updated_at": datetime.utcnow(),
                }
            },
        )
        return result.modified_count > 0

    async def set_connection_error(self, connection_id: str, user_id: str) -> bool:
        """Flip a connection to the error state (e.g. revoked Google token)."""
        if not ObjectId.is_valid(connection_id):
            return False
        result = await self.collection.update_one(
            {"_id": ObjectId(connection_id), "user_id": user_id},
            {
                "$set": {
                    "status": ConnectionStatus.ERROR.value,
                    "updated_at": datetime.utcnow(),
                }
            },
        )
        return result.modified_count > 0

    async def delete_connection(self, connection_id: str, user_id: str) -> bool:
        """Delete a connection. For Gmail, revoke the Google OAuth grant first.

        Revocation is best-effort: failure is logged but does not prevent
        the DB row from being removed (the user sees success either way).
        """
        if not ObjectId.is_valid(connection_id):
            return False

        # Fetch doc before deleting so we can revoke Gmail tokens
        doc = await self.collection.find_one({
            "_id": ObjectId(connection_id),
            "user_id": user_id,
        })
        if not doc:
            logger.debug(f"Connection {connection_id} not found for deletion")
            return False

        # Best-effort Google revoke for Gmail connections
        if doc.get("provider") == "gmail" and doc.get("refresh_token"):
            try:
                from services.gmail import revoke_google_access
                await revoke_google_access(doc["refresh_token"])
            except Exception:
                logger.warning(
                    "Gmail revoke failed for connection %s — proceeding with delete",
                    connection_id,
                    exc_info=True,
                )

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
