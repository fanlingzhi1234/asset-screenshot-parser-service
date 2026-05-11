from __future__ import annotations

from app.core.config import Settings, get_settings
from app.providers.ocr.base import OCRProvider
from app.providers.ocr.mock import MockOCRProvider
from app.providers.ocr.umi_cli import UmiCLIProvider
from app.providers.ocr.umi_http import UmiHTTPProvider


def create_ocr_provider(settings: Settings | None = None) -> OCRProvider:
    settings = settings or get_settings()
    provider = settings.ocr_provider.lower().strip()
    if provider == "umi_http":
        return UmiHTTPProvider(settings.umi_ocr_base_url, settings.ocr_timeout_seconds)
    if provider == "umi_cli":
        return UmiCLIProvider(settings.umi_ocr_cli_path, settings.ocr_timeout_seconds)
    if provider == "mock":
        return MockOCRProvider()
    raise ValueError(f"unsupported OCR_PROVIDER: {settings.ocr_provider}")

