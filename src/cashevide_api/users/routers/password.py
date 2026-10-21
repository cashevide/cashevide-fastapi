from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cashevide_api.cache import get_redis
from cashevide_api.database import get_db
from cashevide_api.ratelimit import RateLimit
from cashevide_api.security import (
    has_usable_password,
    hash_password_async,
    verify_password_async,
)
from cashevide_api.dependencies import get_current_user
from cashevide_api.users.models import User
from cashevide_api.users.otp import clear_otp_verified, is_otp_verified
from cashevide_api.users.schemas import PasswordResetConfirm
from cashevide_api.users.schemas.password import PasswordChange
from cashevide_api.users.utils import blacklist_refresh_token, clear_auth_cookies


router = APIRouter(tags=["password"])


@router.post("/reset-password", dependencies=[Depends(RateLimit("reset_password", 10))])
async def reset_password(
    payload: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    if not await is_otp_verified(redis, payload.email, "password_reset"):
        return JSONResponse(
            status_code=400,
            content={
                "email": [
                    "This email address has not been verified. "
                    "Please verify it using an OTP first."
                ]
            },
        )

    user = await db.scalar(select(User).where(User.email == payload.email))

    if user is None:
        raise HTTPException(status_code=404, detail="No User matches the given query.")

    user.password = await hash_password_async(payload.new_password)
    await db.commit()

    await clear_otp_verified(redis, payload.email, "password_reset")

    return {"detail": "Password has been updated successfully."}


@router.post(
    "/change-password", dependencies=[Depends(RateLimit("change_password", 10))]
)
async def change_password(
    payload: PasswordChange,
    response: Response,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    refresh_token_cookie: str | None = Cookie(default=None, alias="refresh_token"),
):
    if has_usable_password(user.password):
        if not payload.current_password:
            return JSONResponse(
                status_code=400, content={"detail": ["Current password is required."]}
            )

        if not await verify_password_async(payload.current_password, user.password):
            return JSONResponse(
                status_code=400, content={"detail": ["Invalid current password."]}
            )

    user.password = await hash_password_async(payload.new_password)
    await blacklist_refresh_token(db, payload.refresh or refresh_token_cookie)
    await db.commit()

    clear_auth_cookies(response)

    return {"message": "Password has been updated successfully."}
