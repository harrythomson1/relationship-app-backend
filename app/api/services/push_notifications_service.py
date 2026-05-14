from typing import Any

from app.api.utils import push_client


class PushNotificationsService:
    def __init__(self, repository, push_send=push_client.send_push):
        self.repository = repository
        self._push_send = push_send

    async def register(self, user_id: int, token: str, platform: str | None):
        return await self.repository.upsert(user_id=user_id, token=token, platform=platform)

    async def unregister(self, token: str) -> int:
        return await self.repository.delete_by_token(token)

    async def send_to_user(
        self,
        user_id: int,
        title: str,
        body: str,
        data: dict[str, Any] | None = None,
    ) -> push_client.PushSendResult:
        rows = await self.repository.list_for_user(user_id)
        tokens = [row.token for row in rows]
        result = await self._push_send(tokens=tokens, title=title, body=body, data=data)
        if result.dead_tokens:
            await self.repository.delete_tokens(result.dead_tokens)
        return result
