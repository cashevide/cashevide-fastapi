from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column


from cashevide_fastapi.database import Base


class User(Base):
    __tablename__ = "users_user"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    username: Mapped[str] = mapped_column(String(150), unique=True)
    password: Mapped[str] = mapped_column(String(128))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
