from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Literal


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    username: str


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str
    platform: Literal["web", "mobile"] = "mobile"


class LoginResponse(BaseModel):
    message: str
    user: UserOut


class MobileLoginResponse(LoginResponse):
    access: str | None
    refresh: str | None


class TokenRefresh(BaseModel):
    platform: Literal["web", "mobile"] = "mobile"
    refresh: str | None


class TokenRefreshResponse(BaseModel):
    message: str
    access: str | None
    refresh: str | None
