from pydantic import (
    BaseModel,
    EmailStr,
    field_validator,
)

from cashevide_api.users.schemas.password import validate_password_rules


class OTPRequest(BaseModel):
    email: EmailStr


class OTPVerify(BaseModel):
    email: EmailStr
    otp: str


class PasswordResetConfirm(BaseModel):
    email: EmailStr
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value) -> str:
        return validate_password_rules(value)
