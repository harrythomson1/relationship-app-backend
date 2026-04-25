import resend

from app.api.core.config import RESEND_API_KEY


async def send_email(sender, receiver, subject, content):
    resend.api_key = RESEND_API_KEY
    try:
        resend.Emails.send(
            {
                "from": sender,
                "to": receiver,
                "subject": subject,
                "html": content,
            }
        )
    except Exception as e:
        raise RuntimeError(f"Failed to send email: {e}") from e
