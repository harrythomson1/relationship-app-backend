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

    async def get(self, id: int):
        query = select(User).where(User.id == id)
        result = await self.db.execute(query)
        user = result.scalars().first()
        if not user:
            raise UserNotFoundError("User not found")
        return user

    async def update(self, id, update_data):
        result = await self.db.execute(select(User).where(User.id == id))
        user = result.scalar_one_or_none()

        if not user:
            raise UserNotFoundError("User not found")

        if update_data.name is not None:
            user.name = update_data.name

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete(self, id):
        query = select(User).where(User.id == id)
        result = await self.db.execute(query)
        user_to_delete = result.scalars().first()
        if not user_to_delete:
            return None

        await self.db.delete(user_to_delete)
        await self.db.commit()
        return True
