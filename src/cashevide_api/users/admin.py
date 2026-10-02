from sqladmin import ModelView

from cashevide_api.users.models import User, UserProfile, BlacklistedToken


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.email, User.username, User.is_active, User.is_staff]
    column_searchable_list = [User.email, User.username]
    form_excluded_columns = [User.password]


class UserProfileAdmin(ModelView, model=UserProfile):
    column_list = [
        UserProfile.id,
        UserProfile.user_id,
        UserProfile.full_name,
        UserProfile.referral_code,
        UserProfile.credit_points,
    ]
    column_searchable_list = [UserProfile.referral_code]


class BlacklistedTokenAdmin(ModelView, model=BlacklistedToken):
    column_list = [
        BlacklistedToken.id,
        BlacklistedToken.jti,
        BlacklistedToken.blacklisted_at,
    ]
