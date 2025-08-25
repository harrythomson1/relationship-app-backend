from sqlalchemy import select

from app.api.models import User


class DuplicateEmailError(Exception):
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
        return result.scalars().first()
