from sqlalchemy import select

from app.api.models import Relationship, RelationshipMember


class DuplicateEntryError(Exception):
    pass


class RelationshipNotFoundError(Exception):
    pass


class RelationshipRepository:
    def __init__(self, db):
        self.db = db

    async def add_relationship(self, relationship):
        self.db.add(relationship)
        await self.db.flush()
        return relationship

    async def add_relationship_members(self, relationship_member):
        result = await self.db.execute(
            select(RelationshipMember).where(
                (RelationshipMember.relationship_id == relationship_member.relationship_id)
                & (RelationshipMember.user_id == relationship_member.user_id)
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise DuplicateEntryError("User is already a part of this relationship")
        self.db.add(relationship_member)
        await self.db.flush()
        return relationship_member

    async def get_by_id(self, id):
        query = select(Relationship).where(Relationship.id == id)
        result = await self.db.execute(query)
        rel = result.scalars().first()
        if not rel:
            raise RelationshipNotFoundError("Relationship not found")
        return rel
