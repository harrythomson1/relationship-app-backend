from sqlalchemy import select

from app.api.models import Invite


class DuplicateInviteError(Exception):
    pass


class RelationshipInviteRepository:
    def __init__(self, db):
        self.db = db

    async def add(self, invite, user_id):
        result = await self.db.execute(
            select(Invite).where(
                (Invite.inviter_user_id == user_id) & (Invite.invitee_email == invite.invitee_email)
            )
        )
        existing_invite = result.scalar_one_or_none()
        if existing_invite:
            raise DuplicateInviteError("Invite already exists")
        self.db.add(invite)
        await self.db.commit()
        await self.db.refresh(invite)
        return invite
