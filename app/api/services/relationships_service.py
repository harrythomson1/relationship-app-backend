from app.api.models import Relationship, RelationshipMember


class InvalidInviteUserError(Exception):
    pass


class RelationshipsService:
    def __init__(self, repository, db):
        self.repository = repository
        self.db = db

    async def add(self, current_user, relationship_info, user_service, relationship_invite_service):
        invite = await relationship_invite_service.get_by_token(relationship_info.invite_token)
        partner = await user_service.get_by_email(invite.inviter_email)
        if current_user.email != invite.invitee_email:
            raise InvalidInviteUserError("Current user does not match user from the invite")
        async with self.db.begin_nested():
            if current_user.id == partner.id:
                raise ValueError("A relationship must have two distinct users")
            rel = Relationship(type=relationship_info.type, status=relationship_info.status)
            rel = await self.repository.add_relationship(rel)
            rel_member_1 = RelationshipMember(
                relationship_id=rel.id, user_id=current_user.id, role=relationship_info.role
            )
            rel_member_2 = RelationshipMember(
                relationship_id=rel.id, user_id=partner.id, role=relationship_info.role
            )
            await self.repository.add_relationship_members(rel_member_1)
            await self.repository.add_relationship_members(rel_member_2)
            return rel

    async def get_by_id(self, id, current_user):
        rel = await self.repository.get_by_id(id, current_user)
        return rel

    async def update(self, id, update_data):
        return await self.repository.update(id, update_data)

    async def delete(self, user_id):
        return await self.repository.delete(user_id)
