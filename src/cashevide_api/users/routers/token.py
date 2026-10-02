from fastapi import APIRouter, HTTPException, Depends, Response, Cookie

from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from cashevide_api.config import settings
from cashevide_api.database import get_db
from cashevide_api.users.models import BlacklistedToken
from cashevide_api.users.schemas import (
    TokenRefreshResponse,
    TokenRefresh,
)
from cashevide_api.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)

router = APIRouter(prefix="/token", tags=["token"])


@router.post(
    "/refresh",
    response_model=TokenRefreshResponse,
    response_model_exclude_none=True,
)
async def refresh_access_token(
    payload: TokenRefresh,
    response: Response,
    db: AsyncSession = Depends(get_db),
    refresh_token_cookie: str | None = Cookie(default=None, alias="refresh_token"),
) -> TokenRefreshResponse:

    platform = payload.platform
    refresh_token = payload.refresh

    if not refresh_token:
        refresh_token = refresh_token_cookie
        if refresh_token:
            platform = "web"

    if not refresh_token:
        raise HTTPException(status_code=400, detail="Refresh token is required")

    try:
        user_id, jti = decode_refresh_token(token=str(refresh_token))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    is_blacklisted = await db.scalar(
        select(BlacklistedToken).where(BlacklistedToken.jti == jti)
    )

    if is_blacklisted is not None:
        raise HTTPException(status_code=401, detail="Refresh token has been revoked")

    db.add(BlacklistedToken(jti=jti))
    await db.commit()

    access_token = create_access_token(user_id=user_id)
    new_refresh_token = create_refresh_token(user_id=user_id)

    if platform == "web":
        response.set_cookie(
            key="access_token",
            value=access_token,
            max_age=settings.jwt_access_token_expire_minutes * 60,
            httponly=True,
            secure=not settings.debug,
            samesite="lax",
            domain=settings.cookie_domain,
        )

        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            max_age=settings.jwt_refresh_token_expire_days * 24 * 60 * 60,
            httponly=True,
            secure=not settings.debug,
            samesite="lax",
            domain=settings.cookie_domain,
        )

        return TokenRefreshResponse(
            message="Token refreshed successfully",
        )

    else:
        return TokenRefreshResponse(
            message="Token refreshed successfully",
            access=access_token,
            refresh=new_refresh_token,
        )
