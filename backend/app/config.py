from functools import lru_cache
from pathlib import Path
from uuid import UUID
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # =========================================================
    # APPLICATION
    # =========================================================

    app_name: str = "WorkforceOS"
    app_version: str = "0.1.0"

    app_env: str = "development"
    debug: bool = True

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    web_url: str = "http://localhost:3000"
    admin_url: str = "http://localhost:3001"

    api_base_url: str = "http://localhost:8000"
    api_v1_prefix: str = "/api/v1"

    # =========================================================
    # CORS
    # =========================================================

    cors_origins: str = (
        "http://localhost:3000,"
        "http://localhost:3001"
    )

    # =========================================================
    # POSTGRESQL
    # =========================================================

    postgres_host: str = "localhost"
    postgres_port: int = 5432

    postgres_user: str = "postgres"
    postgres_password: str = "postgres"

    control_database_name: str = "workforce_control"

    control_database_url: str = (
        "postgresql+asyncpg://"
        "postgres:postgres@localhost:5432/workforce_control"
    )

    postgres_admin_url: str = (
        "postgresql+asyncpg://"
        "postgres:postgres@localhost:5432/postgres"
    )

    # =========================================================
    # TENANT DATABASE
    # =========================================================

    tenant_database_prefix: str = "tenant_"

    tenant_database_pool_size: int = 5
    tenant_database_max_overflow: int = 10
    tenant_database_pool_timeout: int = 30

    tenant_auto_provision: bool = False

    # =========================================================
    # REDIS
    # =========================================================

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    redis_url: str = "redis://localhost:6379/0"

    redis_key_prefix: str = "workforceos:"

    # =========================================================
    # JWT / AUTHENTICATION
    # =========================================================

    jwt_secret: str = "CHANGE_THIS_TO_A_LONG_RANDOM_SECRET"

    jwt_algorithm: str = "HS256"

    access_token_minutes: int = 30
    refresh_token_days: int = 30

    email_verification_otp_minutes: int = 10
    password_reset_otp_minutes: int = 10

    otp_length: int = 6
    otp_max_attempts: int = 5

    # =========================================================
    # PASSWORD POLICY
    # =========================================================

    password_min_length: int = 8

    password_require_letter: bool = True
    password_require_number: bool = True
    password_require_special: bool = False

    # =========================================================
    # GOOGLE OAUTH
    # =========================================================

    google_client_id: str = ""
    google_client_secret: str = ""

    google_redirect_uri: str = (
        "http://localhost:8000/"
        "api/v1/auth/google/callback"
    )

    # =========================================================
    # GITHUB OAUTH
    # =========================================================

    github_client_id: str = ""
    github_client_secret: str = ""

    github_redirect_uri: str = (
        "http://localhost:8000/"
        "api/v1/auth/github/callback"
    )

    # =========================================================
    # SMTP / EMAIL
    # =========================================================

    smtp_host: str = ""
    smtp_port: int = 587

    smtp_username: str = ""
    smtp_password: str = ""

    smtp_from_email: str = "noreply@workforceos.local"
    smtp_from_name: str = "WorkforceOS"

    smtp_use_tls: bool = True

    email_enabled: bool = False

    # =========================================================
    # OBJECT STORAGE
    # =========================================================

    s3_endpoint: str = "http://localhost:9000"

    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"

    s3_bucket: str = "workforce-os"
    s3_region: str = "us-east-1"

    s3_use_ssl: bool = False

    s3_presigned_url_expiry_seconds: int = 900

    # =========================================================
    # FILE UPLOAD
    # =========================================================

    max_upload_size_mb: int = 100

    allowed_document_extensions: str = (
        "pdf,doc,docx,xls,xlsx,csv,txt"
    )

    allowed_image_extensions: str = (
        "jpg,jpeg,png,webp"
    )

    # =========================================================
    # BILLING
    # =========================================================

    payment_provider: str = "stripe"

    billing_unlimited_user_ids: list[UUID] = Field(default_factory=list)

    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    stripe_webhook_secret: str = ""

    stripe_price_starter_month: str = ""
    stripe_price_starter_year: str = ""
    stripe_price_professional_month: str = ""
    stripe_price_professional_year: str = ""
    stripe_price_business_month: str = ""
    stripe_price_business_year: str = ""
    billing_advanced_device_limit: int | None = Field(default=None, gt=0)
    billing_advanced_retention_days: int | None = Field(default=None, gt=0)
    billing_logo_url: str = ""
    billing_seller_name: str = "WorkforceOS"
    billing_seller_address: list[str] = []
    billing_tax_id: str = ""

    # =========================================================
    # AI
    # =========================================================

    openai_api_key: str = ""

    ai_enabled: bool = False
    ai_default_model: str = ""

    # =========================================================
    # WEBSOCKET
    # =========================================================

    websocket_enabled: bool = True
    websocket_heartbeat_seconds: int = 30

    # =========================================================
    # LIVEKIT
    # =========================================================

    livekit_url: str = "ws://localhost:7880"

    livekit_api_key: str = "devkey"
    livekit_api_secret: str = "secret"

    livekit_enabled: bool = False

    # =========================================================
    # TURN
    # =========================================================

    turn_server_url: str = "turn:localhost:3478"

    turn_username: str = "workforce"
    turn_password: str = "change-me"

    # =========================================================
    # MONITORING
    # =========================================================

    monitoring_enabled: bool = True

    monitoring_require_disclosure: bool = True

    monitoring_default_work_hours_only: bool = True

    monitoring_default_idle_threshold_seconds: int = 300

    monitoring_default_heartbeat_seconds: int = 15

    monitoring_default_screenshot_enabled: bool = False

    monitoring_default_screenshot_interval_seconds: int = 300

    # =========================================================
    # PAYROLL DEFAULTS
    # =========================================================

    default_payroll_currency: str = "PKR"

    default_shift_hours_per_day: int = 8

    default_late_grace_minutes: int = 0

    default_overtime_multiplier: float = 1.5

    # =========================================================
    # ATTENDANCE DEFAULTS
    # =========================================================

    default_attendance_mode: str = "hybrid"

    default_work_week: str = "MON,TUE,WED,THU,FRI"

    default_idle_threshold_seconds: int = 300

    # =========================================================
    # LOGGING
    # =========================================================

    log_level: str = "INFO"

    log_format: str = "text"

    log_include_request_id: bool = True

    # =========================================================
    # SECURITY / RATE LIMITING
    # =========================================================

    rate_limit_enabled: bool = True

    rate_limit_default_requests: int = 100

    rate_limit_default_window_seconds: int = 60

    trust_proxy_headers: bool = False

    # =========================================================
    # PLATFORM
    # =========================================================

    platform_name: str = "WorkforceOS"

    platform_support_email: str = (
        "support@workforceos.local"
    )

    platform_default_timezone: str = "UTC"

    platform_default_locale: str = "en-US"

    # =========================================================
    # DEVELOPMENT
    # =========================================================

    dev_create_default_admin: bool = False

    dev_default_admin_email: str = ""

    dev_default_admin_password: str = ""

    # =========================================================
    # PYDANTIC SETTINGS
    # =========================================================

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # =========================================================
    # VALIDATORS
    # =========================================================

    @field_validator("app_env")
    @classmethod
    def validate_app_env(cls, value: str) -> str:
        allowed = {
            "development",
            "test",
            "staging",
            "production",
        }

        normalized = value.lower().strip()

        if normalized not in allowed:
            raise ValueError(
                f"APP_ENV must be one of: {', '.join(sorted(allowed))}"
            )

        return normalized

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        allowed = {
            "DEBUG",
            "INFO",
            "WARNING",
            "ERROR",
            "CRITICAL",
        }

        normalized = value.upper().strip()

        if normalized not in allowed:
            raise ValueError(
                f"LOG_LEVEL must be one of: {', '.join(sorted(allowed))}"
            )

        return normalized

    @field_validator("api_v1_prefix")
    @classmethod
    def validate_api_prefix(cls, value: str) -> str:
        value = value.strip()

        if not value.startswith("/"):
            value = f"/{value}"

        return value.rstrip("/")

    @field_validator("tenant_database_prefix")
    @classmethod
    def validate_tenant_database_prefix(
        cls,
        value: str,
    ) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "TENANT_DATABASE_PREFIX cannot be empty"
            )

        return value

    @field_validator("otp_length")
    @classmethod
    def validate_otp_length(cls, value: int) -> int:
        if value < 4 or value > 10:
            raise ValueError(
                "OTP_LENGTH must be between 4 and 10"
            )

        return value

    @field_validator(
        "access_token_minutes",
        "refresh_token_days",
        "email_verification_otp_minutes",
        "password_reset_otp_minutes",
        "redis_port",
        "postgres_port",
        "api_port",
    )
    @classmethod
    def validate_positive_integer(
        cls,
        value: int,
    ) -> int:
        if value <= 0:
            raise ValueError(
                "Configuration value must be greater than 0"
            )

        return value

    # =========================================================
    # HELPERS
    # =========================================================

    @property
    def cors_origins_list(self) -> List[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]

    @property
    def allowed_document_extensions_list(
        self,
    ) -> List[str]:
        return [
            extension.strip().lower()
            for extension
            in self.allowed_document_extensions.split(",")
            if extension.strip()
        ]

    @property
    def allowed_image_extensions_list(
        self,
    ) -> List[str]:
        return [
            extension.strip().lower()
            for extension
            in self.allowed_image_extensions.split(",")
            if extension.strip()
        ]

    @property
    def default_work_week_list(
        self,
    ) -> List[str]:
        return [
            day.strip().upper()
            for day in self.default_work_week.split(",")
            if day.strip()
        ]

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_test(self) -> bool:
        return self.app_env == "test"

    @property
    def is_staging(self) -> bool:
        return self.app_env == "staging"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
