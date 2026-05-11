from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings
from app.providers.ocr.factory import create_ocr_provider
from app.repositories.sqlite_repo import SQLiteRepository
from app.services.screenshot_service import ScreenshotParseService


@lru_cache
def get_repository() -> SQLiteRepository:
    return SQLiteRepository(get_settings().database_url)


@lru_cache
def get_parse_service() -> ScreenshotParseService:
    return ScreenshotParseService(create_ocr_provider(), get_repository())

