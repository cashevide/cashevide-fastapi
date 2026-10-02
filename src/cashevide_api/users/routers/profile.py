from typing import Annotated
from fastapi import APIRouter, Depends, Form

from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from cashevide_api.database import get_db
from cashevide_api.users.models import User, UserProfile, UserBusinessProfile
from cashevide_api.users.schemas import (
    UserProfileOut,
    UserProfileUpdate,
    UserBusinessProfileOut,
    UserBusinessProfileUpdate,
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


@router.patch("/profile/me", response_model=UserProfileOut)
async def update_user_profile(
    payload: Annotated[UserProfileUpdate, Form()],
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

    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(user_profile, field, value)

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


@router.patch("/business-profile/me", response_model=UserBusinessProfileOut)
async def update_user_business_profile(
    payload: Annotated[UserBusinessProfileUpdate, Form()],
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

    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(user_business_profile, field, value)

    await db.commit()
    await db.refresh(user_business_profile)

    return user_business_profile
