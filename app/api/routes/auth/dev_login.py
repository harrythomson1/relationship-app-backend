from fastapi import APIRouter, Depends

from app.api.core.security import create_access_token
from app.api.dependencies import get_users_service
from app.api.repositories.user_repository import DuplicateEmailError
from app.api.schemas.auth_schema import AuthResponse, DevLoginRequest
from app.api.services.users_service import UsersService

router = APIRouter()

user_service_dependency = Depends(get_users_service)


@router.post("/auth/dev_login", response_model=AuthResponse)
async def login_or_create(
    login_request: DevLoginRequest, service: UsersService = user_service_dependency
):
    try:
        user = await service.add(login_request)
    except DuplicateEmailError:
        user = await service.get_by_email(login_request.email)

    token = create_access_token({"sub": user.id})
    return {"user": user, "token": token}
