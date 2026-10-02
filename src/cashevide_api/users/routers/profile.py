from fastapi import APIRouter, Depends, Form

from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from cashevide_api.database import get_db
from cashevide_api.users.models import User, UserProfile, UserBusinessProfile
from cashevide_api.users.schemas import UserProfileOut, UserBusinessProfileOut
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


@router.patch("/profile/me", response_model=UserProfileOut)
async def update_user_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    full_name: str | None = Form(default=None, min_length=1),
    phone_number: str | None = Form(default=None),
    job_title: str | None = Form(default=None),
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

    if full_name is not None:
        user_profile.full_name = full_name
    if phone_number is not None:
        user_profile.phone_number = phone_number
    if job_title is not None:
        user_profile.job_title = job_title

    await db.commit()
    await db.refresh(user_profile)

    return user_profile


@router.get("/business-profile/me", response_model=UserBusinessProfileOut)
async def get_user_business_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserBusinessProfile:

    user_business_profile = await db.scalar(
        select(UserBusinessProfile).where(
            UserBusinessProfile.user_id == current_user.id
        )
    )

    if user_business_profile is None:
        user_business_profile = UserBusinessProfile(user_id=current_user.id)

        db.add(user_business_profile)
        await db.commit()
        await db.refresh(user_business_profile)

    return user_business_profile
