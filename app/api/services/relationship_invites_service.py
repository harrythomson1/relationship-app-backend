from datetime import UTC, datetime, timedelta

from app.api.models import Invite, InviteStatus

INVITE_TTL = timedelta(days=7)
INVITE_RATE_LIMIT_WINDOW = timedelta(hours=1)
INVITE_RATE_LIMIT_MAX = 10


class InviteExpiredError(Exception):
    pass


class InviteRecipientMismatchError(Exception):
    pass


class InviteRateLimitedError(Exception):
    pass


def _is_expired(invite):
    return invite.expires_at is not None and invite.expires_at <= datetime.now(UTC)


class RelationshipInvitesService:
    def __init__(self, repository):
        self.repository = repository

    async def add(self, relationship_invite_info, user):
        window_start = datetime.now(UTC) - INVITE_RATE_LIMIT_WINDOW
        recent_count = await self.repository.count_recent_for_inviter(user.id, window_start)
        if recent_count >= INVITE_RATE_LIMIT_MAX:
            raise InviteRateLimitedError(
                f"Invite rate limit reached ({INVITE_RATE_LIMIT_MAX} per hour)"
            )
        invite = Invite(
            invitee_email=relationship_invite_info.invitee_email,
            inviter_user_id=user.id,
            inviter_email=user.email,
            expires_at=datetime.now(UTC) + INVITE_TTL,
        )
        return await self.repository.add(invite, user.id)

    async def get_by_token(self, token):
        invite = await self.repository.get_by_token(token)
        if _is_expired(invite):
            if invite.status == InviteStatus.pending:
                await self.repository.mark_expired(invite)
            raise InviteExpiredError("Invite has expired")
        return invite

    async def get_pending_for_user(self, user):
        invite = await self.repository.get_pending_for_email(user.email, user.id)
        if invite is not None and _is_expired(invite):
            await self.repository.mark_expired(invite)
            return None
        return invite

    async def mark_accepted(self, invite):
        await self.repository.mark_accepted(invite)

    async def mark_declined(self, token, user):
        invite = await self.repository.get_by_token(token)
        if invite.invitee_email != user.email:
            raise InviteRecipientMismatchError("Invite is not addressed to this user")
        if _is_expired(invite):
            if invite.status == InviteStatus.pending:
                await self.repository.mark_expired(invite)
            raise InviteExpiredError("Invite has expired")
        await self.repository.mark_declined(invite)
