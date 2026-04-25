import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.auth.utils import get_current_claims
from app.api.dependencies import get_users_service
from app.api.repositories.user_repository import DuplicateEmailError
from app.api.schemas.user_schema import UserCreate, UserSchema
from app.api.services.users_service import InvalidEmailError, UsersService

router = APIRouter()
logger = logging.getLogger(__name__)

user_service_dependency = Depends(get_users_service)
get_claims = Depends(get_current_claims)


@router.post("/users", status_code=status.HTTP_201_CREATED, response_model=UserSchema)
async def add_user(
    user_info: UserCreate, claims=get_claims, service: UsersService = user_service_dependency
):
    try:
        user = await service.add(user_info, claims)
        return user
    except DuplicateEmailError as e:
        raise HTTPException(status_code=409, detail={"message": str(e)}) from e
    except InvalidEmailError as e:
        raise HTTPException(status_code=422, detail={"message": str(e)}) from e
    except Exception as e:
        logger.exception("Unexpected error with adding a user")
        raise HTTPException(status_code=500, detail={"message": "Internal server error"}) from e
