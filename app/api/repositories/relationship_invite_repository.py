from datetime import UTC, datetime

from sqlalchemy import func, select, update

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
                (Invite.inviter_user_id == user_id)
                & (Invite.invitee_email == invite.invitee_email)
                & (Invite.status == InviteStatus.pending)
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

    async def mark_accepted(self, invite, relationship_id):
        invite.status = InviteStatus.accepted
        invite.accepted_at = datetime.now(UTC)
        invite.relationship_id = relationship_id
        await self.db.flush()

    async def mark_relationship_ended(self, relationship_id):
        await self.db.execute(
            update(Invite)
            .where(
                (Invite.relationship_id == relationship_id)
                & (Invite.status == InviteStatus.accepted)
            )
            .values(status=InviteStatus.ended)
        )
        await self.db.flush()

    async def mark_declined(self, invite):
        invite.status = InviteStatus.declined
        await self.db.commit()

    async def mark_expired(self, invite):
        invite.status = InviteStatus.expired
        await self.db.commit()

    async def get_pending_for_email(self, email, user_id):
        query = select(Invite).where(
            (Invite.invitee_email == email)
            & (Invite.status == InviteStatus.pending)
            & (Invite.inviter_user_id != user_id)
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def count_recent_for_inviter(self, inviter_user_id, since):
        query = select(func.count(Invite.id)).where(
            (Invite.inviter_user_id == inviter_user_id)
            & (Invite.created_at >= since)
            & (Invite.status == InviteStatus.pending)
        )
        result = await self.db.execute(query)
        return result.scalar_one()
