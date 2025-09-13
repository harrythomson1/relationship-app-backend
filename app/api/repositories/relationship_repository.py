from sqlalchemy import select

from app.api.models import Relationship, RelationshipMember
from app.api.repositories.user_repository import UserRepository


class DuplicateEntryError(Exception):
    pass


class RelationshipNotFoundError(Exception):
    pass


class RelationshipMemberNotFoundError(Exception):
    pass


ALLOWED_FIELDS = {"status", "type"}


class RelationshipRepository:
    def __init__(self, db):
        self.db = db
        self.user_repo = UserRepository(db)

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

    async def update(self, user_id, update_data):
        relationship = await self._get_by_user_id(user_id)

        updates = update_data.model_dump(exclude_unset=True, exclude_none=True)

        updates = {k: v for k, v in updates.items() if k in ALLOWED_FIELDS}

        for field, value in updates.items():
            if getattr(relationship, field) != value:
                setattr(relationship, field, value)

        await self.db.commit()
        await self.db.refresh(relationship)
        return relationship

    async def _get_by_user_id(self, user_id):
        result = await self.db.execute(
            select(RelationshipMember).where(RelationshipMember.user_id == user_id)
        )
        relationship_member = result.scalar_one_or_none()

        if not relationship_member:
            raise RelationshipMemberNotFoundError("Relationship member not found")

        result = await self.db.execute(
            select(Relationship).where(Relationship.id == relationship_member.relationship_id)
        )
        relationship = result.scalar_one_or_none()
        if not relationship:
            raise RelationshipNotFoundError("Relationship not found")
        return relationship
