from app.api.models import User


class UserRepository:
    def __init__(self, db):
        self.db = db

    async def add(self, user: User):
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
