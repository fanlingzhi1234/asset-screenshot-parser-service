from __future__ import annotations

from app.api.schemas.common import ScreenshotType, SourcePlatform
from app.api.schemas.screenshots import OCRPayload, SnapshotCandidate
from app.parsers.holding_ocr_parser import parse_holdings_from_ocr_payload


def classify_screenshot_type(
    *,
    ocr_payload: OCRPayload,
    source_platform: SourcePlatform | None,
    screenshot_type_hint: ScreenshotType | None,
) -> tuple[SourcePlatform, ScreenshotType, str]:
    if screenshot_type_hint:
        if screenshot_type_hint == "ths_stock_positions_mobile_v1":
            return "ths_stock", screenshot_type_hint, "high"
        if screenshot_type_hint == "alipay_fund_positions_mobile_v1":
            return "alipay_fund", screenshot_type_hint, "high"

    if source_platform == "ths_stock":
        return "ths_stock", "ths_stock_positions_mobile_v1", "high"
    if source_platform == "alipay_fund":
        return "alipay_fund", "alipay_fund_positions_mobile_v1", "high"

    full_text = ocr_payload.full_text
    if "同花顺" in full_text or "持仓股" in full_text or "成本/现价" in full_text:
        return "ths_stock", "ths_stock_positions_mobile_v1", "medium"
    if "支付宝" in full_text or "我的持有" in full_text or "金额/昨日收益" in full_text:
        return "alipay_fund", "alipay_fund_positions_mobile_v1", "medium"

    raise ValueError("无法识别截图类型，请传入 source_platform 或 screenshot_type_hint")


def parse_snapshot(
    *,
    ocr_payload: OCRPayload,
    source_platform: SourcePlatform,
    screenshot_type: ScreenshotType,
) -> SnapshotCandidate:
    return parse_holdings_from_ocr_payload(
        ocr_payload=ocr_payload,
        source_platform=source_platform,
        screenshot_type=screenshot_type,
    )

