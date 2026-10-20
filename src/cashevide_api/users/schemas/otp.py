from pydantic import (
    BaseModel,
    EmailStr,
)


class OTPRequest(BaseModel):
    email: EmailStr


class OTPVerify(BaseModel):
    email: EmailStr
    otp: str
