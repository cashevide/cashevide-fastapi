from fastapi import APIRouter, Response
from redis.exceptions import RedisError

from cashevide_api.cache import redis_client

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(response: Response) -> dict[str, str]:
    try:
        await redis_client.ping()
    except RedisError:
        response.status_code = 503
        return {"status": "error", "redis": "unreachable"}

    return {"status": "ok", "redis": "ok"}
