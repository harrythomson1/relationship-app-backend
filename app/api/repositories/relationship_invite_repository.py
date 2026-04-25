from datetime import UTC, datetime

from sqlalchemy import select

from app.api.models import Invite, InviteStatus


class DuplicateInviteError(Exception):
    pass


class RelationshipInviteNotFoundError(Exception):
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

    async def get_by_token(self, token):
        query = select(Invite).where(Invite.token == token)
        result = await self.db.execute(query)
        invite = result.scalars().first()
        if not invite:
            raise RelationshipInviteNotFoundError("Relationship invite not found")
        return invite

    async def mark_accepted(self, invite):
        invite.status = InviteStatus.accepted
        invite.accepted_at = datetime.now(UTC)
        await self.db.flush()

    async def get_pending_for_email(self, email, user_id):
        query = select(Invite).where(
            (Invite.invitee_email == email)
            & (Invite.status == InviteStatus.pending)
            & (Invite.inviter_user_id != user_id)
        )
        result = await self.db.execute(query)
        return result.scalars().first()
