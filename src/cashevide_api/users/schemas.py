from fastapi import Form
from pydantic import BaseModel, ConfigDict, EmailStr
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
    full_name: str | None = Form(default=None, min_length=1)
    # profile_picture: str | None = Form(default=None)
    phone_number: str | None = Form(default=None)
    job_title: str | None = Form(default=None)


class UserBusinessProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    business_name: str | None
    logo: str | None
    gst_number: str | None
    vat_number: str | None
    address: str | None
    phone_number: str | None
    website: str | None
    currency: str | None
    business_email: str | None


class UserBusinessProfileUpdate(BaseModel):
    business_name: str | None = Form(default=None)
    # logo: str | None = Form(default=None)
    gst_number: str | None = Form(default=None)
    vat_number: str | None = Form(default=None)
    address: str | None = Form(default=None)
    phone_number: str | None = Form(default=None)
    website: str | None = Form(default=None)
    currency: str | None = Form(default=None)
    business_email: str | None = Form(default=None)


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
