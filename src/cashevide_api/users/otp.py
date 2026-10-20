import logging
import secrets

from redis.asyncio import Redis

from cashevide_api.users.email import send_otp_email

logger = logging.getLogger(__name__)

OTP_TTL = 300
COOLDOWN_TTL = 60
VERIFIED_TTL = 900
MAX_ATTEMPTS = 5


class OTPError(Exception):
    def __init__(self, content: dict[str, str | list[str]]) -> None:
        super().__init__(content)
        self.content = content


def generate_otp(length: int = 6) -> str:
    return f"{secrets.randbelow(10**length):0{length}d}"


def _key(purpose: str, kind: str, email: str) -> str:
    return f"{purpose}:{kind}:{email}"


async def request_otp(redis: Redis, email: str, purpose: str) -> None:
    cooldown_key = _key(purpose, "cooldown", email)
    otp_key = _key(purpose, "otp", email)
    attempts_key = _key(purpose, "attempts", email)

    if not await redis.set(cooldown_key, "1", nx=True, ex=COOLDOWN_TTL):
        raise OTPError(
            {"error": "Please wait 60 seconds before requesting another OTP."}
        )

    otp = generate_otp()
    await redis.set(otp_key, otp, ex=OTP_TTL)
    await redis.delete(attempts_key)

    try:
        await send_otp_email(email, otp, purpose)
    except Exception as exc:
        logger.exception("Failed to send %s OTP to %s", purpose, email)
        await redis.delete(cooldown_key, otp_key)
        raise OTPError(
            {"error": "Failed to send the OTP. Please try again later."}
        ) from exc


async def verify_otp(redis: Redis, email: str, otp: str, purpose: str) -> None:
    otp_key = _key(purpose, "otp", email)
    attempts_key = _key(purpose, "attempts", email)

    stored = await redis.get(otp_key)

    if stored is None:
        raise OTPError(
            {
                "otp": [
                    "The OTP has expired or does not exist. Please request a new one."
                ]
            }
        )

    if not secrets.compare_digest(stored.encode(), otp.encode()):  # type:ignore
        attempts = await redis.incr(attempts_key)
        await redis.expire(attempts_key, OTP_TTL)

        if attempts >= MAX_ATTEMPTS:
            await redis.delete(otp_key, attempts_key)
            raise OTPError(
                {"otp": ["Too many attempts. OTP blocked. Please request a new OTP."]}
            )

        remaining = MAX_ATTEMPTS - attempts
        word = "attempt" if remaining == 1 else "attempts"

        raise OTPError(
            {"otp": [f"The provided OTP is invalid. {remaining} {word} remaining."]}
        )

    await redis.set(_key(purpose, "verified", email), "1", ex=VERIFIED_TTL)
    await redis.delete(otp_key, attempts_key)


async def is_otp_verified(redis: Redis, email: str, purpose: str) -> bool:
    return bool(await redis.exists(_key(purpose, "verified", email)))


async def clear_otp_verified(redis: Redis, email: str, purpose: str) -> None:
    await redis.delete(_key(purpose, "verified", email))
