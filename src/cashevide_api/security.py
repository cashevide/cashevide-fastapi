from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from cashevide_api.config import settings


pwd_context = CryptContext(
    schemes=["django_pbkdf2_sha256"],
    django_pbkdf2_sha256__default_rounds=1_500_000,
)


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hash_password: str) -> bool:
    return pwd_context.verify(plain_password, hash_password)


def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_access_token_expire_minutes
    )

    payload = {"sub": str(user_id), "exp": expire}

    return jwt.encode(
        payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )


def decode_access_token(token: str) -> int:
    paylod = jwt.decode(
        token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
    )

    return int(paylod["sub"])
