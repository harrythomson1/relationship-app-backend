from core.database_connection import get_db
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.repositories.user_repository import UserRepository


async def get_user_repository(db: AsyncSession = Depends(get_db)):
    return UserRepository(db)
