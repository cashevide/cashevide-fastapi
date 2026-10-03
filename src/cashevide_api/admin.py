from fastapi import Request
from sqladmin import Admin
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy import select

from cashevide_api.database import AsyncSessionLocal
from cashevide_api.security import verify_password
from cashevide_api.users.admin import (
    BlacklistedTokenAdmin,
    UserAdmin,
    UserProfileAdmin,
    UserBusinessProfileAdmin,
)
from cashevide_api.users.models import User


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        email = form.get("username")
        password = form.get("password")

        async with AsyncSessionLocal() as db:
            user = await db.scalar(select(User).where(User.email == email))

            if user is None or not verify_password(str(password), user.password):
                return False

            if not user.is_superuser:
                return False

        request.session.update({"admin_user_id": user.id})
        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return "admin_user_id" in request.session


def register_admin_views(admin: Admin):
    admin.add_view(UserAdmin)
    admin.add_view(UserProfileAdmin)
    admin.add_view(BlacklistedTokenAdmin)
    admin.add_view(UserBusinessProfileAdmin)
