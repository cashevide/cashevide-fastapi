from sqladmin import Admin

from cashevide_api.users.admin import UserAdmin, UserProfileAdmin, BlacklistedTokenAdmin


def register_admin_views(admin: Admin):
    admin.add_view(UserAdmin)
    admin.add_view(UserProfileAdmin)
    admin.add_view(BlacklistedTokenAdmin)
