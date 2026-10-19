import re
from difflib import SequenceMatcher
from fastapi import UploadFile
from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    ValidationInfo,
)
from pydantic_core import PydanticCustomError
from typing import Literal


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    username: str


class UserProfileOut(BaseModel):
    user_id: int
    email: str
    username: str
    full_name: str
    profile_picture: str | None
    phone_number: str
    job_title: str
    referral_code: str
    referred_by: int | None
    credit_points: int


class OTPRequest(BaseModel):
    email: EmailStr


class OTPVerify(BaseModel):
    email: EmailStr
    otp: str


class UserProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=3)
    profile_picture: UploadFile | str | None = None
    phone_number: str | None = None
    job_title: str | None = None

    @field_validator("profile_picture")
    @classmethod
    def only_file_or_empty(cls, value: UploadFile | str | None):
        if isinstance(value, str) and value != "":
            raise PydanticCustomError(
                "not_a_file",
                "The submitted data was not a file. "
                "Check the encoding type on the form.",
            )
        return value


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
    business_name: str | None = Field(default=None)
    logo: UploadFile | str | None = Field(default=None)
    gst_number: str | None = Field(default=None)
    vat_number: str | None = Field(default=None)
    address: str | None = Field(default=None)
    phone_number: str | None = Field(default=None)
    website: str | None = Field(default=None)
    currency: str | None = Field(default=None)
    business_email: str | None = Field(default=None)

    @field_validator("logo")
    @classmethod
    def only_file_or_empty(cls, value: UploadFile | str | None):
        if isinstance(value, str) and value != "":
            raise PydanticCustomError(
                "not_a_file",
                "The submitted data was not a file. "
                "Check the encoding type on the form.",
            )
        return value


class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(min_length=1, max_length=150)
    password: str
    full_name: str = Field(min_length=1, max_length=200)
    referral_code_input: str = Field(min_length=1)
    platform: Literal["web", "mobile"] = "mobile"

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str, info: ValidationInfo) -> str:
        if len(value) < 8:
            raise PydanticCustomError(
                "password_too_short",
                "This password is too short. It must contain at least 8 characters.",
            )

        if value.isdigit():
            raise PydanticCustomError(
                "password_entirely_numeric", "This password is entirely numeric."
            )

        for field, label in (("username", "username"), ("email", "email address")):
            attribute = info.data.get(field)

            if not attribute:
                continue

            attribute = str(attribute).lower()

            for part in [*re.split(r"\W+", attribute), attribute]:
                if (
                    part
                    and SequenceMatcher(a=value.lower(), b=part).quick_ratio() >= 0.7
                ):
                    raise PydanticCustomError(
                        "password_too_similar",
                        "The password is too similar to the {label}.",
                        {"label": label},
                    )
        return value


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
