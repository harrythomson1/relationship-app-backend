from fastapi import APIRouter, Depends

from app.api.auth.utils import get_current_user
from app.api.dependencies import get_users_service
from app.api.schemas.user_schema import UserSchema, UserUpdate
from app.api.services.users_service import UsersService

router = APIRouter(prefix="/users", tags=["users"])


get_current_user_dependency = Depends(get_current_user)
user_service_dependency = Depends(get_users_service)


@router.get("/me", response_model=UserSchema)
async def get_me(current_user: UserSchema = get_current_user_dependency):
    return current_user


@router.patch("/me", response_model=UserSchema)
async def update_user(
    update_data: UserUpdate,
    current_user=get_current_user_dependency,
    service: UsersService = user_service_dependency,
):
    user = await service.update(current_user.id, update_data)
    return user
