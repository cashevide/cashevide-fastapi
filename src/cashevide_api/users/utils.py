import logging
import random
import string
import re

from fastapi import Response

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pydantic_core import PydanticCustomError

from cashevide_api.config import settings
from cashevide_api.users.models import BlacklistedToken, UserProfile
from cashevide_api.security import decode_refresh_token

logger = logging.getLogger(__name__)


def check_username_characters(value: str) -> str:
    if not re.fullmatch(r"[\w.@+-]+", value):
        raise PydanticCustomError(
            "invalid_username",
            "Enter a valid username. This value may contain only letters, "
            "numbers, and @/./+/-/_ characters.",
        )
    return value


async def generate_unique_referral_code(db: AsyncSession) -> str:
    while True:
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

        existing = await db.scalar(
            select(UserProfile).where(UserProfile.referral_code == code)
        )

        if existing is None:
            return code


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=settings.jwt_access_token_expire_minutes * 60,
        httponly=True,
        secure=not settings.debug,
        samesite="lax",
        domain=settings.cookie_domain,
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=settings.jwt_refresh_token_expire_days * 24 * 60 * 60,
        httponly=True,
        secure=not settings.debug,
        samesite="lax",
        domain=settings.cookie_domain,
    )


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie("access_token", domain=settings.cookie_domain)
    response.delete_cookie("refresh_token", domain=settings.cookie_domain)


async def blacklist_refresh_token(db: AsyncSession, refresh_token: str | None) -> bool:
    if not refresh_token:
        return False

    try:
        _, jti = decode_refresh_token(refresh_token)
    except Exception as exc:
        logger.warning("Could not blacklist refresh token: %s", exc)
        return False

    already = await db.scalar(
        select(BlacklistedToken.id).where(BlacklistedToken.jti == jti).limit(1)
    )

    if already is None:
        db.add(BlacklistedToken(jti=jti))

    return True
