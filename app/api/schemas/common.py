from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


SourcePlatform = Literal["ths_stock", "alipay_fund"]
ScreenshotType = Literal["ths_stock_positions_mobile_v1", "alipay_fund_positions_mobile_v1"]
AssetType = Literal["stock", "etf", "fund"]
HoldingMarket = Literal["cn", "hk", "us", "fund"]
HoldingConfidence = Literal["high", "medium", "low"]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class APIError(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)

