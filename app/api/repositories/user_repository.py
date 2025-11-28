from uuid import UUID

from sqlalchemy import select

from app.api.models import User


class DuplicateEmailError(Exception):
    pass


class UserNotFoundError(Exception):
    pass


class UserRepository:
    def __init__(self, db):
        self.db = db

    async def add(self, user: User):
        result = await self.db.execute(select(User).where(User.email == user.email))
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise DuplicateEmailError("Email already exists")
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_by_id(self, id: int):
        query = select(User).where(User.id == id)
        result = await self.db.execute(query)
        user = result.scalars().first()
        if not user:
            raise UserNotFoundError("User not found")
        return user

    async def get_by_supabase_user_id(self, supabase_user_id: UUID):
        query = select(User).where(User.supabase_user_id == supabase_user_id)
        result = await self.db.execute(query)
        user = result.scalars().first()
        if not user:
            raise UserNotFoundError("User not found")
        return user

    async def get_by_email(self, email: str):
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        user = result.scalars().first()
        if not user:
            raise UserNotFoundError("User not found")
        return user

    async def update(self, id, update_data):
        result = await self.db.execute(select(User).where(User.id == id))
        user = result.scalar_one_or_none()
        data = update_data.model_dump(exclude_unset=True)

        if not user:
            raise UserNotFoundError("User not found")

        for key, value in data.items():
            setattr(user, key, value)

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete(self, id):
        query = select(User).where(User.id == id)
        result = await self.db.execute(query)
        user_to_delete = result.scalars().first()
        if not user_to_delete:
            raise UserNotFoundError("User not found")

        await self.db.delete(user_to_delete)
        await self.db.commit()
        return True
