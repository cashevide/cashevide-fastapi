from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cashevide_api.database import get_db
from cashevide_api.ratelimit import RateLimit
from cashevide_api.users.models import User, UserProfile

router = APIRouter(tags=["account"])


@router.get("/check-user", dependencies=[Depends(RateLimit("check_user", 20))])
async def check_user(
    field: Literal["username", "email"],
    value: Annotated[str, Query(min_length=1)],
    db: AsyncSession = Depends(get_db),
) -> dict[str, bool]:
    column = User.username if field == "username" else User.email
    taken = await db.scalar(select(User.id).where(column == value).limit(1))

    return {"is_available": taken is None}


@router.get(
    "/check-referral-code", dependencies=[Depends(RateLimit("check_referral_code", 20))]
)
async def check_referral_code(
    response: Response, code: str = "", db: AsyncSession = Depends(get_db)
):
    code = code.strip()

    if not code:
        response.status_code = 400
        return {"is_valid": False, "message": "Referral code is required."}

    found = await db.scalar(
        select(UserProfile.id).where(UserProfile.referral_code == code).limit(1)
    )

    if found is None:
        return {"is_valid": False, "message": "Invalid referral code"}

    return {"is_valid": True, "message": "Referral code is valid"}
