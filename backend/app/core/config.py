"""
Centralised application configuration.

All values are sourced from environment variables / `.env` — nothing sensitive
is hardcoded. Access the singleton via `get_settings()`.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- Brand / core ----
    brand_name: str = Field(default="VoynixAI", alias="BRAND_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=True, alias="DEBUG")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")
    secret_key: str = Field(default="change-me-dev-only", alias="SECRET_KEY")

    # ---- Networking / CORS ----
    backend_host: str = Field(default="0.0.0.0", alias="BACKEND_HOST")
    backend_port: int = Field(default=8000, alias="BACKEND_PORT")
    cors_origins: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")

    # ---- Database (PostgreSQL) ----
    postgres_user: str = Field(default="voynix", alias="POSTGRES_USER")
    postgres_password: str = Field(default="voynix_dev_password", alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="voynixai", alias="POSTGRES_DB")
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    database_url_override: str = Field(default="", alias="DATABASE_URL")

    # ---- Redis ----
    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_url_override: str = Field(default="", alias="REDIS_URL")

    # ---- Auth / JWT ----
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=15, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")
    require_email_verification: bool = Field(default=False, alias="REQUIRE_EMAIL_VERIFICATION")
    email_verification_expire_hours: int = Field(default=48, alias="EMAIL_VERIFICATION_EXPIRE_HOURS")
    password_reset_expire_hours: int = Field(default=2, alias="PASSWORD_RESET_EXPIRE_HOURS")

    # ---- Rate limiting ----
    rate_limit_enabled: bool = Field(default=True, alias="RATE_LIMIT_ENABLED")
    rate_limit_auth_max: int = Field(default=10, alias="RATE_LIMIT_AUTH_MAX")
    rate_limit_auth_window_seconds: int = Field(default=60, alias="RATE_LIMIT_AUTH_WINDOW_SECONDS")

    # ---- External travel data (Amadeus Self-Service; mock fallback if unset) ----
    amadeus_client_id: str = Field(default="", alias="AMADEUS_CLIENT_ID")
    amadeus_client_secret: str = Field(default="", alias="AMADEUS_CLIENT_SECRET")
    amadeus_env: str = Field(default="test", alias="AMADEUS_ENV")

    # ---- AI (Google Gemini; grounded-mock fallback if unset) ----
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL")
    ai_max_history: int = Field(default=12, alias="AI_MAX_HISTORY")  # messages of context

    # ---- Default market (seeded into DB, overridable) ----
    default_country: str = Field(default="AE", alias="DEFAULT_COUNTRY")
    default_city: str = Field(default="Dubai", alias="DEFAULT_CITY")
    default_currency: str = Field(default="AED", alias="DEFAULT_CURRENCY")
    default_locale: str = Field(default="en", alias="DEFAULT_LOCALE")
    default_timezone: str = Field(default="Asia/Dubai", alias="DEFAULT_TIMEZONE")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url(self) -> str:
        if self.database_url_override:
            return self.database_url_override
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def redis_url(self) -> str:
        if self.redis_url_override:
            return self.redis_url_override
        return f"redis://{self.redis_host}:{self.redis_port}/0"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
