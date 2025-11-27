from app.api.models import Invite


class RelationshipInvitesService:
    def __init__(self, repository):
        self.repository = repository

    async def add(self, relationship_invite_info, user):
        invite = Invite(
            invitee_email=relationship_invite_info.invitee_email,
            inviter_user_id=user.id,
            inviter_email=user.email,
        )
        return await self.repository.add(invite, user.id)

    async def get_by_token(self, token):
        return await self.repository.get_by_token(token)
