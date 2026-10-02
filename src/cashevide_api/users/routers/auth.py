from fastapi import APIRouter, HTTPException, Depends, Response

from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from cashevide_api.config import settings
from cashevide_api.database import get_db
from cashevide_api.users.models import User
from cashevide_api.users.schemas import (
    UserOut,
    UserCreate,
    UserLogin,
    LoginResponse,
)
from cashevide_api.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
)

router = APIRouter(tags=["auth"])


@router.post("/signup", response_model=UserOut, status_code=201)
async def signup(payload: UserCreate, db: AsyncSession = Depends(get_db)) -> User:
    existing_email = await db.scalar(select(User).where(User.email == payload.email))

    if existing_email is not None:
        raise HTTPException(status_code=400, detail="Email already registered")

    existing_username = await db.scalar(
        select(User).where(User.username == payload.username)
    )

    if existing_username is not None:
        raise HTTPException(status_code=400, detail="Username already registered")

    user = User(
        email=payload.email,
        username=payload.username,
        password=hash_password(payload.password),
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


@router.post(
    "/login",
    response_model=LoginResponse,
    response_model_exclude_none=True,
    status_code=200,
)
async def login(
    payload: UserLogin, response: Response, db: AsyncSession = Depends(get_db)
) -> LoginResponse:
    user = await db.scalar(
        select(User).where(
            User.email == payload.email,
        )
    )

    if user is None or not verify_password(payload.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    if payload.platform == "web":
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
            value=refresh_token,
            max_age=settings.jwt_refresh_token_expire_days * 24 * 60 * 60,
            httponly=True,
            secure=not settings.debug,
            samesite="lax",
            domain=settings.cookie_domain,
        )

        return LoginResponse(
            message="login successful",
            user=UserOut.model_validate(user),
        )

    else:
        return LoginResponse(
            message="login successful",
            user=UserOut.model_validate(user),
            access=access_token,
            refresh=refresh_token,
        )
