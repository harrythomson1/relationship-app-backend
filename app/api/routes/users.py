import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.auth.utils import get_current_user
from app.api.dependencies import get_users_service
from app.api.repositories.user_repository import DuplicateEmailError, UserNotFoundError
from app.api.schemas.user_schema import UserCreate, UserSchema, UserUpdate
from app.api.services.users_service import UsersService

router = APIRouter()
logger = logging.getLogger(__name__)

user_service_dependency = Depends(get_users_service)
get_current_user_dependency = Depends(get_current_user)


@router.get("/users/me", response_model=UserSchema)
async def get_me(current_user: UserSchema = get_current_user_dependency):
    return current_user


@router.post("/users", status_code=status.HTTP_201_CREATED, response_model=UserSchema)
async def add_user(user_info: UserCreate, service: UsersService = user_service_dependency):
    try:
        user = await service.add(user_info)
        return user
    except DuplicateEmailError as e:
        raise HTTPException(status_code=409, detail={"message": str(e)}) from e
    except Exception as e:
        logger.exception("Unexpected error with adding a user")
        raise HTTPException(status_code=500, detail={"message": "Internal server error"}) from e


@router.get("/users/{id}", response_model=UserSchema)
async def get_user(id: int, service: UsersService = user_service_dependency):
    try:
        user = await service.get_by_id(id)
    except UserNotFoundError as e:
        raise HTTPException(status_code=404, detail={"message": str(e)}) from e
    return user


@router.patch("/users/{id}", response_model=UserSchema)
async def update_username(
    id: int, update_data: UserUpdate, service: UsersService = user_service_dependency
):
    try:
        user = await service.update(id, update_data)
    except UserNotFoundError as e:
        raise HTTPException(status_code=404, detail={"message": str(e)}) from e
    return user


@router.delete("/users/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(id: int, service: UsersService = user_service_dependency):
    try:
        await service.delete(id)
    except UserNotFoundError as e:
        raise HTTPException(status_code=404, detail={"message": str(e)}) from e
