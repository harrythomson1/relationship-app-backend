from app.api.models import Relationship, RelationshipMember


class RelationshipsService:
    def __init__(self, repository):
        self.repository = repository

    async def add(self, relationship_info):
        async with self.repository.db.begin():
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
