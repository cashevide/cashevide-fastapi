from datetime import date, datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from cashevide_api.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class LegalDocument(Base):
    __tablename__ = "legal_legaldocument"
    __table_args__ = (UniqueConstraint("document_type", "version"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    document_type: Mapped[str] = mapped_column(String(20))
    version: Mapped[str] = mapped_column(String(10))
    content: Mapped[str] = mapped_column(Text)
    effective_date: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class UserLegalDocumentAcceptance(Base):
    __tablename__ = "legal_userlegaldocumentacceptance"
    __table_args__ = (UniqueConstraint("user_id", "legal_document_id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users_user.id", ondelete="CASCADE")
    )
    legal_document_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("legal_legaldocument.id", ondelete="CASCADE")
    )
    accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
