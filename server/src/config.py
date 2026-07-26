import json
from typing import List, Optional
from datetime import timedelta
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AliasChoices, Field


class DatabaseConfig(BaseSettings):
    url: str = Field(
        default="sqlite:///db.sqlite3",
        validation_alias=AliasChoices("DATABASE_URL", "DATABASE__URL"),
    )
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class AWSConfig(BaseSettings):
    cloudfront_domain: str = Field(
        default="",
        validation_alias=AliasChoices("AWS__CLOUDFRONT_DOMAIN", "AWS_CLOUDFRONT_DOMAIN"),
    )
    cloudfront_key_pair_id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("AWS__CLOUDFRONT_KEY_PAIR_ID", "AWS_CLOUDFRONT_KEY_PAIR_ID"),
    )
    cloudfront_private_key: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("AWS__CLOUDFRONT_PRIVATE_KEY", "AWS_CLOUDFRONT_PRIVATE_KEY"),
    )
    cloudfront_signed_url_ttl_seconds: int = Field(
        default=900,
        validation_alias=AliasChoices(
            "AWS__CLOUDFRONT_SIGNED_URL_TTL_SECONDS",
            "AWS_CLOUDFRONT_SIGNED_URL_TTL_SECONDS",
        ),
    )
    cloudfront_sign_wildcard: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AWS__CLOUDFRONT_SIGN_WILDCARD",
            "AWS_CLOUDFRONT_SIGN_WILDCARD",
        ),
    )

    s3_bucket_name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("AWS__S3_BUCKET_NAME", "AWS_S3_BUCKET_NAME"),
    )
    s3_region_name: str = Field(
        default="ap-south-2",
        validation_alias=AliasChoices("AWS__REGION", "AWS_S3_REGION_NAME"),
    )
    keys_bucket_name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("AWS__KEYS_BUCKET_NAME", "AWS_KEYS_BUCKET_NAME"),
    )

    use_s3: bool = Field(default=False, alias="AWS__USE_S3")
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class JWTConfig(BaseSettings):
    secret_key: str = Field(
        default="jwt-secret-key-replace-in-production", alias="JWT_SECRET_KEY"
    )
    access_token_lifetime_minutes: int = Field(
        default=60, alias="JWT_ACCESS_TOKEN_LIFETIME_MINUTES"
    )  # 1 hour
    refresh_token_lifetime_days: int = Field(
        default=7, alias="JWT_REFRESH_TOKEN_LIFETIME_DAYS"
    )  # 7 days
    algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    rotate_refresh_tokens: bool = Field(default=True, alias="JWT_ROTATE_REFRESH_TOKENS")
    blacklist_after_rotation: bool = Field(
        default=True, alias="JWT_BLACKLIST_AFTER_ROTATION"
    )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def access_token_lifetime(self) -> timedelta:
        return timedelta(minutes=self.access_token_lifetime_minutes)

    @property
    def refresh_token_lifetime(self) -> timedelta:
        return timedelta(days=self.refresh_token_lifetime_days)


class TurnstileConfig(BaseSettings):
    secret_key: str = Field(default="", alias="CLOUDFLARE_TURNSTILE_SECRET_KEY")
    enabled: Optional[bool] = Field(default=None, alias="TURNSTILE_ENABLED")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def is_enabled(self) -> bool:
        if self.enabled is not None:
            return self.enabled
        return bool(self.secret_key.strip())


class AppConfig(BaseSettings):
    debug: bool = Field(default=True, alias="DEBUG")
    secret_key: str = Field(
        default="django-insecure-replace-this-in-production", alias="SECRET_KEY"
    )
    allowed_hosts: str = Field(
        default='["localhost", "127.0.0.1"]',
        alias="ALLOWED_HOSTS",
    )
    cors_allowed_origins: str = Field(
        default='["http://localhost:3000"]',
        alias="CORS_ALLOWED_ORIGINS",
    )

    db: DatabaseConfig = DatabaseConfig()
    aws: AWSConfig = AWSConfig()
    jwt: JWTConfig = JWTConfig()
    turnstile: TurnstileConfig = TurnstileConfig()

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @staticmethod
    def _parse_list_setting(raw: str) -> List[str]:
        """Accept either JSON array string or comma-separated string values."""
        value = (raw or "").strip()
        if not value:
            return []

        if value.startswith("["):
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
            return []

        return [part.strip() for part in value.split(",") if part.strip()]

    @property
    def allowed_hosts_list(self) -> List[str]:
        return self._parse_list_setting(self.allowed_hosts)

    @property
    def cors_allowed_origins_list(self) -> List[str]:
        return self._parse_list_setting(self.cors_allowed_origins)


config = AppConfig()
