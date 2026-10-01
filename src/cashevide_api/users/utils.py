import random
import string

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cashevide_api.users.models import UserProfile


async def generate_unique_referral_code(db: AsyncSession) -> str:
    while True:
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

        existing = await db.scalar(
            select(UserProfile).where(UserProfile.referral_code == code)
        )

        if existing is None:
            return code
