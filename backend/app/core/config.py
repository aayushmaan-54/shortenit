from datetime import timedelta
from pathlib import Path

import pytimeparse2
from pydantic import PositiveInt, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE_PATH = Path(__file__).resolve().parents[2] / ".env"
MIN_JWT_SECRET_KEY_BYTES = 32


class Settings(BaseSettings):
    """Define the variables used in application"""

    # App
    app_name: str = "ShortenIt"
    debug: bool = False
    frontend_origin: str = "http://localhost:5173"

    # Network & Security
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:5174"]
    trusted_hosts: list[str] = ["localhost", "::1", "127.0.0.1"]
    max_body_size: int = 1_048_576  # 1 MB

    # Proxy: IPs trusted to send real client IP
    forwarded_allow_ips: str = "127.0.0.1"

    # Redis (Upstash)
    redis_url: str = "redis://localhost:6379/0"

    # Auth
    jwt_signing_keys: dict[str, str]
    jwt_algorithm: str = "HS256"
    encryption_key: str
    access_token_expires_in: int  # seconds, parsed from e.g. "15m"
    refresh_token_expires_in: int  # seconds, parsed from e.g. "7d"
    refresh_grace_period: int = 10  # seconds; multi-tab refresh window
    token_issuer: str = "ShortenIt-api"
    token_audience: str = "ShortenIt-api"
    jwt_leeway_seconds: int = 30  # 30 sec

    # OTP
    otp_secret_key: str
    otp_length: PositiveInt = 6
    otp_expires_in: int = 300  # seconds; 5 min
    otp_resend_cooldown: int = 60  # seconds; 1 resend per min
    otp_max_attempts: PositiveInt = 3  # wrong guesses before OTP is invalidated
    otp_daily_limit: PositiveInt = 5  # OTPs sent per email per day

    # DB
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_database: str = "my_database"

    # AWS
    aws_access_key: str
    aws_secret_access_key: str
    aws_default_region: str = "ap-south-1"

    # SES
    aws_ses_source_email: str

    @field_validator(
        "access_token_expires_in",
        "refresh_token_expires_in",
        "refresh_grace_period",
        "otp_expires_in",
        "otp_resend_cooldown",
        mode="before",
    )
    @classmethod
    def parse_duration(cls, val: str | float | timedelta) -> int:
        """Parse "15m"/"7d"-style strings (or raw numbers) into seconds"""
        if isinstance(val, (int, float)):
            seconds = int(val)
        elif isinstance(val, timedelta):
            seconds = int(val.total_seconds())
        else:
            parsed = pytimeparse2.parse(val)
            if parsed is None:
                raise ValueError(f"Could not parse duration string: '{val}'")
            if isinstance(parsed, timedelta):
                seconds = int(parsed.total_seconds())
            else:
                seconds = int(parsed)

        if seconds <= 0:
            raise ValueError(f"Duration must be positive, got '{val}'")

        return seconds

    @field_validator("otp_secret_key")
    @classmethod
    def validate_otp_secret_key(cls, val: str) -> str:
        """HMAC-SHA256 key should be at least as long as its 256-bit output"""
        if len(val.encode("utf-8")) < MIN_JWT_SECRET_KEY_BYTES:
            raise ValueError(
                f"OTP_SECRET_KEY must be at least {MIN_JWT_SECRET_KEY_BYTES} bytes"
            )
        return val

    @field_validator("jwt_signing_keys")
    @classmethod
    def validate_jwt_signing_keys(cls, val: dict[str, str]) -> dict[str, str]:
        """Need at least one key; HS256 needs each key at least as long as its 256-bit output"""
        if not val:
            raise ValueError("JWT_SIGNING_KEYS must have at least one key")

        for kid, key in val.items():
            if len(key.encode("utf-8")) < MIN_JWT_SECRET_KEY_BYTES:
                raise ValueError(
                    f"JWT_SIGNING_KEYS['{kid}'] must be at least {MIN_JWT_SECRET_KEY_BYTES} bytes"
                )
        return val

    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH if ENV_FILE_PATH.exists() else None,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()  # type: ignore[call-arg]
