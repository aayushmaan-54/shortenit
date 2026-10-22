from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE_PATH = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    """Define the variables used in application"""

    app_name: str = "ShortenIt"
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:5174"]
    trusted_hosts: list[str] = ["localhost", "::1", "127.0.0.1"]
    forwarded_allow_ips: str = "127.0.0.1"
    redis_url: str = "redis://localhost:6379/0"
    max_body_size: int = 1_048_576  # 1 MB

    model_config = SettingsConfigDict(env_file=ENV_FILE_PATH, env_file_encoding="utf-8")


settings = Settings()
