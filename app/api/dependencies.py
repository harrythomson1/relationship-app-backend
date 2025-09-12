from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.core.database_connection import get_db
from app.api.repositories.relationship_repository import RelationshipRepository
from app.api.repositories.user_repository import UserRepository
from app.api.services.relationships_service import RelationshipsService
from app.api.services.users_service import UsersService

db_dependency = Depends(get_db)


async def get_user_repository(db: AsyncSession = db_dependency):
    return UserRepository(db)


async def get_relationship_repository(db: AsyncSession = db_dependency):
    return RelationshipRepository(db)


user_repository_dependency = Depends(get_user_repository)
relationship_repository_dependency = Depends(get_relationship_repository)


async def get_users_service(user_repostitory=user_repository_dependency):
    return UsersService(repository=user_repostitory)


async def get_relationships_service(
    db=db_dependency, relationship_repository=relationship_repository_dependency
):
    return RelationshipsService(relationship_repository, db)
