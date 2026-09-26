from fastapi import APIRouter, HTTPException, Depends

from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from cashevide_api.database import get_db
from cashevide_api.users.models import User
from cashevide_api.users.schemas import UserOut, UserCreate, UserLogin, LoginResponse
from cashevide_api.security import hash_password, verify_password, create_access_token
from cashevide_api.dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/profile/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


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


@router.post("/login", response_model=LoginResponse, status_code=200)
async def login(
    payload: UserLogin, db: AsyncSession = Depends(get_db)
) -> LoginResponse:
    user = await db.scalar(
        select(User).where(
            User.email == payload.email,
        )
    )

    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not verify_password(payload.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return LoginResponse(
        user=UserOut.model_validate(user),
        access_token=create_access_token(str(user.id)),
    )
