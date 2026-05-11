# API Contract

Base path: `/api/v1`

This service is an OCR-backed asset screenshot parser. It accepts screenshots,
normalizes OCR output, classifies the screenshot family, and returns a structured
asset snapshot candidate for an upstream product to review and persist.

## Authentication

`GET /health` is public.

All other endpoints require `X-API-Key` when `API_KEY` is configured on the
server. If `API_KEY` is empty, the service accepts unauthenticated requests.

```http
X-API-Key: <asset-parser-api-key>
```

## Supported Types

`source_platform`:

- `ths_stock`: Tonghuashun stock/ETF holding screenshots.
- `alipay_fund`: Alipay fund holding screenshots.

`screenshot_type`:

- `ths_stock_positions_mobile_v1`
- `alipay_fund_positions_mobile_v1`

`asset_type`:

- `stock`
- `etf`
- `fund`

`market`:

- `cn`
- `hk`
- `us`
- `fund`

`confidence`:

- `high`
- `medium`
- `low`

## Health

`GET /health`

Returns service status and selected OCR provider.

Example response:

```json
{
  "status": "ok",
  "service": "asset-screenshot-parser-service",
  "env": "production",
  "ocr_provider": "umi_http"
}
```

## Parse Screenshot Upload

`POST /screenshots/parse`

Content type: `multipart/form-data`

Fields:

- `file`: required screenshot image.
- `source_platform`: optional, `ths_stock` or `alipay_fund`.
- `screenshot_type_hint`: optional, one of the supported screenshot types.

Example:

```bash
curl -X POST "$ASSET_PARSER_BASE_URL/api/v1/screenshots/parse" \
  -H "X-API-Key: $ASSET_PARSER_API_KEY" \
  -F "file=@./examples/ths-stock.jpg" \
  -F "source_platform=ths_stock"
```

Use this endpoint when the caller can upload a file directly, such as a web app,
mobile app, or backend job reading an image from disk/object storage.

## Parse Screenshot JSON

`POST /screenshots/parse-json`

Content type: `application/json`

Request body:

```json
{
  "image_base64": "<base64-image-content>",
  "mime_type": "image/jpeg",
  "source_platform": "ths_stock",
  "screenshot_type_hint": "ths_stock_positions_mobile_v1",
  "review_mode": true
}
```

Fields:

- `image_base64`: required image bytes encoded as base64, without a data URL prefix.
- `mime_type`: optional, defaults to `image/jpeg`.
- `source_platform`: optional but recommended for deterministic parsing.
- `screenshot_type_hint`: optional layout hint.
- `review_mode`: reserved for review workflows; currently accepted for compatibility.

Use this endpoint when the caller receives images from Feishu, mobile upload
callbacks, queues, or other services where JSON payloads are easier to route.

## Parse Response

Both parse endpoints return the same response shape.

```json
{
  "request_id": "8b160efd-23d7-4f8f-a17e-52c41fc5a12f",
  "ocr_provider": "umi_http",
  "screenshot_type": "ths_stock_positions_mobile_v1",
  "template_id": "ths_stock_positions_mobile_v1:default",
  "template_version": "v1",
  "classification_confidence": "high",
  "warnings": [],
  "ocr": {
    "provider": "umi_http",
    "model": "umi-ocr",
    "full_text": "...",
    "lines": [
      {
        "text": "航天发展",
        "score": 0.997,
        "bbox": {"x_min": 48.0, "y_min": 360.0, "x_max": 160.0, "y_max": 392.0},
        "poly": [[48.0, 360.0], [160.0, 360.0], [160.0, 392.0], [48.0, 392.0]]
      }
    ],
    "raw_result": {}
  },
  "snapshot_candidate": {
    "source_platform": "ths_stock",
    "screenshot_type": "ths_stock_positions_mobile_v1",
    "summary": {
      "total_market_value": 34049.0,
      "total_profit": -8734.8,
      "position_count": 4,
      "currency": "CNY"
    },
    "positions": [
      {
        "asset_type": "stock",
        "source_platform": "ths_stock",
        "display_name": "航天发展",
        "symbol": null,
        "market": "cn",
        "quantity": 300.0,
        "market_value": 8376.0,
        "cost_price": 39.017,
        "cost_basis_total": null,
        "daily_profit": null,
        "profit_amount": -3338.19,
        "profit_pct": -28.44,
        "position_weight": null,
        "price": 27.92,
        "confidence": "high",
        "raw_payload": "{...}"
      }
    ],
    "warnings": []
  }
}
```

Important response semantics:

- `snapshot_candidate` is the normalized business result.
- `ocr` is included for debugging, review, and future parser improvements.
- `warnings` means the parser succeeded but found something worth reviewing.
- `raw_payload` is a JSON string containing OCR lines used for one parsed position.
- `symbol` can be `null`; name-to-code resolution is intentionally left to the consuming app.

## Templates

Templates describe parser/layout versions for screenshot families. They are useful
for case management and future parser evolution.

`GET /templates`

Returns all templates.

`POST /templates`

Request body:

```json
{
  "template_id": "ths_stock_positions_mobile_v1:default",
  "screenshot_type": "ths_stock_positions_mobile_v1",
  "source_platform": "ths_stock",
  "layout_version": "v1",
  "status": "active",
  "field_schema": {},
  "parser_rules": {},
  "normalization_rules": {},
  "notes": "Default Tonghuashun mobile holding parser"
}
```

`status`: `draft`, `active`, or `archived`.

## Cases

Cases store screenshot examples, expected snapshots, and actual parser output for
regression evaluation.

`GET /cases`

Returns all cases.

`POST /cases`

Request body:

```json
{
  "case_id": "ths-stock-mobile-20260511-001",
  "screenshot_type": "ths_stock_positions_mobile_v1",
  "source_platform": "ths_stock",
  "template_id": "ths_stock_positions_mobile_v1:default",
  "image_uri": "s3://asset-parser-cases/ths-stock-mobile-20260511-001.jpg",
  "ocr_raw_payload": {},
  "expected_snapshot": {},
  "actual_snapshot": {},
  "status": "verified",
  "review_notes": "Real mobile screenshot regression case"
}
```

`status`: `draft`, `verified`, `failed`, or `deprecated`.

## Error Handling

Typical errors:

- `401`: missing or invalid `X-API-Key`.
- `422`: request validation failed, such as unsupported `source_platform`.
- `500`: OCR provider failure, invalid image data, or parser failure.

Recommended caller behavior:

- Retry OCR/network failures with bounded retries.
- Do not retry validation errors automatically.
- Store the original image and response `request_id` in the consuming app for review.
- Treat parser results as a reviewable candidate when money-sensitive decisions are involved.

## Compatibility Notes

- Parse response fields should be treated as additive. Consumers should ignore
  unknown fields.
- Existing enum values are stable; new screenshot families may add new
  `source_platform` and `screenshot_type` values later.
- The service does not execute trades, log in to financial apps, or fetch account
  data directly.
