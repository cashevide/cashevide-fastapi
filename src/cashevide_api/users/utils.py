import random
import string

from fastapi import Response

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cashevide_api.config import settings
from cashevide_api.users.models import UserProfile


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
