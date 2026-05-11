from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "asset-screenshot-parser-service"
    app_env: str = "local"
    app_host: str = "0.0.0.0"
    app_port: int = 8010
    log_level: str = "INFO"

    database_url: str = "sqlite:///./data/parser.db"
    upload_dir: Path = Path("./data/uploads")

    ocr_provider: str = "umi_http"
    ocr_timeout_seconds: int = 30
    umi_ocr_base_url: str = "http://127.0.0.1:1224"
    umi_ocr_cli_path: str = "umi-ocr"

    api_key: Optional[str] = Field(default=None)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()

