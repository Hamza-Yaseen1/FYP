from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional
from bson import ObjectId


class MessageCreate(BaseModel):
    sender: str
    content: str
    source: str
    status: str = "unread"


class MessageUpdate(BaseModel):
    sender: Optional[str] = None
    content: Optional[str] = None
    source: Optional[str] = None
    status: Optional[str] = None


class MessageResponse(BaseModel):
    id: str
    sender: str
    content: str
    source: str
    status: str
    created_at: datetime
    updated_at: datetime


def message_doc_to_response(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "sender": doc["sender"],
        "content": doc["content"],
        "source": doc["source"],
        "status": doc["status"],
        "created_at": doc["created_at"],
        "updated_at": doc["updated_at"],
    }
