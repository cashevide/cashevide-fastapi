from fastapi import HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from sqlalchemy.ext.asyncio import AsyncSession

from cashevide_api.database import get_db
from cashevide_api.security import decode_access_token
from cashevide_api.users.models import User


bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:

    try:
        user_id = decode_access_token(credentials.credentials)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = await db.get(User, user_id)

    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user
