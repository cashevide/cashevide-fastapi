from fastapi import APIRouter, Depends

from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from cashevide_api.database import get_db
from cashevide_api.users.models import User, UserProfile
from cashevide_api.users.schemas import (
    UserProfileOut,
)
from cashevide_api.dependencies import get_current_user
from cashevide_api.users.utils import generate_unique_referral_code

router = APIRouter(tags=["profile"])


@router.get(
    "/profile/me",
    response_model=UserProfileOut,
)
async def get_user_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserProfile:

    user_profile = await db.scalar(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )

    if user_profile is None:
        user_profile = UserProfile(
            user_id=current_user.id,
            referral_code=await generate_unique_referral_code(db),
        )

        db.add(user_profile)
        await db.commit()
        await db.refresh(user_profile)

    return user_profile
