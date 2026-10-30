from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column


def _now() -> datetime:
    return datetime.now(timezone.utc)


class TimestampedMixin:
    """created_at, updated_at and is_active, like Django's core.BaseModel.

    Django filled these in Python, so the existing tables have no database
    defaults. They are set here instead.
    """

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
