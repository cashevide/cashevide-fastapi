from pydantic import (
    BaseModel,
)
from typing import Literal


class TokenRefresh(BaseModel):
    platform: Literal["web", "mobile"] = "mobile"
    refresh: str | None = None


class TokenRefreshResponse(BaseModel):
    message: str
    access: str | None = None
    refresh: str | None = None
