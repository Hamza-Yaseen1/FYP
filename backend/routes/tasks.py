from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from bson import ObjectId

from database import tasks_collection

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskStatusUpdate(BaseModel):
    status: str


@router.get("")
async def get_tasks():
    cursor = tasks_collection.find().sort("created_at", -1)
    docs = await cursor.to_list(length=100)
    result = []
    for doc in docs:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
        result.append(doc)
    return result


@router.put("/{task_id}/status")
async def update_task_status(task_id: str, payload: TaskStatusUpdate):
    if not ObjectId.is_valid(task_id):
        raise HTTPException(status_code=400, detail="Invalid task ID")

    if payload.status not in ["pending", "in_progress", "completed"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid status. Must be: pending, in_progress, or completed",
        )

    now = datetime.now(timezone.utc)
    result = await tasks_collection.find_one_and_update(
        {"_id": ObjectId(task_id)},
        {"$set": {"status": payload.status, "updated_at": now}},
        return_document=True,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")

    result["id"] = str(result["_id"])
    del result["_id"]
    return result


@router.delete("/{task_id}", status_code=204)
async def delete_task(task_id: str):
    if not ObjectId.is_valid(task_id):
        raise HTTPException(status_code=400, detail="Invalid task ID")

    result = await tasks_collection.delete_one({"_id": ObjectId(task_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
