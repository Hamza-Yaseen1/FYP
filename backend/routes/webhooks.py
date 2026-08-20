from datetime import datetime, timezone
from fastapi import APIRouter
from pydantic import BaseModel

from database import messages_collection
from models.message import message_doc_to_response
from services.ai import analyze_message

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


class WhatsAppPayload(BaseModel):
    sender: str
    message: str
    timestamp: str | None = None


@router.post("/whatsapp")
async def whatsapp_webhook(payload: WhatsAppPayload):
    if payload.timestamp:
        created_at = datetime.fromisoformat(payload.timestamp)
    else:
        created_at = datetime.now(timezone.utc)

    doc = {
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

    # Trigger AI analysis synchronously
    ai_analysis = await analyze_message(payload.message, message_id=str(result.inserted_id))
    await messages_collection.update_one(
        {"_id": result.inserted_id},
        {"$set": {"ai_analysis": ai_analysis}},
    )
    doc["ai_analysis"] = ai_analysis

    return {
        "success": True,
        "message": "WhatsApp message received, analyzed, and stored",
        "data": message_doc_to_response(doc),
    }
