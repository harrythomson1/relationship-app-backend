from email.message import EmailMessage

import aiosmtplib


async def send_email(sender, receiver, subject, content):
    message = EmailMessage()
    message["From"] = sender
    message["To"] = receiver
    message["Subject"] = subject
    message.set_content(content)

    try:
        await aiosmtplib.send(message, hostname="127.0.0.1", port=25)
    except Exception as e:
        raise RuntimeError(f"Failed to send email: {e}") from e
