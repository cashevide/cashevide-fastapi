from fastapi import Depends, HTTPException, Request
from redis.asyncio import Redis

from cashevide_api.cache import get_redis


def get_client_ip(request: Request) -> str:
    """Return the real client IP.

    nginx sets X-Real-IP from $remote_addr, and with the Cloudflare realip
    config that is the real visitor IP (not spoofable). If the header is
    missing or blank (e.g. local dev without nginx), fall back to the
    direct peer address.
    """
    real_ip = (request.headers.get("x-real-ip") or "").strip()
    if real_ip:
        return real_ip
    return request.client.host if request.client else "unknown"


class RateLimit:
    """Fixed-window rate limit per client IP, used as a route dependency.

    Example: @router.post("/login", dependencies=[Depends(RateLimit("login", 10))])
    """

    def __init__(self, name: str, limit: int, window: int = 60):
        self.name = name
        self.limit = limit
        self.window = window

    async def __call__(
        self, request: Request, redis: Redis = Depends(get_redis)
    ) -> None:
        key = f"ratelimit:{self.name}:{get_client_ip(request)}"

        # One atomic transaction: count the request, set the expiry only if
        # the key has none yet (NX), and read the remaining time.
        async with redis.pipeline(transaction=True) as pipe:
            pipe.incr(key)
            pipe.expire(key, self.window, nx=True)
            pipe.ttl(key)
            count, _, ttl = await pipe.execute()

        if count > self.limit:
            retry_after = max(ttl, 1)
            raise HTTPException(
                status_code=429,
                detail=f"Request was throttled. Expected available in {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)},
            )
