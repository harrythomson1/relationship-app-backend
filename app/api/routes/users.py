import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_users_service
from app.api.repositories.user_repository import DuplicateEmailError, UserNotFoundError
from app.api.schemas.user_schema import UserCreate, UserSchema, UserUpdate
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
    except DuplicateEmailError as e:
        raise HTTPException(status_code=409, detail={"message": str(e)}) from e
    except Exception:
        logger.exception("Unexpected error with adding a user")


@router.get("/users/{id}")
async def get_user(id: int, service: UsersService = user_service_dependency):
    try:
        user = await service.get(id)
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
