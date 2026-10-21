import asyncio
import logging
from dataclasses import dataclass
from collections.abc import Mapping
from typing import Any
import httpx
from urllib.parse import urlparse


from google.auth.exceptions import GoogleAuthError, TransportError
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from cashevide_api.config import settings

logger = logging.getLogger(__name__)

MAX_PICTURE_BYTES = 5 * 1024 * 1024
PICTURE_TIMEOUT_SECONDS = 5


class InvalidGoogleToken(Exception):
    """The Google ID token is invalid, expired, or not usable for login."""


class GoogleUnavailable(Exception):
    """Google's signing certificates could not be fetched (network issue)."""


@dataclass(frozen=True)
class GoogleIdentity:
    email: str
    first_name: str
    last_name: str
    picture_url: str | None

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


def _verify_sync(token: str, client_id: str) -> Mapping[str, Any]:
    return id_token.verify_oauth2_token(token, google_requests.Request(), client_id)


async def verify_google_token(token: str) -> GoogleIdentity:

    if not settings.google_client_id:
        raise RuntimeError("GOOGLE_CLIENT_ID is not configured")

    try:
        info = await asyncio.to_thread(_verify_sync, token, settings.google_client_id)
    except TransportError as exc:
        logger.error("Could not reach Google to verify token: %s", exc)
        raise GoogleUnavailable from exc
    except (ValueError, GoogleAuthError) as exc:
        logger.info("Google token rejected: %s", exc)
        raise InvalidGoogleToken from exc

    email = info.get("email")

    if not email or info.get("email_verified") is not True:
        raise InvalidGoogleToken("Google email is missing or not verified")

    return GoogleIdentity(
        email=email,
        first_name=info.get("given_name", ""),
        last_name=info.get("family_name", ""),
        picture_url=info.get("picture"),
    )


def _is_google_picture_url(url: str) -> bool:
    parsed = urlparse(url)
    host = parsed.hostname or ""
    return parsed.scheme == "https" and (
        host == "googleusercontent.com" or host.endswith(".googleusercontent.com")
    )


async def download_google_picture(url: str | None) -> bytes | None:
    """Download the Google profile picture, or return None.

    The picture is a nice-to-have, so every failure returns None and never
    blocks signup. Only https URLs on googleusercontent.com are fetched,
    redirects are not followed, and the size is capped.
    """
    if not url:
        return None

    if not _is_google_picture_url(url):
        logger.warning("Ignoring Google picture URL on unexpected host")
        return None

    try:
        async with httpx.AsyncClient(
            timeout=PICTURE_TIMEOUT_SECONDS, follow_redirects=False
        ) as client:
            async with client.stream("GET", url) as response:
                response.raise_for_status()

                chunks: list[bytes] = []
                size = 0
                async for chunk in response.aiter_bytes():
                    size += len(chunk)
                    if size > MAX_PICTURE_BYTES:
                        logger.warning("Google picture is larger than the limit")
                        return None
                    chunks.append(chunk)

    except httpx.HTTPError as exc:
        logger.warning("Could not download Google picture: %s", exc)
        return None

    return b"".join(chunks)
