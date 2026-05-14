from contextlib import suppress

from app.api.auth.supabase_admin import delete_auth_user
from app.api.models import User
from app.api.repositories.relationship_repository import (
    RelationshipMemberNotFoundError,
    RelationshipNotFoundError,
)


class InvalidEmailError(Exception):
    pass


class UsersService:
    def __init__(self, repository, relationship_repository=None):
        self.repository = repository
        self.relationship_repository = relationship_repository

    async def add(self, user_info, claims):
        email = claims.get("email", "").lower().strip()
        user = User(
            name=user_info.name,
            email=email,
            supabase_user_id=claims["sub"],
            time_zone=user_info.time_zone,
        )
        return await self.repository.add(user)

    async def get_by_id(self, id):
        user = await self.repository.get_by_id(id)
        return user

    async def get_by_email(self, email):
        user = await self.repository.get_by_email(email)
        return user

    async def update(self, id, update_data):
        return await self.repository.update(id, update_data)

    async def delete(self, id):
        user = await self.repository.get_by_id(id)

        # Delete from Supabase auth FIRST. If this fails, our DB stays intact
        # so the user can retry. If it succeeds and our DB delete later fails,
        # the user can no longer authenticate, leaving only an orphaned row.
        await delete_auth_user(user.supabase_user_id)

        # End the user's relationship if one exists (also frees the partner).
        # CASCADE on relationship_members would clean up membership anyway,
        # but we explicitly delete the whole relationship to match the
        # behaviour of the manual "remove partner" flow.
        if self.relationship_repository is not None:
            with suppress(RelationshipMemberNotFoundError, RelationshipNotFoundError):
                await self.relationship_repository.delete(id)

        await self.repository.delete(id)
