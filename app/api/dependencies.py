from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.core.database_connection import get_db
from app.api.repositories.user_repository import UserRepository
from app.api.services.UsersService import UsersService

db_dependency = Depends(get_db)


async def get_user_repository(db: AsyncSession = db_dependency):
    return UserRepository(db)


user_repository_dependency = Depends(get_user_repository)


async def get_users_service(user_repostitory=user_repository_dependency):
    return UsersService(repository=user_repostitory)
