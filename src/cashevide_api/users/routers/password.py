from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cashevide_api.cache import get_redis
from cashevide_api.database import get_db
from cashevide_api.security import hash_password_async
from cashevide_api.users.models import User
from cashevide_api.users.otp import clear_otp_verified, is_otp_verified
from cashevide_api.users.schemas import PasswordResetConfirm


router = APIRouter(tags=["password"])


@router.post("/reset-password")
async def reset_password(
    payload: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    if not is_otp_verified(redis, payload.email, "password_reset"):
        return JSONResponse(
            status_code=400,
            content={
                "email": [
                    "This email address has not been verified. "
                    "Please verify it using an OTP first."
                ]
            },
        )

    user = await db.scalar(select(User).where(User.email == payload.email).limit(1))

    if user is None:
        raise HTTPException(status_code=404, detail="No User matches the given query.")

    user.password = await hash_password_async(payload.new_password)
    await db.commit()

    await clear_otp_verified(redis, payload.email, "password_reset")

    return {"detail": "Password has been updated successfully."}
