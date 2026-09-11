from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Provider(str, Enum):
    WHATSAPP = "whatsapp"
    GMAIL = "gmail"
    LINKEDIN = "linkedin"


class ConnectionStatus(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    COMING_SOON = "coming_soon"


class ConnectionCreate(BaseModel):
    provider: Provider


class ConnectionResponse(BaseModel):
    id: str
    provider: Provider
    status: ConnectionStatus
    created_at: datetime
    gmail_email: Optional[str] = None


class ConnectionInDB(BaseModel):
    id: Optional[str] = None
    user_id: str
    provider: Provider
    status: ConnectionStatus = ConnectionStatus.DISCONNECTED
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    last_fetched_at: Optional[datetime] = None
    gmail_email: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


def connection_doc_to_response(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "provider": doc["provider"],
        "status": doc["status"],
        "created_at": doc["created_at"],
        "gmail_email": doc.get("gmail_email"),
    }
