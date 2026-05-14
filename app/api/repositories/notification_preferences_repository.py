from sqlalchemy import delete, select

from app.api.models import NotificationOptOut


class NotificationPreferencesRepository:
    def __init__(self, db):
        self.db = db

    async def list_opt_outs(self, user_id: int) -> set[str]:
        result = await self.db.execute(
            select(NotificationOptOut.key).where(NotificationOptOut.user_id == user_id)
        )
        return set(result.scalars().all())

    async def list_opt_outs_for_users(self, user_ids: list[int]) -> dict[int, set[str]]:
        if not user_ids:
            return {}
        result = await self.db.execute(
            select(NotificationOptOut.user_id, NotificationOptOut.key).where(
                NotificationOptOut.user_id.in_(user_ids)
            )
        )
        out: dict[int, set[str]] = {uid: set() for uid in user_ids}
        for user_id, key in result.all():
            out[user_id].add(key)
        return out

    async def set_enabled(self, user_id: int, key: str, enabled: bool) -> None:
        if enabled:
            await self.db.execute(
                delete(NotificationOptOut).where(
                    (NotificationOptOut.user_id == user_id) & (NotificationOptOut.key == key)
                )
            )
        else:
            existing = (
                await self.db.execute(
                    select(NotificationOptOut).where(
                        (NotificationOptOut.user_id == user_id) & (NotificationOptOut.key == key)
                    )
                )
            ).scalar_one_or_none()
            if existing is None:
                self.db.add(NotificationOptOut(user_id=user_id, key=key))
        await self.db.commit()
