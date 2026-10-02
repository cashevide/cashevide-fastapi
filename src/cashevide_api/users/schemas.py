from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Literal


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    username: str


class UserProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    full_name: str
    profile_picture: str | None
    phone_number: str | None
    job_title: str | None
    referral_code: str
    referred_by_id: int | None
    credit_points: int | None


class UserProfileUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    full_name: str | None = Field(default=None, min_length=1)
    profile_picture: str | None = None
    phone_number: str | None = None
    job_title: str | None = None


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
    access: str | None = None
    refresh: str | None = None


class TokenRefresh(BaseModel):
    platform: Literal["web", "mobile"] = "mobile"
    refresh: str | None = None


class TokenRefreshResponse(BaseModel):
    message: str
    access: str | None = None
    refresh: str | None = None
