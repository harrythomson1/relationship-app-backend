from sqlalchemy import select

from app.api.models import Relationship, RelationshipMember
from app.api.repositories.user_repository import UserRepository


class DuplicateEntryError(Exception):
    pass


class RelationshipNotFoundError(Exception):
    pass


class RelationshipMemberNotFoundError(Exception):
    pass


class UserNotAMemberOfRelationshipError(Exception):
    pass


ALLOWED_FIELDS = {"status", "type", "next_meet_at"}


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

    async def get_partner(self, current_user):
        result = await self.db.execute(
            select(RelationshipMember).where(RelationshipMember.user_id == current_user.id)
        )
        existing = result.scalar_one_or_none()
        if not existing:
            raise RelationshipMemberNotFoundError("Relationship member not found")
        result = await self.db.execute(
            select(RelationshipMember).where(
                RelationshipMember.relationship_id == existing.relationship_id
            )
        )
        rows = result.scalars().all()
        if not rows:
            raise RelationshipMemberNotFoundError("Relationship member not found")
        partner = next(
            (rel_member for rel_member in rows if rel_member.user_id != current_user.id), None
        )
        return partner

    async def get_by_id(self, relationship_id, user_id):
        query = select(Relationship).where(Relationship.id == relationship_id)
        result = await self.db.execute(query)
        rel = result.scalars().first()
        if not rel:
            raise RelationshipNotFoundError("Relationship not found")
        query = select(RelationshipMember).where(
            (RelationshipMember.relationship_id == relationship_id)
            & (RelationshipMember.user_id == user_id)
        )
        result = await self.db.execute(query)
        rel_mem = result.scalars().first()
        if not rel_mem:
            raise UserNotAMemberOfRelationshipError("User is not a member of relationship")
        return rel

    async def get_by_user_id(self, user_id):
        return await self._get_by_user_id(user_id)

    async def update(self, user_id, update_data):
        relationship = await self._get_by_user_id(user_id)

        updates = update_data.model_dump(exclude_none=True)

        updates = {k: v for k, v in updates.items() if k in ALLOWED_FIELDS}

        for field, value in updates.items():
            if getattr(relationship, field) != value:
                setattr(relationship, field, value)

        await self.db.commit()
        await self.db.refresh(relationship)
        return relationship

    async def delete(self, user_id):
        relationship = await self._get_by_user_id(user_id)
        await self.db.delete(relationship)
        await self.db.commit()
        return True

    async def get_existing_relationship_between_users(self, current_user_id, partner_id):
        user_member = await self._get_relationship_member_by_id(current_user_id)
        partner_member = await self._get_relationship_member_by_id(partner_id)
        if partner_member.relationship_id != user_member.relationship_id:
            raise RelationshipNotFoundError("Relationship between these users does not exist")
        relationship = await self.get_by_id(user_member.relationship_id, current_user_id)
        return relationship

    async def _get_by_user_id(self, user_id):
        relationship_member = await self._get_relationship_member_by_id(user_id)

        result = await self.db.execute(
            select(Relationship).where(Relationship.id == relationship_member.relationship_id)
        )
        relationship = result.scalar_one_or_none()
        if not relationship:
            raise RelationshipNotFoundError("Relationship not found")
        return relationship

    async def _get_relationship_member_by_id(self, id):
        query = select(RelationshipMember).where(RelationshipMember.user_id == id)
        result = await self.db.execute(query)
        relationship_member = result.scalar_one_or_none()
        if not relationship_member:
            raise RelationshipMemberNotFoundError("Relationship member not found")
        return relationship_member
