# API Contract

Base path: `/api/v1`

## Health

`GET /health`

Returns service status and selected OCR provider.

## Parse Screenshot

`POST /screenshots/parse`

Content type: `multipart/form-data`

Fields:

- `file`: screenshot image.
- `source_platform`: optional, `ths_stock` or `alipay_fund`.
- `screenshot_type_hint`: optional, `ths_stock_positions_mobile_v1` or `alipay_fund_positions_mobile_v1`.

`POST /screenshots/parse-json`

JSON body:

```json
{
  "image_base64": "...",
  "mime_type": "image/jpeg",
  "source_platform": "ths_stock",
  "screenshot_type_hint": "ths_stock_positions_mobile_v1"
}
```

Response:

```json
{
  "request_id": "...",
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
    "lines": []
  },
  "snapshot_candidate": {
    "source_platform": "ths_stock",
    "screenshot_type": "ths_stock_positions_mobile_v1",
    "summary": {},
    "positions": [],
    "warnings": []
  }
}
```

## Templates

- `GET /templates`
- `POST /templates`

Templates are versioned parser/layout definitions. First release stores them in SQLite as JSON payloads.

## Cases

- `GET /cases`
- `POST /cases`

Cases store screenshot examples, expected snapshots, and actual parser output for regression evaluation.

