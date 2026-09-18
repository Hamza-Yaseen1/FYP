from datetime import datetime
from typing import List

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from database import db
from dependencies import get_current_user
from models.connection import ConnectionCreate, Provider
from services.connection import ConnectionService

router = APIRouter(prefix="/connections", tags=["connections"])


@router.get("")
async def list_connections(current_user: dict = Depends(get_current_user)):
    service = ConnectionService(db)
    connections = await service.get_user_connections(str(current_user["_id"]))
    return {"connections": connections}


@router.post("", status_code=201)
async def create_connection(
    payload: ConnectionCreate,
    current_user: dict = Depends(get_current_user)
):
    if payload.provider == Provider.GMAIL:
        raise HTTPException(
            status_code=400,
            detail="Use the Gmail connect flow (GET /connections/gmail/auth-url)",
        )
    service = ConnectionService(db)
    try:
        connection = await service.create_connection(
            str(current_user["_id"]),
            payload.provider
        )
        return connection
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{connection_id}", status_code=204)
async def delete_connection(
    connection_id: str,
    current_user: dict = Depends(get_current_user)
):
    service = ConnectionService(db)
    deleted = await service.delete_connection(connection_id, str(current_user["_id"]))

    if not deleted:
        raise HTTPException(status_code=404, detail="Connection not found")
