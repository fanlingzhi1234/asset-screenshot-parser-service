from __future__ import annotations

from app.api.schemas.screenshots import OCRPayload
from app.parsers.holding_ocr_parser import parse_holdings_from_ocr_payload


def test_parse_tonghuashun_mobile_ocr_lines() -> None:
    payload = OCRPayload(
        provider="fixture",
        lines=[
            {"text": "航天发展", "bbox": {"x_min": 48, "y_min": 360, "x_max": 160, "y_max": 392}},
            {"text": "8,376.00", "bbox": {"x_min": 52, "y_min": 412, "x_max": 150, "y_max": 438}},
            {"text": "-3,338.19", "bbox": {"x_min": 286, "y_min": 364, "x_max": 408, "y_max": 392}},
            {"text": "-28.440%", "bbox": {"x_min": 292, "y_min": 412, "x_max": 404, "y_max": 438}},
            {"text": "300", "bbox": {"x_min": 520, "y_min": 366, "x_max": 580, "y_max": 392}},
            {"text": "300", "bbox": {"x_min": 520, "y_min": 412, "x_max": 580, "y_max": 438}},
            {"text": "39.017", "bbox": {"x_min": 742, "y_min": 366, "x_max": 822, "y_max": 392}},
            {"text": "27.920", "bbox": {"x_min": 742, "y_min": 412, "x_max": 822, "y_max": 438}},
            {"text": "万向钱潮", "bbox": {"x_min": 50, "y_min": 474, "x_max": 168, "y_max": 506}},
            {"text": "12,348.00", "bbox": {"x_min": 50, "y_min": 528, "x_max": 164, "y_max": 556}},
            {"text": "-1,808.18", "bbox": {"x_min": 286, "y_min": 478, "x_max": 404, "y_max": 506}},
            {"text": "-12.699%", "bbox": {"x_min": 292, "y_min": 528, "x_max": 404, "y_max": 556}},
            {"text": "700", "bbox": {"x_min": 524, "y_min": 478, "x_max": 574, "y_max": 506}},
            {"text": "700", "bbox": {"x_min": 524, "y_min": 528, "x_max": 574, "y_max": 556}},
            {"text": "20.207", "bbox": {"x_min": 742, "y_min": 478, "x_max": 822, "y_max": 506}},
            {"text": "17.640", "bbox": {"x_min": 742, "y_min": 528, "x_max": 822, "y_max": 556}},
        ],
    )

    snapshot = parse_holdings_from_ocr_payload(ocr_payload=payload, source_platform="ths_stock")

    assert snapshot.summary.position_count == 2
    assert snapshot.positions[0].display_name == "航天发展"
    assert snapshot.positions[0].quantity == 300.0
    assert snapshot.positions[0].market_value == 8376.0
    assert snapshot.positions[0].profit_amount == -3338.19
    assert snapshot.positions[0].profit_pct == -28.44
    assert snapshot.positions[0].cost_price == 39.017
    assert snapshot.positions[0].price == 27.92
    assert snapshot.positions[1].display_name == "万向钱潮"
    assert snapshot.positions[1].quantity == 700.0
    assert snapshot.warnings == []


def test_parse_tonghuashun_filters_mobile_navigation_noise_and_repairs_number() -> None:
    payload = OCRPayload(
        provider="fixture",
        lines=[
            {"text": "中中", "bbox": {"x_min": 50, "y_min": 40, "x_max": 110, "y_max": 70}},
            {"text": "万向钱潮", "bbox": {"x_min": 50, "y_min": 474, "x_max": 168, "y_max": 506}},
            {"text": "12,348.00", "bbox": {"x_min": 50, "y_min": 528, "x_max": 164, "y_max": 556}},
            {"text": "-1.808.18", "bbox": {"x_min": 286, "y_min": 478, "x_max": 404, "y_max": 506}},
            {"text": "-12.699%", "bbox": {"x_min": 292, "y_min": 528, "x_max": 404, "y_max": 556}},
            {"text": "700", "bbox": {"x_min": 524, "y_min": 478, "x_max": 574, "y_max": 506}},
            {"text": "700", "bbox": {"x_min": 524, "y_min": 528, "x_max": 574, "y_max": 556}},
            {"text": "20.207", "bbox": {"x_min": 742, "y_min": 478, "x_max": 822, "y_max": 506}},
            {"text": "17.640", "bbox": {"x_min": 742, "y_min": 528, "x_max": 822, "y_max": 556}},
            {"text": "首页 行情", "bbox": {"x_min": 46, "y_min": 1650, "x_max": 210, "y_max": 1690}},
            {"text": "自选 交易 资讯 理财", "bbox": {"x_min": 260, "y_min": 1650, "x_max": 820, "y_max": 1690}},
        ],
    )

    snapshot = parse_holdings_from_ocr_payload(ocr_payload=payload, source_platform="ths_stock")

    assert snapshot.summary.position_count == 1
    assert snapshot.positions[0].display_name == "万向钱潮"
    assert snapshot.positions[0].profit_amount == -1808.18
    assert snapshot.warnings == []


def test_parse_alipay_mobile_ocr_lines() -> None:
    payload = OCRPayload(
        provider="fixture",
        lines=[
            {"text": "工银瑞信新能源汽车主", "bbox": {"x_min": 56, "y_min": 708, "x_max": 250, "y_max": 740}},
            {"text": "题混合A", "bbox": {"x_min": 58, "y_min": 748, "x_max": 150, "y_max": 776}},
            {"text": "31,618.92", "bbox": {"x_min": 474, "y_min": 708, "x_max": 610, "y_max": 740}},
            {"text": "0.00", "bbox": {"x_min": 518, "y_min": 754, "x_max": 580, "y_max": 778}},
            {"text": "+8,397.06", "bbox": {"x_min": 744, "y_min": 708, "x_max": 888, "y_max": 740}},
            {"text": "+36.16%", "bbox": {"x_min": 764, "y_min": 754, "x_max": 870, "y_max": 778}},
            {"text": "汇添富恒生指数(QDII-", "bbox": {"x_min": 56, "y_min": 1038, "x_max": 298, "y_max": 1072}},
            {"text": "LOF)C", "bbox": {"x_min": 56, "y_min": 1078, "x_max": 124, "y_max": 1106}},
            {"text": "3,635.16", "bbox": {"x_min": 492, "y_min": 1042, "x_max": 602, "y_max": 1070}},
            {"text": "0.00", "bbox": {"x_min": 518, "y_min": 1086, "x_max": 580, "y_max": 1108}},
            {"text": "+635.16", "bbox": {"x_min": 770, "y_min": 1042, "x_max": 860, "y_max": 1070}},
            {"text": "+21.17%", "bbox": {"x_min": 760, "y_min": 1086, "x_max": 864, "y_max": 1110}},
        ],
    )

    snapshot = parse_holdings_from_ocr_payload(ocr_payload=payload, source_platform="alipay_fund")

    assert snapshot.summary.position_count == 2
    assert snapshot.positions[0].display_name == "工银瑞信新能源汽车主题混合A"
    assert snapshot.positions[0].market_value == 31618.92
    assert snapshot.positions[0].daily_profit == 0.0
    assert snapshot.positions[0].profit_amount == 8397.06
    assert snapshot.positions[0].profit_pct == 36.16
    assert snapshot.positions[1].display_name == "汇添富恒生指数(QDII-LOF)C"
    assert snapshot.positions[1].market_value == 3635.16
    assert snapshot.positions[1].profit_amount == 635.16
    assert snapshot.warnings == []


def test_parse_alipay_filters_marketing_and_navigation_noise() -> None:
    payload = OCRPayload(
        provider="fixture",
        lines=[
            {"text": "AI迭代机会", "bbox": {"x_min": 60, "y_min": 220, "x_max": 250, "y_max": 260}},
            {"text": "我的持有吕", "bbox": {"x_min": 56, "y_min": 390, "x_max": 190, "y_max": 430}},
            {"text": "投资锦囊乘风A/变革，投资美股，近3年同类第2", "bbox": {"x_min": 132, "y_min": 1408, "x_max": 850, "y_max": 1450}},
            {"text": "3", "bbox": {"x_min": 584, "y_min": 1408, "x_max": 596, "y_max": 1450}},
            {"text": "配置机会", "bbox": {"x_min": 58, "y_min": 1780, "x_max": 174, "y_max": 1820}},
            {"text": "基金市场", "bbox": {"x_min": 100, "y_min": 1900, "x_max": 190, "y_max": 1940}},
            {"text": "机会", "bbox": {"x_min": 330, "y_min": 1900, "x_max": 390, "y_max": 1940}},
            {"text": "中欧中证A50指数A", "bbox": {"x_min": 56, "y_min": 1584, "x_max": 278, "y_max": 1622}},
            {"text": "23,263.39", "bbox": {"x_min": 488, "y_min": 1584, "x_max": 626, "y_max": 1622}},
            {"text": "0.00", "bbox": {"x_min": 528, "y_min": 1636, "x_max": 590, "y_max": 1662}},
            {"text": "+3,504.59", "bbox": {"x_min": 748, "y_min": 1584, "x_max": 878, "y_max": 1622}},
            {"text": "+17.52%", "bbox": {"x_min": 772, "y_min": 1636, "x_max": 874, "y_max": 1662}},
        ],
    )

    snapshot = parse_holdings_from_ocr_payload(ocr_payload=payload, source_platform="alipay_fund")

    assert snapshot.summary.position_count == 1
    assert snapshot.positions[0].display_name == "中欧中证A50指数A"
    assert snapshot.positions[0].market_value == 23263.39
    assert snapshot.positions[0].profit_amount == 3504.59
    assert snapshot.positions[0].profit_pct == 17.52
    assert snapshot.warnings == []
