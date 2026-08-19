from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from bson import ObjectId

from database import messages_collection
from models.message import (
    MessageCreate,
    MessageUpdate,
    MessageResponse,
    message_doc_to_response,
)
from services.ai import analyze_message

router = APIRouter(prefix="/messages", tags=["messages"])


@router.post("", response_model=MessageResponse, status_code=201)
async def create_message(payload: MessageCreate):
    now = datetime.now(timezone.utc)
    doc = {
        **payload.model_dump(),
        "state": "active",
        "created_at": now,
        "updated_at": now,
    }
    result = await messages_collection.insert_one(doc)
    doc["_id"] = result.inserted_id

    ai_analysis = await analyze_message(payload.content)
    await messages_collection.update_one(
        {"_id": result.inserted_id},
        {"$set": {"ai_analysis": ai_analysis}},
    )
    doc["ai_analysis"] = ai_analysis

    return message_doc_to_response(doc)


@router.get("", response_model=list[MessageResponse])
async def get_messages():
    cursor = messages_collection.find().sort("created_at", -1)
    docs = await cursor.to_list(length=100)
    return [message_doc_to_response(doc) for doc in docs]


@router.get("/{message_id}", response_model=MessageResponse)
async def get_message(message_id: str):
    if not ObjectId.is_valid(message_id):
        raise HTTPException(status_code=400, detail="Invalid message ID")

    doc = await messages_collection.find_one({"_id": ObjectId(message_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Message not found")

    return message_doc_to_response(doc)


@router.put("/{message_id}", response_model=MessageResponse)
async def update_message(message_id: str, payload: MessageUpdate):
    if not ObjectId.is_valid(message_id):
        raise HTTPException(status_code=400, detail="Invalid message ID")

    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    updates["updated_at"] = datetime.now(timezone.utc)

    result = await messages_collection.find_one_and_update(
        {"_id": ObjectId(message_id)},
        {"$set": updates},
        return_document=True,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Message not found")

    return message_doc_to_response(result)


@router.delete("/{message_id}", status_code=204)
async def delete_message(message_id: str):
    if not ObjectId.is_valid(message_id):
        raise HTTPException(status_code=400, detail="Invalid message ID")

    result = await messages_collection.delete_one({"_id": ObjectId(message_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Message not found")
