from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cashevide_api.database import get_db
from cashevide_api.users.models import User

router = APIRouter(tags=["account"])


@router.get("/check-user")
async def check_user(
    filed: Literal["username", "email"],
    value: Annotated[str, Query(min_length=1)],
    db: AsyncSession = Depends(get_db),
) -> dict[str, bool]:
    column = User.username if filed == "username" else User.email
    taken = await db.scalar(select(User.id).where(column == value).limit(1))

    return {"is_available": taken is None}
