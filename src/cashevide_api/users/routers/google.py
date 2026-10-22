import logging

from fastapi import APIRouter, Depends, Response
from fastapi.responses import JSONResponse
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from cashevide_api.database import get_db
from cashevide_api.ratelimit import RateLimit
from cashevide_api.users.google import (
    GoogleUnavailable,
    InvalidGoogleToken,
    download_google_picture,
    verify_google_token,
)
from cashevide_api.users.models import User, UserProfile
from cashevide_api.users.schemas.auth import LoginResponse, UserOut
from cashevide_api.users.schemas.google import GoogleAuthRequest
from cashevide_api.security import (
    create_access_token,
    create_refresh_token,
    make_unusable_password,
)
from cashevide_api.users.services import create_user_account
from cashevide_api.users.utils import set_auth_cookies
from cashevide_api.storage import delete_image, save_image_bytes

logger = logging.getLogger(__name__)

router = APIRouter(tags=["google"])


async def _save_google_picture(url: str | None) -> str | None:

    data = await download_google_picture(url)

    if data is None:
        return None

    try:
        return await save_image_bytes(data, "profile_pictures", "jpg")

    except Exception:
        logger.warning("Could not save Google profile picture", exc_info=True)
        return None


@router.post(
    "/google",
    response_model=LoginResponse,
    response_model_exclude_none=True,
    dependencies=[Depends(RateLimit("google", 10))],
)
async def google_auth(
    payload: GoogleAuthRequest, response: Response, db: AsyncSession = Depends(get_db)
) -> LoginResponse | JSONResponse:

    try:
        identity = await verify_google_token(payload.google_id_token)
    except InvalidGoogleToken:
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid or expired Google token."},
        )

    except GoogleUnavailable:
        return JSONResponse(
            status_code=503,
            content={
                "error": "Service temporarily unavailable. Please try again later."
            },
        )

    user = await db.scalar(select(User).where(User.email == identity.email))
    is_signup = False

    if not user:
        if not payload.referral_code_input:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "prompt_referral",
                    "email": identity.email,
                    "full_name": identity.full_name,
                },
            )

        if not payload.username:
            return JSONResponse(
                status_code=400,
                content={"username": ["This field is required for new users."]},
            )

        errors: dict[str, list[str]] = {}

        referrer = await db.scalar(
            select(UserProfile).where(
                UserProfile.referral_code == payload.referral_code_input
            )
        )

        if referrer is None:
            errors["referral_code_input"] = [
                "The referral code provided is incorrect. Please check it."
            ]

        username_taken = await db.scalar(
            select(User.id).where(func.lower(User.username) == payload.username.lower())
        )

        if username_taken is not None:
            errors["username"] = [
                "This username is already taken. Please choose another one."
            ]

        if errors:
            return JSONResponse(status_code=400, content=errors)

        picture_key = await _save_google_picture(identity.picture_url)

        try:
            user = await create_user_account(
                db,
                email=identity.email,
                username=payload.username,
                full_name=identity.full_name[:200],
                password_hash=make_unusable_password(),
                referrer=referrer,
                profile_picture=picture_key,
            )

        except IntegrityError:
            await db.rollback()
            await delete_image(picture_key)
            return JSONResponse(
                status_code=400,
                content={"error": "An account with these details already exists."},
            )

        except Exception:
            await delete_image(picture_key)
            raise

        is_signup = True

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    user_out = UserOut.model_validate(user)
    message = "Signup successful" if is_signup else "login successful"

    response.status_code = 201 if is_signup else 200

    if payload.platform == "web":
        set_auth_cookies(response, access_token, refresh_token)
        return LoginResponse(message=message, user=user_out)

    return LoginResponse(
        message=message, user=user_out, access=access_token, refresh=refresh_token
    )
