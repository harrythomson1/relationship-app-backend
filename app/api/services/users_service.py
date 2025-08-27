from app.api.models import User


class UsersService:
    def __init__(self, repository):
        self.repository = repository

    async def add(self, user_info):
        user = User(name=user_info.name, email=user_info.email)
        return await self.repository.add(user)

    async def get_by_id(self, id):
        user = await self.repository.get_by_id(id)
        return user

    async def get_by_email(self, email):
        user = await self.repository.get_by_email(email)
        return user

    async def update(self, id, update_data):
        return await self.repository.update(id, update_data)

    async def delete(self, id):
        return await self.repository.delete(id)
