from datetime import UTC, datetime

from sqlalchemy import delete, select

from app.api.models import DeviceToken


class DeviceTokenRepository:
    def __init__(self, db):
        self.db = db

    async def upsert(self, user_id: int, token: str, platform: str | None) -> DeviceToken:
        existing = (
            await self.db.execute(select(DeviceToken).where(DeviceToken.token == token))
        ).scalar_one_or_none()
        if existing:
            existing.user_id = user_id
            existing.platform = platform
            existing.updated_at = datetime.now(UTC)
            await self.db.commit()
            await self.db.refresh(existing)
            return existing

        new_token = DeviceToken(user_id=user_id, token=token, platform=platform)
        self.db.add(new_token)
        await self.db.commit()
        await self.db.refresh(new_token)
        return new_token

    async def list_for_user(self, user_id: int) -> list[DeviceToken]:
        result = await self.db.execute(select(DeviceToken).where(DeviceToken.user_id == user_id))
        return list(result.scalars().all())

    async def delete_by_token(self, token: str) -> int:
        result = await self.db.execute(delete(DeviceToken).where(DeviceToken.token == token))
        await self.db.commit()
        return result.rowcount or 0

    async def delete_tokens(self, tokens: list[str]) -> int:
        if not tokens:
            return 0
        result = await self.db.execute(delete(DeviceToken).where(DeviceToken.token.in_(tokens)))
        await self.db.commit()
        return result.rowcount or 0
