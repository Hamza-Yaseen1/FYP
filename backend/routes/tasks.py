from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from bson import ObjectId

from database import tasks_collection
from dependencies import get_current_user

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskStatusUpdate(BaseModel):
    status: str


@router.get("")
async def get_tasks(current_user: dict = Depends(get_current_user)):
    uid = str(current_user["_id"])
    cursor = tasks_collection.find({"user_id": uid}).sort("created_at", -1)
    docs = await cursor.to_list(length=100)
    result = []
    for doc in docs:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
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
