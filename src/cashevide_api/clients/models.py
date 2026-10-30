from sqlalchemy import BigInteger, Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from cashevide_api.core.models import TimestampedMixin
from cashevide_api.database import Base


class Client(TimestampedMixin, Base):
    __tablename__ = "clients_client"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users_user.id"))
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(254), default="")
    phone: Mapped[str] = mapped_column(String(20))
    address: Mapped[str] = mapped_column(Text, default="")
    slug: Mapped[str] = mapped_column(String(50), unique=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
