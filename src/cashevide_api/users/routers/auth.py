from fastapi import APIRouter, Cookie, HTTPException, Depends, Response

from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from sqlalchemy import select

from redis.asyncio import Redis

from cashevide_api.ratelimit import RateLimit
from cashevide_api.database import get_db
from cashevide_api.cache import get_redis
from cashevide_api.users.models import User, UserProfile
from cashevide_api.users.schemas import (
    UserOut,
    UserCreate,
    UserLogin,
    LoginResponse,
)
from cashevide_api.users.otp import is_otp_verified, clear_otp_verified
from cashevide_api.users.schemas.token import TokenRefresh
from cashevide_api.users.services import create_user_account
from cashevide_api.security import (
    verify_password_async,
    create_access_token,
    create_refresh_token,
)
from cashevide_api.users.utils import (
    blacklist_refresh_token,
    clear_auth_cookies,
    set_auth_cookies,
)

router = APIRouter(tags=["auth"])


@router.post(
    "/signup",
    response_model=LoginResponse,
    response_model_exclude_none=True,
    status_code=201,
    dependencies=[Depends(RateLimit("signup", 10))],
)
async def signup(
    payload: UserCreate,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> LoginResponse | JSONResponse:

    errors: dict[str, list[str]] = {}

    existing_email = await db.scalar(select(User).where(User.email == payload.email))

    if existing_email is not None:
        errors["email"] = ["user with this email already exists."]

    existing_username = await db.scalar(
        select(User).where(User.username == payload.username)
    )

    if existing_username is not None:
        errors["username"] = ["A user with that username already exists."]

    referrer = await db.scalar(
        select(UserProfile).where(
            UserProfile.referral_code == payload.referral_code_input
        )
    )

    if referrer is None:
        errors["referral_code_input"] = [
            "The referral code provided is incorrect. Please check it."
        ]

    if errors:
        return JSONResponse(status_code=400, content=errors)

    if not await is_otp_verified(redis, payload.email, "signup"):
        return JSONResponse(
            status_code=400,
            content={
                "email": [
                    "This email address has not been verified. "
                    "Please verify it using an OTP first."
                ]
            },
        )

    try:
        user = await create_user_account(db, payload, referrer)

    except IntegrityError:
        await db.rollback()
        return JSONResponse(
            status_code=400,
            content={"error": "An account with these details already exists."},
        )

    await clear_otp_verified(redis, payload.email, "signup")

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    user_out = UserOut.model_validate(user)

    if payload.platform == "web":
        set_auth_cookies(response, access_token, refresh_token)
        return LoginResponse(message="Signup successful", user=user_out)

    return LoginResponse(
        message="Signup successful",
        user=UserOut.model_validate(user),
        access=access_token,
        refresh=refresh_token,
    )


@router.post(
    "/login",
    response_model=LoginResponse,
    response_model_exclude_none=True,
    status_code=200,
    dependencies=[Depends(RateLimit("signup", 10))],
)
async def login(
    payload: UserLogin, response: Response, db: AsyncSession = Depends(get_db)
) -> LoginResponse:
    user = await db.scalar(
        select(User).where(
            User.email == payload.email,
        )
    )

    if user is None or not await verify_password_async(payload.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    if payload.platform == "web":
        set_auth_cookies(response, access_token, refresh_token)

        return LoginResponse(
            message="login successful",
            user=UserOut.model_validate(user),
        )

    return LoginResponse(
        message="login successful",
        user=UserOut.model_validate(user),
        access=access_token,
        refresh=refresh_token,
    )


@router.post("/logout", dependencies=[Depends(RateLimit("logout", 10))])
async def logout(
    response: Response,
    payload: TokenRefresh | None = None,
    db: AsyncSession = Depends(get_db),
    refresh_token_cookie: str | None = Cookie(default=None, alias="refresh_token"),
):
    refresh_token = (payload.refresh if payload else None) or refresh_token_cookie

    if not refresh_token:
        return JSONResponse(
            status_code=400,
            content={"error": "Refresh token is required to logout"},
        )

    if not await blacklist_refresh_token(db, refresh_token):
        return JSONResponse(
            status_code=400, content={"error": "Invalid or expired token"}
        )

    await db.commit()
    clear_auth_cookies(response)

    return {"message": "Successfully logged out"}
