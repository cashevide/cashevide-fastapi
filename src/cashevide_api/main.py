from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqladmin import Admin
from starlette.middleware.sessions import SessionMiddleware

from cashevide_api.admin import AdminAuth, register_admin_views
from cashevide_api.config import settings
from cashevide_api.database import engine
from cashevide_api.users.router import router as users_router

app = FastAPI(title="Cashevide API", debug=settings.debug)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key=settings.jwt_secret_key)

api_router = APIRouter(prefix="/api")

api_router.include_router(users_router)

app.include_router(api_router)


admin = Admin(
    app, engine, authentication_backend=AdminAuth(secret_key=settings.jwt_secret_key)
)
register_admin_views(admin)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "Cashevide API",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
