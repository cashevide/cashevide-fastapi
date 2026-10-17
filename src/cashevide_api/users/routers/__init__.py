from fastapi import APIRouter

from cashevide_api.users.routers.account import router as account_router
from cashevide_api.users.routers.auth import router as auth_router
from cashevide_api.users.routers.profile import router as profile_router
from cashevide_api.users.routers.token import router as token_router
from cashevide_api.users.routers.otp import router as otp_router

router = APIRouter(prefix="/users")

router.include_router(auth_router)
router.include_router(profile_router)
router.include_router(token_router)
router.include_router(account_router)
router.include_router(otp_router)
