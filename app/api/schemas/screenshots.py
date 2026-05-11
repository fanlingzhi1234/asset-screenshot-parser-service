from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.api.schemas.common import (
    AssetType,
    HoldingConfidence,
    HoldingMarket,
    ScreenshotType,
    SourcePlatform,
)


class OCRLine(BaseModel):
    text: str
    score: float | None = None
    bbox: dict[str, float]
    poly: list[list[float]] = Field(default_factory=list)


class OCRPayload(BaseModel):
    provider: str
    model: str | None = None
    full_text: str = ""
    lines: list[OCRLine] = Field(default_factory=list)
    raw_result: dict[str, Any] = Field(default_factory=dict)


class AssetPosition(BaseModel):
    asset_type: AssetType
    source_platform: SourcePlatform
    display_name: str
    symbol: str | None = None
    market: HoldingMarket = "cn"
    quantity: float | None = None
    market_value: float | None = None
    cost_price: float | None = None
    cost_basis_total: float | None = None
    daily_profit: float | None = None
    profit_amount: float | None = None
    profit_pct: float | None = None
    position_weight: float | None = None
    price: float | None = None
    confidence: HoldingConfidence = "medium"
    raw_payload: str | None = None


class SnapshotSummary(BaseModel):
    total_market_value: float | None = None
    total_profit: float | None = None
    position_count: int = 0
    currency: str = "CNY"


class SnapshotCandidate(BaseModel):
    source_platform: SourcePlatform
    screenshot_type: ScreenshotType
    summary: SnapshotSummary
    positions: list[AssetPosition] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ScreenshotParseJsonRequest(BaseModel):
    image_base64: str = Field(..., min_length=1)
    mime_type: str = "image/jpeg"
    source_platform: SourcePlatform | None = None
    screenshot_type_hint: ScreenshotType | None = None
    review_mode: bool = True


class ScreenshotParseResponse(BaseModel):
    request_id: str
    ocr_provider: str
    screenshot_type: ScreenshotType
    template_id: str | None = None
    template_version: str | None = None
    classification_confidence: HoldingConfidence
    warnings: list[str] = Field(default_factory=list)
    ocr: OCRPayload
    snapshot_candidate: SnapshotCandidate

