from fastapi import FastAPI, APIRouter
from cashevide_api.config import settings

from cashevide_api.users.router import router as users_router

app = FastAPI(title="Cashevide API", debug=settings.debug)


api_router = APIRouter(prefix="/api")

api_router.include_router(users_router)

app.include_router(api_router)


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
