from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.core.database_connection import get_db
from app.api.repositories.device_token_repository import DeviceTokenRepository
from app.api.repositories.notification_preferences_repository import (
    NotificationPreferencesRepository,
)
from app.api.repositories.relationship_invite_repository import RelationshipInviteRepository
from app.api.repositories.relationship_repository import RelationshipRepository
from app.api.repositories.user_repository import UserRepository
from app.api.services.push_notifications_service import PushNotificationsService
from app.api.services.relationship_invites_service import RelationshipInvitesService
from app.api.services.relationships_service import RelationshipsService
from app.api.services.users_service import UsersService

db_dependency = Depends(get_db)


async def get_user_repository(db: AsyncSession = db_dependency):
    return UserRepository(db)


async def get_relationship_repository(db: AsyncSession = db_dependency):
    return RelationshipRepository(db)


async def get_relationship_invites_repository(db: AsyncSession = db_dependency):
    return RelationshipInviteRepository(db)


user_repository_dependency = Depends(get_user_repository)
relationship_repository_dependency = Depends(get_relationship_repository)
relationship_invite_repository_dependency = Depends(get_relationship_invites_repository)


async def get_users_service(
    user_repository=user_repository_dependency,
    relationship_repository=relationship_repository_dependency,
):
    return UsersService(
        repository=user_repository,
        relationship_repository=relationship_repository,
    )


async def get_relationships_service(
    db=db_dependency,
    relationship_repository=relationship_repository_dependency,
    user_repository=user_repository_dependency,
):
    return RelationshipsService(
        relationship_repository=relationship_repository, db=db, user_repository=user_repository
    )


async def get_relationship_invites_service(
    relationship_invite_repository=relationship_invite_repository_dependency,
):
    return RelationshipInvitesService(relationship_invite_repository)


async def get_device_token_repository(db: AsyncSession = db_dependency):
    return DeviceTokenRepository(db)


device_token_repository_dependency = Depends(get_device_token_repository)


async def get_push_notifications_service(
    device_token_repository=device_token_repository_dependency,
):
    return PushNotificationsService(device_token_repository)


async def get_notification_preferences_repository(db: AsyncSession = db_dependency):
    return NotificationPreferencesRepository(db)


notification_preferences_repository_dependency = Depends(get_notification_preferences_repository)
