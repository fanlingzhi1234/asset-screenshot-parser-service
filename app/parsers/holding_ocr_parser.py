from __future__ import annotations

import json
import re
from typing import Any

from app.api.schemas.common import ScreenshotType, SourcePlatform
from app.api.schemas.screenshots import AssetPosition, OCRPayload, SnapshotCandidate, SnapshotSummary


_THS_IGNORE_TEXTS = {
    "同花顺app",
    "中信证券",
    "买入",
    "卖出",
    "撤单",
    "持仓",
    "查询",
    "a股",
    "港股通",
    "总资产",
    "总盈亏",
    "当日参考盈亏",
    "总市值",
    "可用",
    "可取",
    "持仓股",
    "市值",
    "盈亏",
    "持仓/可用",
    "成本/现价",
    "查看已清仓股票",
    "持仓管理",
    "批量买入",
    "批量卖出",
    "止盈止损",
    "持仓资讯",
    "资产分析",
    "首页",
    "行情",
    "自选",
    "交易",
    "资讯",
    "理财",
}

_ALIPAY_IGNORE_TEXTS = {
    "基金",
    "我的持有",
    "更新时间排序",
    "全部",
    "偏股",
    "偏债",
    "指数",
    "黄金",
    "全球",
    "名称",
    "金额/昨日收益",
    "持有收益/率",
    "定投",
    "投资锦囊",
    "配置机会",
    "基金市场",
    "机会",
}

_THS_NOISE_KEYWORDS = ("首页", "行情", "自选", "交易", "资讯", "理财")
_ALIPAY_NOISE_KEYWORDS = ("投资锦囊", "配置机会", "基金市场")


def parse_holdings_from_ocr_payload(
    *,
    ocr_payload: OCRPayload | dict[str, Any],
    source_platform: SourcePlatform,
    screenshot_type: ScreenshotType | None = None,
) -> SnapshotCandidate:
    payload = ocr_payload if isinstance(ocr_payload, OCRPayload) else OCRPayload.model_validate(ocr_payload)
    lines = [_normalize_line(line.model_dump()) for line in payload.lines]
    lines = [line for line in lines if line is not None]
    if not lines:
        raise ValueError("OCR payload has no usable lines")

    if source_platform == "ths_stock":
        rows, warnings = _parse_tonghuashun(lines)
        resolved_type: ScreenshotType = screenshot_type or "ths_stock_positions_mobile_v1"
    elif source_platform == "alipay_fund":
        rows, warnings = _parse_alipay(lines)
        resolved_type = screenshot_type or "alipay_fund_positions_mobile_v1"
    else:
        raise ValueError(f"unsupported source_platform: {source_platform}")

    positions = [AssetPosition(source_platform=source_platform, **row) for row in rows]
    total_market_value = sum(item.market_value or 0.0 for item in positions) or None
    total_profit = sum(item.profit_amount or 0.0 for item in positions) or None
    return SnapshotCandidate(
        source_platform=source_platform,
        screenshot_type=resolved_type,
        summary=SnapshotSummary(
            total_market_value=total_market_value,
            total_profit=total_profit,
            position_count=len(positions),
        ),
        positions=positions,
        warnings=warnings,
    )


def _parse_tonghuashun(lines: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    warnings: list[str] = []
    width = max(line["bbox"]["x_max"] for line in lines) or 1.0
    left_threshold = width * 0.32
    anchors = [
        line for line in lines
        if line["bbox"]["x_min"] <= left_threshold
        and _looks_like_name(line["text"], ignored=_THS_IGNORE_TEXTS)
    ]
    anchors.sort(key=lambda item: item["y_center"])

    rows: list[dict[str, Any]] = []
    for index, anchor in enumerate(anchors):
        next_anchor_y = anchors[index + 1]["bbox"]["y_min"] if index + 1 < len(anchors) else None
        row_lines = _collect_row_lines(lines, anchor, next_anchor_y)
        if row_lines:
            rows.append(_build_ths_row(row_lines, warnings))

    rows = [row for row in rows if _is_valid_ths_row(row)]
    if not rows:
        raise ValueError("未能从 OCR 文本中识别同花顺持仓行")
    return rows, warnings


def _parse_alipay(lines: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    warnings: list[str] = []
    width = max(line["bbox"]["x_max"] for line in lines) or 1.0
    left_threshold = width * 0.42
    name_lines = [
        line for line in lines
        if line["bbox"]["x_min"] <= left_threshold
        and _looks_like_name(line["text"], ignored=_ALIPAY_IGNORE_TEXTS)
    ]
    name_lines.sort(key=lambda item: item["y_center"])
    name_groups = _merge_name_groups(name_lines)

    rows: list[dict[str, Any]] = []
    for index, group in enumerate(name_groups):
        next_anchor_y = name_groups[index + 1]["top_y"] if index + 1 < len(name_groups) else None
        row_lines = _collect_group_row_lines(lines, group, next_anchor_y)
        if row_lines:
            rows.append(_build_alipay_row(group, row_lines, warnings))

    rows = [row for row in rows if _is_valid_alipay_row(row)]
    if not rows:
        raise ValueError("未能从 OCR 文本中识别支付宝基金持仓行")
    return rows, warnings


def _build_ths_row(row_lines: list[dict[str, Any]], warnings: list[str]) -> dict[str, Any]:
    row_lines.sort(key=lambda item: (item["y_center"], item["x_center"]))
    width = max(line["bbox"]["x_max"] for line in row_lines) or 1.0
    name_lines = [
        line for line in row_lines
        if line["bbox"]["x_min"] <= width * 0.32 and _looks_like_name(line["text"], ignored=_THS_IGNORE_TEXTS)
    ]
    display_name = " ".join(line["text"] for line in name_lines).strip()

    numeric_left = _numeric_lines(row_lines, x_min=0.0, x_max=width * 0.35)
    market_value = _first_non_percent(numeric_left)
    profit_lines = _numeric_lines(row_lines, x_min=width * 0.32, x_max=width * 0.58)
    profit_amount = _first_non_percent(profit_lines)
    profit_pct = _first_percent(profit_lines)
    quantity_lines = _numeric_lines(row_lines, x_min=width * 0.55, x_max=width * 0.78)
    quantity = _first_non_percent(quantity_lines)
    price_lines = _numeric_lines(row_lines, x_min=width * 0.75, x_max=width * 1.05)
    cost_price, current_price = _extract_cost_and_price(price_lines)

    return {
        "display_name": display_name,
        "symbol": None,
        "asset_type": "etf" if _looks_like_etf(display_name) else "stock",
        "market": "cn",
        "quantity": quantity,
        "market_value": market_value,
        "cost_price": cost_price,
        "cost_basis_total": None,
        "profit_amount": profit_amount,
        "profit_pct": profit_pct,
        "price": current_price,
        "confidence": _derive_confidence(display_name, market_value, quantity, current_price),
        "raw_payload": json.dumps({"ocr_lines": row_lines}, ensure_ascii=False),
    }


def _build_alipay_row(
    group: dict[str, Any],
    row_lines: list[dict[str, Any]],
    warnings: list[str],
) -> dict[str, Any]:
    width = max(line["bbox"]["x_max"] for line in row_lines) or 1.0
    display_name = group["display_name"]
    center_lines = _numeric_lines(row_lines, x_min=width * 0.40, x_max=width * 0.72)
    right_lines = _numeric_lines(row_lines, x_min=width * 0.70, x_max=width * 1.05)

    market_value = _first_non_percent(center_lines)
    daily_profit = _second_non_percent(center_lines)
    profit_amount = _first_non_percent(right_lines)
    profit_pct = _first_percent(right_lines)
    return {
        "display_name": display_name,
        "symbol": None,
        "asset_type": "fund",
        "market": "fund",
        "quantity": None,
        "market_value": market_value,
        "daily_profit": daily_profit,
        "cost_basis_total": None,
        "profit_amount": profit_amount,
        "profit_pct": profit_pct,
        "price": None,
        "confidence": _derive_confidence(display_name, market_value, None, None),
        "raw_payload": json.dumps({"ocr_lines": row_lines}, ensure_ascii=False),
    }


def _collect_row_lines(
    lines: list[dict[str, Any]],
    anchor: dict[str, Any],
    next_anchor_y: float | None,
) -> list[dict[str, Any]]:
    row_top = anchor["bbox"]["y_min"] - 18.0
    row_bottom = (
        next_anchor_y - 18.0
        if next_anchor_y is not None and next_anchor_y > anchor["bbox"]["y_min"]
        else anchor["bbox"]["y_max"] + 96.0
    )
    return [line for line in lines if row_top <= line["y_center"] <= row_bottom]


def _collect_group_row_lines(
    lines: list[dict[str, Any]],
    group: dict[str, Any],
    next_anchor_y: float | None,
) -> list[dict[str, Any]]:
    row_top = group["top_y"] - 18.0
    row_bottom = (
        next_anchor_y - 20.0
        if next_anchor_y is not None and next_anchor_y > group["top_y"]
        else group["bottom_y"] + 120.0
    )
    return [line for line in lines if row_top <= line["y_center"] <= row_bottom]


def _merge_name_groups(lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    for line in lines:
        if not groups:
            groups.append(_make_group(line))
            continue
        prev = groups[-1]
        vertical_gap = line["bbox"]["y_min"] - prev["bottom_y"]
        same_row = vertical_gap <= 55.0 and abs(line["bbox"]["x_min"] - prev["x_min"]) <= 36.0
        if same_row:
            prev["lines"].append(line)
            prev["display_name"] = "".join(item["text"] for item in prev["lines"]).strip()
            prev["bottom_y"] = max(prev["bottom_y"], line["bbox"]["y_max"])
        else:
            groups.append(_make_group(line))
    return groups


def _make_group(line: dict[str, Any]) -> dict[str, Any]:
    return {
        "display_name": line["text"],
        "lines": [line],
        "top_y": line["bbox"]["y_min"],
        "bottom_y": line["bbox"]["y_max"],
        "x_min": line["bbox"]["x_min"],
    }


def _normalize_line(line: Any) -> dict[str, Any] | None:
    if not isinstance(line, dict):
        return None
    text = str(line.get("text") or "").strip()
    bbox = line.get("bbox")
    if not text or not isinstance(bbox, dict):
        return None
    try:
        x_min = float(bbox.get("x_min", 0.0))
        y_min = float(bbox.get("y_min", 0.0))
        x_max = float(bbox.get("x_max", x_min))
        y_max = float(bbox.get("y_max", y_min))
    except (TypeError, ValueError):
        return None
    return {
        "text": text,
        "score": line.get("score"),
        "bbox": {"x_min": x_min, "y_min": y_min, "x_max": x_max, "y_max": y_max},
        "poly": line.get("poly") or [],
        "x_center": (x_min + x_max) / 2.0,
        "y_center": (y_min + y_max) / 2.0,
    }


def _numeric_lines(lines: list[dict[str, Any]], *, x_min: float, x_max: float) -> list[dict[str, Any]]:
    result = []
    for line in lines:
        if x_min <= line["x_center"] <= x_max and _extract_number(line["text"]) is not None:
            result.append(line)
    result.sort(key=lambda item: (item["y_center"], item["x_center"]))
    return result


def _first_non_percent(lines: list[dict[str, Any]]) -> float | None:
    for line in lines:
        if "%" not in line["text"]:
            number = _extract_number(line["text"])
            if number is not None:
                return number
    return None


def _second_non_percent(lines: list[dict[str, Any]]) -> float | None:
    count = 0
    for line in lines:
        if "%" in line["text"]:
            continue
        number = _extract_number(line["text"])
        if number is None:
            continue
        count += 1
        if count == 2:
            return number
    return None


def _first_percent(lines: list[dict[str, Any]]) -> float | None:
    for line in lines:
        if "%" in line["text"]:
            number = _extract_number(line["text"])
            if number is not None:
                return number
    return None


def _extract_cost_and_price(lines: list[dict[str, Any]]) -> tuple[float | None, float | None]:
    numbers = [_extract_number(line["text"]) for line in lines if "%" not in line["text"]]
    numbers = [number for number in numbers if number is not None]
    if not numbers:
        return None, None
    if len(numbers) == 1:
        return numbers[0], None
    return numbers[0], numbers[1]


def _derive_confidence(
    display_name: str,
    market_value: float | None,
    quantity: float | None,
    price: float | None,
) -> str:
    score = 0
    if display_name:
        score += 1
    if market_value is not None:
        score += 1
    if quantity is not None:
        score += 1
    if price is not None:
        score += 1
    if score >= 4:
        return "high"
    if score >= 2:
        return "medium"
    return "low"


def _looks_like_name(text: str, *, ignored: set[str]) -> bool:
    normalized = text.strip().lower()
    compact = re.sub(r"\s+", "", normalized)
    ignored_compact = {re.sub(r"\s+", "", item.lower()) for item in ignored}
    if not normalized or normalized in ignored or compact in ignored_compact:
        return False
    if re.fullmatch(r"[+\-]?\d[\d,]*(?:\.\d+)?%?", text):
        return False
    if any(token in normalized for token in ("今日", "收益", "金额", "总", "仓位")):
        return False
    return bool(re.search(r"[\u4e00-\u9fffA-Za-z]", text))


def _looks_like_etf(name: str) -> bool:
    return any(keyword in (name or "").strip() for keyword in ("ETF", "指数", "恒指", "纳指"))


def _extract_number(text: str) -> float | None:
    normalized = str(text or "").replace("，", ",").replace("¥", "").replace("￥", "")
    normalized = normalized.replace("%", "").strip()
    match = re.search(r"[+\-]?\d[\d,.]*", normalized)
    if not match:
        return None
    token = _normalize_numeric_token(match.group(0))
    try:
        return float(token)
    except ValueError:
        return None


def _normalize_numeric_token(token: str) -> str:
    token = token.strip().replace(",", "")
    if not token:
        return token
    sign = ""
    if token[0] in "+-":
        sign = token[0]
        token = token[1:]
    if token.count(".") > 1:
        integer_part, decimal_part = token.rsplit(".", 1)
        token = f"{integer_part.replace('.', '')}.{decimal_part}"
    return f"{sign}{token}"


def _is_valid_ths_row(row: dict[str, Any]) -> bool:
    display_name = str(row.get("display_name") or "").strip()
    if not display_name:
        return False
    if any(keyword in display_name for keyword in _THS_NOISE_KEYWORDS):
        return False
    if row.get("market_value") is None or row.get("quantity") is None:
        return False
    return row.get("price") is not None or row.get("cost_price") is not None or row.get("profit_amount") is not None


def _is_valid_alipay_row(row: dict[str, Any]) -> bool:
    display_name = str(row.get("display_name") or "").strip()
    if not display_name:
        return False
    if any(keyword in display_name for keyword in _ALIPAY_NOISE_KEYWORDS):
        return False
    if row.get("market_value") is None:
        return False
    return row.get("profit_amount") is not None or row.get("profit_pct") is not None
