from pydantic import BaseModel, EmailStr, field_validator

from pydantic_core import PydanticCustomError


def validate_password_rules(value: str) -> str:
    if len(value) < 8:
        raise PydanticCustomError(
            "password_too_short",
            "This password is too short. It must contain at least 8 characters.",
        )

    if value.isdigit():
        raise PydanticCustomError(
            "password_entirely_numeric", "This password is entirely numeric."
        )

    return value


class PasswordResetConfirm(BaseModel):
    email: EmailStr
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value) -> str:
        return validate_password_rules(value)
