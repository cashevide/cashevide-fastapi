from fastapi import FastAPI
from cashevide_fastapi.config import settings

from cashevide_fastapi.users.router import router as users_router

app = FastAPI(title="Cashevide API", debug=settings.debug)

app.include_router(users_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
