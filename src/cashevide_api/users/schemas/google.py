from pydantic import BaseModel, Field, field_validator
from typing import Literal


from cashevide_api.users.utils import check_username_characters


class GoogleAuthRequest(BaseModel):
    google_id_token: str = Field(min_length=1)
    platform: Literal["web", "mobile"] = "mobile"
    referral_code_input: str | None = None
    username: str | None = Field(default=None, min_length=1, max_length=150)

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str | None) -> str | None:
        if not value:
            return value

        return check_username_characters(value)
