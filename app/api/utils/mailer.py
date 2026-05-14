import asyncio

import resend

from app.api.core.config import RESEND_API_KEY


def _send_sync(sender, receiver, subject, content):
    resend.api_key = RESEND_API_KEY
    resend.Emails.send(
        {
            "from": sender,
            "to": receiver,
            "subject": subject,
            "html": content,
        }
    )


async def send_email(sender, receiver, subject, content):
    try:
        await asyncio.to_thread(_send_sync, sender, receiver, subject, content)
    except Exception as e:
        raise RuntimeError(f"Failed to send email: {e}") from e
