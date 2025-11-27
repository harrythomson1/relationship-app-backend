import os
import ssl
from email.message import EmailMessage

import aiosmtplib
import certifi


async def send_email(sender, receiver, subject, content):
    message = EmailMessage()
    message["From"] = sender
    message["To"] = receiver
    message["Subject"] = subject
    message.set_content(content, subtype="html")

    try:
        tls_context = ssl.create_default_context(cafile=certifi.where())
        await aiosmtplib.send(
            message,
            hostname="smtp.gmail.com",
            port=587,
            start_tls=True,
            tls_context=tls_context,
            username=sender,
            password=os.environ.get("GMAIL_APP_PASSWORD"),
        )
    except Exception as e:
        raise RuntimeError(f"Failed to send email: {e}") from e
