import logging

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_users_service
from app.api.schemas.user_schema import UserCreate, UserSchema
from app.api.services.UsersService import UsersService

router = APIRouter()
logger = logging.getLogger(__name__)

user_service_dependency = Depends(get_users_service)


@router.get("/users")
def test_route():
    return {"Are users working?": "Yes"}


@router.post("/users", status_code=status.HTTP_201_CREATED, response_model=UserSchema)
async def add_user(user_info: UserCreate, service: UsersService = user_service_dependency):
    try:
        user = await service.add(user_info)
        return user
    except Exception:
        logger.exception("Unexpected error with adding a user")
