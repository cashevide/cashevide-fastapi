import asyncio

from sqlalchemy import select

from cashevide_api.config import settings
from cashevide_api.database import AsyncSessionLocal
from cashevide_api.security import hash_password
from cashevide_api.users.models import User


async def create_superuser() -> None:
    if not settings.admin_email or not settings.admin_password:
        print("ADMIN_EMAIL/ADMIN_PASSWORD not set, skipping superuser creation.")
        return

    async with AsyncSessionLocal() as db:
        existing = await db.scalar(
            select(User).where(User.email == settings.admin_email)
        )

        if existing is not None:
            print("Superuser already exists.")
            return

        superuser = User(
            email=settings.admin_email,
            username=settings.admin_username,
            password=hash_password(settings.admin_password),
            is_superuser=True,
            is_staff=True,
        )
        db.add(superuser)
        await db.commit()
        print(f"Superuser created: {settings.admin_email}")


if __name__ == "__main__":
    asyncio.run(create_superuser())
