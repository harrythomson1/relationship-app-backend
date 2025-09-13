from app.api.models import Relationship, RelationshipMember


class RelationshipsService:
    def __init__(self, repository, db):
        self.repository = repository
        self.db = db

    async def add(self, relationship_info):
        async with self.db.begin_nested():
            u1, u2 = relationship_info.user_ids
            if u1 == u2:
                raise ValueError("A relationship must have two distinct users")
            rel = Relationship(type=relationship_info.type, status=relationship_info.status)
            rel = await self.repository.add_relationship(rel)
            rel_member_1 = RelationshipMember(
                relationship_id=rel.id, user_id=u1, role=relationship_info.role
            )
            rel_member_2 = RelationshipMember(
                relationship_id=rel.id, user_id=u2, role=relationship_info.role
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
