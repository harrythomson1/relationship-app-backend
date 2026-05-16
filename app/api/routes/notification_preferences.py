from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict

from app.api.auth.utils import get_current_user
from app.api.core.database_connection import get_db
from app.api.notifications.keys import ALL_KEYS, NotificationKey
from app.api.repositories.notification_preferences_repository import (
    NotificationPreferencesRepository,
)

router = APIRouter(prefix="/me/notification-preferences", tags=["notifications"])

get_db_dependency = Depends(get_db)
get_current_user_dependency = Depends(get_current_user)


class PreferencesResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    overlap_opening: bool = True
    countdown_updated: bool = True


class PreferencesUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    overlap_opening: bool | None = None
    countdown_updated: bool | None = None


def _build_response(opt_outs: set[str]) -> PreferencesResponse:
    return PreferencesResponse(
        **{key.value: key.value not in opt_outs for key in ALL_KEYS},
    )


@router.get("", response_model=PreferencesResponse)
async def get_preferences(
    db=get_db_dependency,
    current_user=get_current_user_dependency,
):
    repo = NotificationPreferencesRepository(db)
    opt_outs = await repo.list_opt_outs(current_user.id)
    return _build_response(opt_outs)


@router.patch("", response_model=PreferencesResponse)
async def update_preferences(
    body: PreferencesUpdate,
    db=get_db_dependency,
    current_user=get_current_user_dependency,
):
    repo = NotificationPreferencesRepository(db)
    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(
            status_code=422, detail={"message": "At least one preference must be provided"}
        )
    for key_str, enabled in updates.items():
        try:
            key = NotificationKey(key_str)
        except ValueError as e:
            raise HTTPException(
                status_code=422, detail={"message": f"Unknown notification key: {key_str}"}
            ) from e
        await repo.set_enabled(current_user.id, key.value, enabled)

    opt_outs = await repo.list_opt_outs(current_user.id)
    return _build_response(opt_outs)
