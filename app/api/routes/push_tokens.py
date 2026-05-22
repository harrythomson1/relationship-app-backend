import logging
import os

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from app.api.auth.utils import get_current_user
from app.api.dependencies import get_push_notifications_service
from app.api.services.push_notifications_service import PushNotificationsService
from app.api.utils.push_client import PushDeliveryError

router = APIRouter(prefix="/me/push-tokens", tags=["push-notifications"])
logger = logging.getLogger(__name__)

push_service_dependency = Depends(get_push_notifications_service)
get_current_user_dependency = Depends(get_current_user)


class PushTokenCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str = Field(min_length=1, max_length=255)
    platform: str | None = Field(default=None, max_length=16)


@router.post("", status_code=status.HTTP_201_CREATED)
async def register_push_token(
    body: PushTokenCreate,
    service: PushNotificationsService = push_service_dependency,
    current_user=get_current_user_dependency,
):
    row = await service.register(user_id=current_user.id, token=body.token, platform=body.platform)
    return {"id": row.id, "token": row.token, "platform": row.platform}


@router.delete("/{token:path}", status_code=status.HTTP_204_NO_CONTENT)
async def unregister_push_token(
    token: str,
    service: PushNotificationsService = push_service_dependency,
    current_user=get_current_user_dependency,
):
    await service.unregister(token)


@router.post("/test")
async def send_test_push(
    service: PushNotificationsService = push_service_dependency,
    current_user=get_current_user_dependency,
):
    # Diagnostic-only endpoint; disabled unless explicitly enabled for an env.
    if os.getenv("ENABLE_TEST_PUSH_ENDPOINT", "false").lower() != "true":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"message": "Not found"})
    try:
        result = await service.send_to_user(
            user_id=current_user.id,
            title="Anywhere",
            body="Hello from your own device 🧡",
            data={"type": "test"},
        )
    except PushDeliveryError as e:
        raise HTTPException(status_code=502, detail={"message": str(e)}) from e
    return {"sent": result.sent, "removed_dead_tokens": len(result.dead_tokens)}
