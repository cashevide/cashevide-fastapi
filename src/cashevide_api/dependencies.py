from fastapi import HTTPException, Depends, Cookie
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from sqlalchemy.ext.asyncio import AsyncSession

from cashevide_api.database import get_db
from cashevide_api.security import decode_access_token
from cashevide_api.users.models import User


bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    access_token_cookie: str | None = Cookie(default=None, alias="access_token"),
    db: AsyncSession = Depends(get_db),
) -> User:

    token = credentials.credentials if credentials else access_token_cookie

    if token is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        user_id = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = await db.get(User, user_id)

    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user
