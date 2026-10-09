from typing import Annotated

from fastapi import APIRouter, Depends, Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cashevide_api.database import get_db
from cashevide_api.dependencies import get_current_user
from cashevide_api.storage import media_url
from cashevide_api.users.models import User, UserBusinessProfile, UserProfile
from cashevide_api.users.schemas import (
    UserBusinessProfileOut,
    UserBusinessProfileUpdate,
    UserProfileOut,
    UserProfileUpdate,
)
from cashevide_api.users.utils import generate_unique_referral_code

router = APIRouter(tags=["profile"])


def build_profile_out(profile: UserProfile, user: User) -> UserProfileOut:
    return UserProfileOut(
        user_id=profile.user_id,
        email=user.email,
        username=user.username,
        full_name=profile.full_name,
        profile_picture=media_url(profile.profile_picture),
        phone_number=profile.phone_number,
        job_title=profile.job_title,
        referral_code=profile.referral_code,
        referred_by=profile.referred_by_id,
        credit_points=profile.credit_points,
    )


def build_business_profile_out(
    profile: UserBusinessProfile,
) -> UserBusinessProfileOut:
    return UserBusinessProfileOut(
        user_id=profile.user_id,
        business_name=profile.business_name,
        logo=media_url(profile.logo),
        gst_number=profile.gst_number,
        vat_number=profile.vat_number,
        address=profile.address,
        phone_number=profile.phone_number,
        website=profile.website,
        currency=profile.currency,
        business_email=profile.business_email,
    )


@router.get(
    "/profile/me",
    response_model=UserProfileOut,
)
async def get_user_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserProfileOut:

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

    return build_profile_out(user_profile, current_user)


@router.patch("/profile/me", response_model=UserProfileOut)
async def update_user_profile(
    payload: Annotated[UserProfileUpdate, Form()],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserProfileOut:

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

    return build_profile_out(user_profile, current_user)


@router.get("/business-profile/me", response_model=UserBusinessProfileOut)
async def get_user_business_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserBusinessProfileOut:

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

    return build_business_profile_out(user_business_profile)


@router.patch("/business-profile/me", response_model=UserBusinessProfileOut)
async def update_user_business_profile(
    payload: Annotated[UserBusinessProfileUpdate, Form()],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserBusinessProfileOut:

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

    return build_business_profile_out(UserBusinessProfileOut)
