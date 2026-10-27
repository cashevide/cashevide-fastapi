from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from cashevide_api.users.models import UserSubscription


class TierLimitError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


async def check_tier_limit(
    db: AsyncSession,
    *,
    user_id: int,
    model,
    limits: dict[str, int],
    action: str,
    item_name: str,
) -> None:

    tier = await db.scalar(
        select(UserSubscription.tier).where(UserSubscription.user_id == user_id)
    )

    max_allowed = limits.get(tier) if tier else None

    if max_allowed is None:
        return

    current = await db.scalar(
        select(func.count())
        .select_from(model)
        .where(
            model.user_id == user_id,
            model.is_active.is_(True),
            model.is_archived.is_(False),
        )
    )

    if current >= max_allowed:
        raise TierLimitError(
            f"You cannot {action} more than {max_allowed} {item_name} in {tier} plan"
        )
