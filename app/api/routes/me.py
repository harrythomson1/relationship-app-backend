from fastapi import APIRouter, Depends

from app.api.auth.utils import get_current_user
from app.api.schemas.user_schema import UserSchema

router = APIRouter(prefix="/users", tags=["users"])


get_current_user_dependency = Depends(get_current_user)


@router.get("/me", response_model=UserSchema)
async def get_me(current_user: UserSchema = get_current_user_dependency):
    return current_user
