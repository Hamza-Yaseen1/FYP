from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, model_serializer

from dependencies import get_current_user
from services.ai.jarvis_agent import process_command, process_confirmation

router = APIRouter(prefix="/jarvis", tags=["jarvis"])


class JarvisChatRequest(BaseModel):
    message: str = ""
    confirmation_token: Optional[str] = None
    confirmed: bool = True


class JarvisAction(BaseModel):
    type: str
    target: Optional[str] = None
    detail: Optional[dict] = None
    confirmation_token: Optional[str] = None

    @model_serializer
    def _serialize(self) -> dict:
        """Serialize with only the fields that are actually set.

        Keeps the Phase 1 wire shape for plain navigation actions
        (``{"type", "target"}``) while still carrying ``detail`` /
        ``confirmation_token`` when present.
        """
        out = {"type": self.type}
        if self.target is not None:
            out["target"] = self.target
        if self.detail is not None:
            out["detail"] = self.detail
        if self.confirmation_token is not None:
            out["confirmation_token"] = self.confirmation_token
        return out


class JarvisChatResponse(BaseModel):
    reply: str
    action: Optional[JarvisAction] = None
    used_ai: bool = False


@router.post("/chat", response_model=JarvisChatResponse)
async def jarvis_chat(
    payload: JarvisChatRequest,
    current_user: dict = Depends(get_current_user),
):
    """Handle one JARVIS command for the authenticated user.

    The owner is always resolved server-side from the session (`get_current_user`),
    never from request payload, so JARVIS can only ever touch the caller's own
    messages / tasks / attention data.

    When ``confirmation_token`` is present the request is a confirm/cancel
    round-trip for a previously-requested action (create/delete task) instead
    of a fresh command; the signed token is re-validated before executing.
    """
    if not payload.message.strip() and not payload.confirmation_token:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    uid = str(current_user["_id"])
    if payload.confirmation_token:
        return await process_confirmation(uid, payload.confirmation_token, payload.confirmed)
    return await process_command(uid, payload.message)