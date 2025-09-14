from app.api.models import Invite


class RelationshipInvitesService:
    def __init__(self, repository):
        self.repository = repository

    async def add(self, relationship_invite_info, user_id):
        invite = Invite(
            invitee_email=relationship_invite_info.invitee_email, inviter_user_id=user_id
        )
        return await self.repository.add(invite, user_id)
