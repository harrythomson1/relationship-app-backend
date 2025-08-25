from app.api.models import User


class UsersService:
    def __init__(self, repository):
        self.repository = repository

    async def add(self, user_info):
        user = User(name=user_info.name, email=user_info.email)
        return await self.repository.add(user)
