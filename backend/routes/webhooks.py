import hashlib
import hmac
import logging
import os
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, Query, HTTPException, Request, BackgroundTasks, Depends
from fastapi.responses import PlainTextResponse
from pydantic import ValidationError

from database import connections_collection, messages_collection
from models.message import SimulateMessageRequest, message_doc_to_response
from models.meta_webhook import MetaMessage, MetaValue, MetaWebhookPayload
from routes.auth import get_current_user
from services.webhook_ingest import ingest_message

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)

VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")


def _app_secret() -> str:
    return os.getenv("WHATSAPP_APP_SECRET", "")


def verify_signature(raw_body: bytes, signature_header: Optional[str]) -> bool:
    """Verify Meta's X-Hub-Signature-256 against the App Secret.

    Comparison is constant-time (hmac.compare_digest). An unconfigured App
    Secret rejects every delivery.
    """
    secret = _app_secret()
    if not secret:
        logger.warning("Webhook rejected: WHATSAPP_APP_SECRET not configured")
        return False
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    provided = signature_header[len("sha256=") :]
    expected = hmac.new(
        secret.encode("utf-8"), raw_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, provided)


def _resolve_sender(value: MetaValue, msg: MetaMessage) -> str:
    if value.contacts:
        profile = value.contacts[0].profile
        if profile and profile.name:
            return profile.name
    return msg.from_


def _message_content(msg: MetaMessage) -> str:
    if msg.type == "text" and msg.text and msg.text.body:
        return msg.text.body
    return ""


def _message_type(msg: MetaMessage) -> str:
    return "text" if msg.type == "text" else "media"


async def _resolve_owner() -> Optional[str]:
    """Owning user for inbound WhatsApp messages, resolved server-side from
    the connected WhatsApp connection. Never derived from the payload."""
    connection = await connections_collection.find_one(
        {"provider": "whatsapp", "status": "connected"}
    )
    if connection is None:
        return None
    return connection["user_id"]


@router.get("/whatsapp")
async def verify_whatsapp_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge"),
):
    """
    Meta WhatsApp webhook verification endpoint.
    Meta sends a GET request with hub.mode, hub.verify_token, and hub.challenge.
    If the verify token matches, we return the challenge to complete verification.
    """
    logger.info("Webhook verification requested: mode=%s", hub_mode)

    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        logger.info("Webhook verification succeeded")
        return PlainTextResponse(content=hub_challenge)

    logger.warning("Webhook verification failed: mode=%s", hub_mode)
    raise HTTPException(status_code=403, detail="Verification token mismatch")


@router.post("/simulate")
async def simulate_webhook(
    payload: SimulateMessageRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """
    Debug/test endpoint mirroring the real Meta flow (T021). Requires the
    authenticated user; ingests with source="simulate" so it is visually
    distinct from real WhatsApp messages and never processed as real traffic.
    """
    uid = str(current_user["_id"])
    message_id = await ingest_message(
        user_id=uid,
        source="simulate",
        sender=payload.sender,
        content=payload.message,
        message_type="text",
        background_tasks=background_tasks,
    )
    doc = await messages_collection.find_one({"_id": ObjectId(message_id)})
    return message_doc_to_response(doc)


@router.post("/whatsapp")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    raw = await request.body()

    if not verify_signature(raw, request.headers.get("X-Hub-Signature-256")):
        raise HTTPException(status_code=403, detail="Invalid signature")

    try:
        payload = MetaWebhookPayload.model_validate_json(raw)
    except ValidationError as exc:
        logger.warning("Webhook delivery rejected: malformed payload (%s)", exc)
        raise HTTPException(status_code=400, detail="Invalid payload")

    owner_id = await _resolve_owner()

    for entry in payload.entry or []:
        for change in entry.changes:
            if change.field != "messages":
                continue
            value = change.value
            if not value.messages:
                continue

            phone_number_id = (
                value.metadata.phone_number_id if value.metadata else None
            )
            if phone_number_id != WHATSAPP_PHONE_NUMBER_ID:
                logger.info(
                    "Delivery ignored: phone number id %s is not ours",
                    phone_number_id,
                )
                continue

            if owner_id is None:
                logger.info(
                    "Delivery ignored: no connected whatsapp owner"
                )
                continue

            for msg in value.messages:
                await ingest_message(
                    user_id=owner_id,
                    source="whatsapp",
                    sender=_resolve_sender(value, msg),
                    content=_message_content(msg),
                    external_message_id=msg.id,
                    message_type=_message_type(msg),
                    background_tasks=background_tasks,
                )

    logger.info("Webhook delivery acknowledged")
    return {"status": "ok"}