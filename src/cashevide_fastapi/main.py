from fastapi import FastAPI
from cashevide_fastapi.config import settings

app = FastAPI(title="Cashevide API", debug=settings.debug)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
