import logging

from cashevide_api.config import settings

logger = logging.getLogger(__name__)


async def send_otp_email(email: str, otp: str, purpose: str) -> None:
    if not settings.debug:
        raise RuntimeError("Email sending is not configured yet.")

    logger.warning("DEV ONLY - %s OTP for %s: %s", purpose, email, otp)
