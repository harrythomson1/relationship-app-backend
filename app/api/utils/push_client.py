import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"

# Receipt error codes Expo returns for tokens that are no longer valid. When
# we see these we should drop the token from our DB so we stop trying to use it.
DEAD_TOKEN_ERRORS = {"DeviceNotRegistered", "InvalidCredentials"}


class PushSendResult:
    """Outcome of a fan-out send.

    `dead_tokens` are Expo tokens the caller should remove from the DB.
    """

    def __init__(self, sent: int, dead_tokens: list[str]):
        self.sent = sent
        self.dead_tokens = dead_tokens


async def send_push(
    tokens: list[str],
    title: str,
    body: str,
    data: dict[str, Any] | None = None,
) -> PushSendResult:
    if not tokens:
        return PushSendResult(sent=0, dead_tokens=[])

    messages = [
        {
            "to": token,
            "title": title,
            "body": body,
            "sound": "default",
            **({"data": data} if data else {}),
        }
        for token in tokens
    ]

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(EXPO_PUSH_URL, json=messages)
    except httpx.HTTPError as e:
        logger.exception("Expo push request failed")
        raise PushDeliveryError(f"Expo push request failed: {e}") from e

    if response.status_code >= 500:
        raise PushDeliveryError(f"Expo push server error {response.status_code}: {response.text}")

    payload = response.json()
    tickets = payload.get("data", []) if isinstance(payload, dict) else []

    dead: list[str] = []
    sent = 0
    for token, ticket in zip(tokens, tickets, strict=False):
        if not isinstance(ticket, dict):
            continue
        if ticket.get("status") == "ok":
            sent += 1
            continue
        details = ticket.get("details") or {}
        if details.get("error") in DEAD_TOKEN_ERRORS:
            dead.append(token)

    return PushSendResult(sent=sent, dead_tokens=dead)


class PushDeliveryError(Exception):
    pass
