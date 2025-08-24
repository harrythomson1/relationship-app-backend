import logging

from fastapi import APIRouter, Depends, status

from app.api.schemas.user_schema import UserCreate, UserSchema

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/users")
def test_route():
    return {"Are users working?": "Yes"}


@router.post("/users", status_code=status.HTTP_201_CREATED, response_model=UserSchema)
async def add_user(user_info: UserCreate, service: UsersService = Depends(get_users_service)):
    try:
        user = await service.add_user(user_info)
        return user
    except Exception:
        logger.exception("Unexpected error with adding a user")
