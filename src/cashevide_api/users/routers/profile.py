import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cashevide_api.database import get_db
from cashevide_api.dependencies import get_current_user
from cashevide_api.storage import delete_image, media_url, save_image
from cashevide_api.users.models import User, UserBusinessProfile, UserProfile
from cashevide_api.users.schemas import (
    UserBusinessProfileOut,
    UserBusinessProfileUpdate,
    UserProfileOut,
    UserProfileUpdate,
)
from cashevide_api.users.utils import generate_unique_referral_code

logger = logging.getLogger(__name__)

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

    old_key = user_profile.profile_picture
    new_key: str | None = None

    if "profile_picture" in update_data:
        picture = update_data.pop("profile_picture")

        if picture is None or isinstance(picture, str):
            user_profile.profile_picture = None

        else:
            new_key = await save_image(
                upload=picture,
                folder="profile_pictures",
                fmt="jpg",
                field="profile_picture",
            )
            user_profile.profile_picture = new_key

    for field, value in update_data.items():
        setattr(user_profile, field, value)

    try:
        await db.commit()
    except Exception:
        if new_key:
            await delete_image(new_key)
        raise

    await db.refresh(user_profile)

    if old_key and old_key != user_profile.profile_picture:
        try:
            await delete_image(old_key)
        except Exception:
            logger.exception("Could not delete old profile picture %s", old_key)

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

    new_key: str | None = None

    if "logo" in update_data:
        logo = update_data.pop("logo")

        if logo is None or isinstance(logo, str):
            user_business_profile.logo = None
        else:
            new_key = await save_image(
                upload=logo, folder="logos", fmt="png", field="logo"
            )
            user_business_profile.logo = new_key

    for field, value in update_data.items():
        setattr(user_business_profile, field, value)

    try:
        await db.commit()
    except Exception:
        if new_key:
            await delete_image(new_key)
        raise

    await db.refresh(user_business_profile)

    return build_business_profile_out(user_business_profile)
