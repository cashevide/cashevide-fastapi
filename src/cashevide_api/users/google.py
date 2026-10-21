import asyncio
import logging
from dataclasses import dataclass
from collections.abc import Mapping
from typing import Any


from google.auth.exceptions import GoogleAuthError, TransportError
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from cashevide_api.config import settings

logger = logging.getLogger(__name__)


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
