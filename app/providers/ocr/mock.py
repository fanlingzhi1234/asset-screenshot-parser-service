from __future__ import annotations

from app.api.schemas.screenshots import OCRPayload
from app.providers.ocr.base import OCRProvider


class MockOCRProvider(OCRProvider):
    name = "mock"

    def recognize(self, image_bytes: bytes, mime_type: str = "image/jpeg") -> OCRPayload:
        return OCRPayload(provider=self.name, model="mock", full_text="", lines=[], raw_result={})

