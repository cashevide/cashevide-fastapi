from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from cashevide_api.users.schemas.auth import UserCreate
from cashevide_api.users.models import (
    UserProfile,
    User,
    UserBusinessProfile,
    UserSubscription,
)
from cashevide_api.security import hash_password_async
from cashevide_api.legal.models import LegalDocument, UserLegalDocumentAcceptance
from cashevide_api.users.utils import generate_unique_referral_code


SIGNUP_BONUS_CREDITS = 25
REFEREE_BONUS_CREDITS = 25
REFERRER_BONUS_CREDITS = 25


async def create_user_account(
    db: AsyncSession, payload: UserCreate, referrer: UserProfile | None = None
) -> User:

    user = User(
        email=payload.email,
        username=payload.username,
        password=await hash_password_async(payload.password),
    )

    db.add(user)
    await db.flush()

    credits = SIGNUP_BONUS_CREDITS
    referred_by_id = None

    if referrer is not None:
        credits += REFEREE_BONUS_CREDITS
        referred_by_id = referrer.user_id

        await db.execute(
            update(UserProfile)
            .where(UserProfile.id == referrer.id)
            .values(credit_points=UserProfile.credit_points + REFERRER_BONUS_CREDITS)
        )

    db.add(
        UserProfile(
            user_id=user.id,
            full_name=payload.full_name,
            referral_code=await generate_unique_referral_code(db),
            referred_by_id=referred_by_id,
            credit_points=credits,
        )
    )

    legal_document_ids = await db.scalars(
        select(LegalDocument.id).where(LegalDocument.is_active.is_(True))
    )
    db.add_all(
        UserLegalDocumentAcceptance(user_id=user.id, legal_document_id=doc_id)
        for doc_id in legal_document_ids
    )

    db.add(UserBusinessProfile(user_id=user.id))
    db.add(UserSubscription(user_id=user.id))

    await db.commit()
    await db.refresh(user)

    return user
