from fastapi import Request


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
