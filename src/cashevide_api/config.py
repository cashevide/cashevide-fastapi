from pydantic_settings import BaseSettings, SettingsConfigDict


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

    admin_email: str | None = None
    admin_username: str = "admin"
    admin_password: str | None = None

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
