from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    debug: bool = False

    db_user: str
    db_password: str
    db_name: str
    db_host: str = "localhost"
    db_port: int = 5432
    db_echo: bool = False

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 5
    jwt_refresh_token_expire_days: int = 90

    cookie_domain: str | None = None

    cors_allowed_origins: str = ""

    use_s3_storage: bool = False
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_storage_bucket_name: str | None = None
    aws_s3_endpoint_url: str | None = None
    aws_s3_custom_domain: str | None = None
    media_root: str = "media"
    media_base_url: str = "http://localhost:8001/media/"
    max_image_upload_mb: int = 10

    admin_email: str | None = None
    admin_username: str = "admin"
    admin_password: str | None = None

    @model_validator(mode="after")
    def check_s3_settings(self) -> "Settings":
        if self.use_s3_storage:
            required = {
                "AWS_ACCESS_KEY_ID": self.aws_access_key_id,
                "AWS_SECRET_ACCESS_KEY": self.aws_secret_access_key,
                "AWS_STORAGE_BUCKET_NAME": self.aws_storage_bucket_name,
                "AWS_S3_ENDPOINT_URL": self.aws_s3_endpoint_url,
                "AWS_S3_CUSTOM_DOMAIN": self.aws_s3_custom_domain,
            }
            missing = [name for name, value in required.items() if not value]
            if missing:
                raise ValueError(f"USE_S3_STORAGE=True needs: {', '.join(missing)}")
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        if not self.cors_allowed_origins:
            return []

        return [origin.strip() for origin in self.cors_allowed_origins.split(",")]

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()  # type: ignore
