from fastapi import APIRouter, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqladmin import Admin
from starlette.middleware.sessions import SessionMiddleware

from cashevide_api.admin import AdminAuth, register_admin_views
from cashevide_api.config import settings
from cashevide_api.database import engine
from cashevide_api.users.routers import router as users_router
from pathlib import Path

from fastapi.staticfiles import StaticFiles

from cashevide_api.storage import ImageError

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

if not settings.use_s3_storage:
    media_dir = Path(settings.media_root)
    media_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/media", StaticFiles(directory=media_dir), name="media")


admin = Admin(
    app, engine, authentication_backend=AdminAuth(secret_key=settings.jwt_secret_key)
)
register_admin_views(admin)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors: dict[str, list[str]] = {}

    for error in exc.errors():
        field = str(error["loc"][-1])
        errors.setdefault(field, []).append(error["msg"])

    return JSONResponse(status_code=422, content=errors)


@app.exception_handler(ImageError)
async def image_error_handler(request: Request, exc: ImageError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})


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
