from fastapi import APIRouter, Depends, HTTPException, status

from app.api.auth.supabase_admin import SupabaseAdminError
from app.api.auth.utils import get_current_claims, get_current_user
from app.api.core.database_connection import get_db
from app.api.dependencies import get_users_service
from app.api.repositories.user_repository import (
    DuplicateEmailError,
    UserNotFoundError,
)
from app.api.schemas.user_schema import UserSchema, UserUpdate
from app.api.services.users_service import InvalidEmailError, UsersService

router = APIRouter(prefix="/users", tags=["users"])


get_current_claims_dependency = Depends(get_current_claims)
get_db_dependency = Depends(get_db)
get_current_user_dependency = Depends(get_current_user)
user_service_dependency = Depends(get_users_service)


@router.get("/me", response_model=UserSchema)
async def get_me(
    current_claims=get_current_claims_dependency,
    db=get_db_dependency,
):
    try:
        return await get_current_user(current_claims, db)
    except UserNotFoundError as e:
        raise HTTPException(status_code=404, detail={"message": str(e)}) from e
    except DuplicateEmailError as e:
        raise HTTPException(status_code=409, detail={"message": str(e)}) from e
    except InvalidEmailError as e:
        raise HTTPException(status_code=422, detail={"message": str(e)}) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Internal server error"}) from e


@router.patch("/me", response_model=UserSchema)
async def update_user(
    update_data: UserUpdate,
    current_user=get_current_user_dependency,
    service: UsersService = user_service_dependency,
):
    user = await service.update(current_user.id, update_data)
    return user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    current_user=get_current_user_dependency, service: UsersService = user_service_dependency
):
    try:
        await service.delete(current_user.id)
    except UserNotFoundError as e:
        raise HTTPException(status_code=404, detail={"message": str(e)}) from e
    except SupabaseAdminError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"message": f"Failed to delete authentication account: {e}"},
        ) from e
