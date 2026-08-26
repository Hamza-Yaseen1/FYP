from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from bson import ObjectId

from database import tasks_collection, messages_collection
from dependencies import get_current_user

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskStatusUpdate(BaseModel):
    status: str


class SnoozeRequest(BaseModel):
    duration: str


@router.get("")
async def get_tasks(current_user: dict = Depends(get_current_user)):
    uid = str(current_user["_id"])
    now = datetime.now(timezone.utc)
    
    # Build query: exclude completed tasks, exclude currently snoozed tasks
    query = {
        "user_id": uid,
        "status": {"$ne": "completed"},
        "$or": [
            {"snoozed_until": {"$exists": False}},
            {"snoozed_until": {"$lte": now}}
        ]
    }
    
    # Aggregation pipeline for priority-based sorting
    pipeline = [
        {"$match": query},
        {"$addFields": {
            "priority_order": {
                "$switch": {
                    "branches": [
                        {"case": {"$eq": ["$priority_indicator", "urgent"]}, "then": 1},
                        {"case": {"$eq": ["$priority_indicator", "important"]}, "then": 2},
                        {"case": {"$eq": ["$priority_indicator", "normal"]}, "then": 3}
                    ],
                    "default": 4
                }
            }
        }},
        {"$sort": {"priority_order": 1, "created_at": -1}},
        {"$limit": 100}
    ]
    
    cursor = tasks_collection.aggregate(pipeline)
    docs = await cursor.to_list(length=100)
    result = []
    for doc in docs:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
        # Add is_snoozed computed field
        doc["is_snoozed"] = doc.get("snoozed_until") and doc["snoozed_until"] > now
        result.append(doc)
    return result


@router.put("/{task_id}/status")
async def update_task_status(
    task_id: str,
    payload: TaskStatusUpdate,
    current_user: dict = Depends(get_current_user),
):
    if not ObjectId.is_valid(task_id):
        raise HTTPException(status_code=404)

    if payload.status not in ["pending", "in_progress", "completed"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid status. Must be: pending, in_progress, or completed",
        )

    now = datetime.now(timezone.utc)
    uid = str(current_user["_id"])
    result = await tasks_collection.find_one_and_update(
        {"_id": ObjectId(task_id), "user_id": uid},
        {"$set": {"status": payload.status, "updated_at": now}},
        return_document=True,
    )
    if not result:
        raise HTTPException(status_code=404)

    result["id"] = str(result["_id"])
    del result["_id"]
    return result


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: str, current_user: dict = Depends(get_current_user)
):
    if not ObjectId.is_valid(task_id):
        raise HTTPException(status_code=404)

    uid = str(current_user["_id"])
    result = await tasks_collection.delete_one(
        {"_id": ObjectId(task_id), "user_id": uid}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404)


@router.put("/{task_id}/snooze")
async def snooze_task(
    task_id: str,
    payload: SnoozeRequest,
    current_user: dict = Depends(get_current_user),
):
    if not ObjectId.is_valid(task_id):
        raise HTTPException(status_code=404)
    
    if payload.duration not in ["1hour", "tomorrow", "nextweek"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid duration. Must be: 1hour, tomorrow, or nextweek",
        )
    
    now = datetime.now(timezone.utc)
    uid = str(current_user["_id"])
    
    # Calculate snooze duration
    if payload.duration == "1hour":
        snooze_until = now + timedelta(hours=1)
    elif payload.duration == "tomorrow":
        # Tomorrow at same time
        snooze_until = now + timedelta(days=1)
    else:  # nextweek
        snooze_until = now + timedelta(weeks=1)
    
    result = await tasks_collection.find_one_and_update(
        {"_id": ObjectId(task_id), "user_id": uid},
        {"$set": {"snoozed_until": snooze_until, "updated_at": now}},
        return_document=True,
    )
    if not result:
        raise HTTPException(status_code=404)
    
    result["id"] = str(result["_id"])
    del result["_id"]
    return result


@router.get("/{task_id}/message")
async def get_task_message(
    task_id: str,
    current_user: dict = Depends(get_current_user),
):
    if not ObjectId.is_valid(task_id):
        raise HTTPException(status_code=404)
    
    uid = str(current_user["_id"])
    
    # First get the task to verify ownership and get source_message_id
    task = await tasks_collection.find_one(
        {"_id": ObjectId(task_id), "user_id": uid}
    )
    if not task:
        raise HTTPException(status_code=404)
    
    source_message_id = task.get("source_message_id")
    if not source_message_id or not ObjectId.is_valid(source_message_id):
        raise HTTPException(status_code=404, detail="Source message not found")
    
    # Fetch the original message
    message = await messages_collection.find_one(
        {"_id": ObjectId(source_message_id), "user_id": uid}
    )
    if not message:
        raise HTTPException(status_code=404, detail="Source message not found")
    
    # Convert to response format
    message["id"] = str(message["_id"])
    del message["_id"]
    return message
