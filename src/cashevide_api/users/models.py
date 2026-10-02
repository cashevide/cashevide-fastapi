from datetime import datetime, timezone


from sqlalchemy import Boolean, DateTime, String, BigInteger, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from cashevide_api.database import Base


class User(Base):
    __tablename__ = "users_user"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    username: Mapped[str] = mapped_column(String(150), unique=True)
    password: Mapped[str] = mapped_column(String(128))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    first_name: Mapped[str] = mapped_column(String(150), default="")
    last_name: Mapped[str] = mapped_column(String(150), default="")
    is_staff: Mapped[bool] = mapped_column(Boolean, default=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    date_joined: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    last_login: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class UserProfile(Base):
    __tablename__ = "users_userprofile"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users_user.id", ondelete="CASCADE"), unique=True
    )
    profile_picture: Mapped[str | None] = mapped_column(String(100), nullable=True)
    full_name: Mapped[str] = mapped_column(String(200), default="")
    phone_number: Mapped[str] = mapped_column(String(20), default="")
    job_title: Mapped[str] = mapped_column(String(100), default="")
    referral_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    credit_points: Mapped[int] = mapped_column(default=0)
    referred_by_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users_user.id", ondelete="SET NULL"), nullable=True
    )


class BlacklistedToken(Base):
    __tablename__ = "blacklisted_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    jti: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    blacklisted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class UserBusinessProfile(Base):
    __tablename__ = "users_userbusinessprofile"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users_user.id", ondelete="CASCADE"), unique=True
    )
    business_name: Mapped[str] = mapped_column(String(255), default="")
    logo: Mapped[str | None] = mapped_column(String(100), nullable=True)
    gst_number: Mapped[str] = mapped_column(String(15), default="")
    vat_number: Mapped[str] = mapped_column(String(15), default="")
    address: Mapped[str] = mapped_column(Text, default="")
    phone_number: Mapped[str] = mapped_column(String(20), default="")
    website: Mapped[str] = mapped_column(String(200), default="")
    currency: Mapped[str] = mapped_column(String(3), default="")
    business_email: Mapped[str] = mapped_column(String(254), default="")
