from passlib.context import CryptContext


pwd_context = CryptContext(
    schemes=["django_pbkdf2_sha256"],
    django_pbkdf2_sha256__default_rounds=1_500_000,
)


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hash_password: str) -> bool:
    return pwd_context.verify(plain_password, hash_password)
