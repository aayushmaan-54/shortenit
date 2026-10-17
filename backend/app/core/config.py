from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE_PATH = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    """Define the variables used in application"""

    app_name: str = "ShortenIt"
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:5174"]
    trusted_hosts: list[str] = ["localhost", "::1", "127.0.0.1"]

    model_config = SettingsConfigDict(env_file=ENV_FILE_PATH, env_file_encoding="utf-8")


settings = Settings()
