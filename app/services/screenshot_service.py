from __future__ import annotations

import base64
from uuid import uuid4

from app.api.schemas.common import HoldingConfidence, ScreenshotType, SourcePlatform
from app.api.schemas.screenshots import OCRPayload, ScreenshotParseResponse
from app.parsers.registry import classify_screenshot_type, parse_snapshot
from app.providers.ocr.base import OCRProvider
from app.repositories.sqlite_repo import SQLiteRepository


class ScreenshotParseService:
    def __init__(self, ocr_provider: OCRProvider, repository: SQLiteRepository) -> None:
        self.ocr_provider = ocr_provider
        self.repository = repository

    def parse_image_bytes(
        self,
        *,
        image_bytes: bytes,
        mime_type: str,
        source_platform: SourcePlatform | None = None,
        screenshot_type_hint: ScreenshotType | None = None,
    ) -> ScreenshotParseResponse:
        request_id = str(uuid4())
        ocr_payload = self.ocr_provider.recognize(image_bytes=image_bytes, mime_type=mime_type)
        if ocr_payload.provider == "mock" and not ocr_payload.lines and source_platform:
            ocr_payload = self._mock_payload_for_platform(source_platform)
        resolved_platform, screenshot_type, classification = classify_screenshot_type(
            ocr_payload=ocr_payload,
            source_platform=source_platform,
            screenshot_type_hint=screenshot_type_hint,
        )
        snapshot_candidate = parse_snapshot(
            ocr_payload=ocr_payload,
            source_platform=resolved_platform,
            screenshot_type=screenshot_type,
        )
        response = ScreenshotParseResponse(
            request_id=request_id,
            ocr_provider=ocr_payload.provider,
            screenshot_type=screenshot_type,
            template_id=self._default_template_id(screenshot_type),
            template_version="v1",
            classification_confidence=classification if classification in ("high", "medium", "low") else "medium",
            warnings=snapshot_candidate.warnings,
            ocr=ocr_payload,
            snapshot_candidate=snapshot_candidate,
        )
        self.repository.create_snapshot(response.model_dump(mode="json"))
        return response

    def parse_base64(
        self,
        *,
        image_base64: str,
        mime_type: str,
        source_platform: SourcePlatform | None = None,
        screenshot_type_hint: ScreenshotType | None = None,
    ) -> ScreenshotParseResponse:
        return self.parse_image_bytes(
            image_bytes=base64.b64decode(image_base64),
            mime_type=mime_type,
            source_platform=source_platform,
            screenshot_type_hint=screenshot_type_hint,
        )

    @staticmethod
    def _default_template_id(screenshot_type: ScreenshotType) -> str:
        return f"{screenshot_type}:default"

    @staticmethod
    def _mock_payload_for_platform(source_platform: SourcePlatform) -> OCRPayload:
        if source_platform == "alipay_fund":
            return OCRPayload(
                provider="mock",
                model="fixture",
                lines=[
                    {"text": "工银瑞信新能源汽车主", "bbox": {"x_min": 56, "y_min": 708, "x_max": 250, "y_max": 740}},
                    {"text": "题混合A", "bbox": {"x_min": 58, "y_min": 748, "x_max": 150, "y_max": 776}},
                    {"text": "31,618.92", "bbox": {"x_min": 474, "y_min": 708, "x_max": 610, "y_max": 740}},
                    {"text": "0.00", "bbox": {"x_min": 518, "y_min": 754, "x_max": 580, "y_max": 778}},
                    {"text": "+8,397.06", "bbox": {"x_min": 744, "y_min": 708, "x_max": 888, "y_max": 740}},
                    {"text": "+36.16%", "bbox": {"x_min": 764, "y_min": 754, "x_max": 870, "y_max": 778}},
                ],
            )
        return OCRPayload(
            provider="mock",
            model="fixture",
            lines=[
                {"text": "航天发展", "bbox": {"x_min": 48, "y_min": 360, "x_max": 160, "y_max": 392}},
                {"text": "8,376.00", "bbox": {"x_min": 52, "y_min": 412, "x_max": 150, "y_max": 438}},
                {"text": "-3,338.19", "bbox": {"x_min": 286, "y_min": 364, "x_max": 408, "y_max": 392}},
                {"text": "-28.440%", "bbox": {"x_min": 292, "y_min": 412, "x_max": 404, "y_max": 438}},
                {"text": "300", "bbox": {"x_min": 520, "y_min": 366, "x_max": 580, "y_max": 392}},
                {"text": "39.017", "bbox": {"x_min": 742, "y_min": 366, "x_max": 822, "y_max": 392}},
                {"text": "27.920", "bbox": {"x_min": 742, "y_min": 412, "x_max": 822, "y_max": 438}},
            ],
        )
