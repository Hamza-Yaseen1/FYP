from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from database import messages_collection
from dependencies import get_current_user
from models.message import message_doc_to_response
from services.ai import analyze_message

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

DUPLICATE_WINDOW = timedelta(minutes=10)


class WhatsAppPayload(BaseModel):
    sender: str
    message: str
    timestamp: str | None = None


@router.post("/whatsapp")
async def whatsapp_webhook(
    payload: WhatsAppPayload, current_user: dict = Depends(get_current_user)
):
    uid = str(current_user["_id"])
    if payload.timestamp:
        created_at = datetime.fromisoformat(payload.timestamp)
    else:
        created_at = datetime.now(timezone.utc)

    # Duplicate guard: re-delivered webhooks update the existing message
    # instead of creating a copy.
    existing = await messages_collection.find_one(
        {
            "user_id": uid,
            "sender": payload.sender,
            "content": payload.message,
            "source": "whatsapp",
            "created_at": {"$gte": created_at - DUPLICATE_WINDOW},
        }
    )

    if existing:
        doc = existing
        message_id = str(existing["_id"])
    else:
        doc = {
            "user_id": uid,
            "sender": payload.sender,
            "content": payload.message,
            "source": "whatsapp",
            "status": "unread",
            "state": "active",
            "created_at": created_at,
            "updated_at": datetime.now(timezone.utc),
        }

        result = await messages_collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        message_id = str(result.inserted_id)

    # Trigger AI analysis synchronously
    ai_analysis = await analyze_message(payload.message, message_id=message_id, user_id=uid)
    await messages_collection.update_one(
        {"_id": doc["_id"]},
        {"$set": {"ai_analysis": ai_analysis}},
    )
    doc["ai_analysis"] = ai_analysis

    return {
        "success": True,
        "message": "WhatsApp message received, analyzed, and stored",
        "data": message_doc_to_response(doc),
    }
