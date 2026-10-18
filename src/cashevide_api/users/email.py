import asyncio
import logging
import smtplib
import ssl

from email.message import EmailMessage
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from cashevide_api.config import settings

logger = logging.getLogger(__name__)

templates = Environment(
    loader=FileSystemLoader(Path(__file__).parent / "templates"),
    autoescape=select_autoescape(["html"]),
)


def _build_message(email: str, otp: str, purpose: str) -> EmailMessage:
    if purpose == "password_reset":
        subject = "Your Cashevide Password Reset Code"
        text = (
            "Hello,"
            f"\n\nYour verification code for resetting your password is: {otp}"
            "\n\nThis code will expire in 5 minutes.\n\nThank you!"
        )

    else:
        subject = "Your Cashevide Verification Code"
        text = (
            "Welcome to Cashevide!"
            f"\n\nYour verification code for signup is: {otp}\n\n"
            "This code will expire in 5 minutes.\n\nThank you!"
        )

    html = templates.get_template("otp_email.html").render(otp=otp, purpose=purpose)

    msg = EmailMessage()
    msg["subject"] = subject
    msg["from"] = settings.default_from_email
    msg["to"] = email
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")

    return msg


def _send_sync(msg: EmailMessage) -> None:
    if not settings.smtp_username or not settings.smtp_password:
        raise RuntimeError("SMTP_USERNAME / SMTP_PASSWORD are not configured.")

    with smtplib.SMTP(settings.email_host, settings.email_port, timeout=15) as smtp:
        smtp.starttls(context=ssl.create_default_context())
        smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(msg)


async def send_otp_email(email: str, otp: str, purpose: str) -> None:
    if settings.debug:
        logger.warning("DEV ONLY - %s OTP for %s: %s", purpose, email, otp)
        return

    msg = _build_message(email, otp, purpose)
    await asyncio.to_thread(_send_sync, msg)
