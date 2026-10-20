from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


from cashevide_api.cache import get_redis
from cashevide_api.database import get_db
from cashevide_api.users.models import User
from cashevide_api.users.otp import OTPError, request_otp, verify_otp
from cashevide_api.users.schemas import OTPRequest, OTPVerify

router = APIRouter(tags=["otp"])


@router.post("/signup-request-otp")
async def signup_request_otp(
    payload: OTPRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    taken = await db.scalar(select(User.id).where(User.email == payload.email).limit(1))

    if taken is not None:
        return JSONResponse(
            status_code=400,
            content={"email": ["An account with this email address already exists."]},
        )

    try:
        await request_otp(redis, payload.email, "signup")
    except OTPError as exc:
        return JSONResponse(status_code=400, content=exc.content)

    return {"message": "An OTP has been successfully sent to your email address."}


@router.post("/signup-verify-otp")
async def signup_verify_otp(payload: OTPVerify, redis: Redis = Depends(get_redis)):
    try:
        await verify_otp(redis, payload.email, payload.otp, "signup")

    except OTPError as exc:
        return JSONResponse(status_code=400, content=exc.content)

    return {"message": "Email verification successful."}


@router.post("/password-reset-request-otp")
async def password_reset_request_otp(
    payload: OTPRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    message = {"message": "If an account exists, an OTP has been sent."}

    exists = await db.scalar(
        select(User.id).where(User.email == payload.email).limit(1)
    )

    if exists is None:
        return message

    try:
        await request_otp(redis, payload.email, "password_reset")

    except OTPError as exc:
        return JSONResponse(status_code=400, content=exc.content)

    return message


@router.post("/password-reset-verify-otp")
async def password_reset_verify_otp(
    payload: OTPVerify, redis: Redis = Depends(get_redis)
):
    try:
        await verify_otp(redis, payload.email, payload.otp, "password_reset")

    except OTPError as exc:
        return JSONResponse(status_code=400, content=exc.content)

    return {"message": "Email verification successful."}
