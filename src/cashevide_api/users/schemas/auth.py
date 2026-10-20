import re
from difflib import SequenceMatcher
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

from cashevide_api.users.schemas.password import validate_password_rules


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    username: str


class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(min_length=1, max_length=150)
    password: str
    full_name: str = Field(min_length=1, max_length=200)
    referral_code_input: str = Field(min_length=1)
    platform: Literal["web", "mobile"] = "mobile"

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        if not re.fullmatch(r"[\w.@+-]+", value):
            raise PydanticCustomError(
                "invalid_username",
                "Enter a valid username. This value may contain only letters, "
                "numbers, and @/./+/-/_ characters.",
            )
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str, info: ValidationInfo) -> str:

        value = validate_password_rules(value)

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
