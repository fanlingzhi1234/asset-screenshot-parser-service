# Asset Screenshot Parser Service

Reusable OCR-backed service for parsing personal, family, and investment asset screenshots.

This repository owns screenshot OCR integration, screenshot-type classification, parser templates, parser cases, and structured asset snapshot extraction. Upstream apps such as `daily_stock_analysis` should call this service over HTTP instead of embedding OCR or screenshot-specific parsing rules.

## What It Does

- Receives mobile asset screenshots through a stable HTTP API.
- Calls an OCR provider, defaulting to Umi-OCR HTTP.
- Normalizes OCR text lines into a stable internal payload.
- Classifies screenshot type when possible.
- Parses supported screenshot families into structured asset positions.
- Stores templates, cases, and parsed snapshots for review workflows.

Initial screenshot types:

- `ths_stock_positions_mobile_v1`
- `alipay_fund_positions_mobile_v1`

## Architecture

```text
Client / Upstream App
  -> FastAPI gateway
  -> OCR provider abstraction
      -> Umi-OCR HTTP
      -> Umi-OCR CLI
      -> mock provider for local tests
  -> screenshot classifier
  -> parser registry
  -> template / case / snapshot repository
  -> structured asset snapshot response
```

## API

Base path: `/api/v1`

Main endpoints:

- `GET /health`
- `POST /screenshots/parse`
- `POST /screenshots/parse-json`
- `GET /templates`
- `POST /templates`
- `GET /cases`
- `POST /cases`

See [API Contract](docs/api-contract.md) for the endpoint contract and
[Integration Guide](docs/integration-guide.zh-CN.md) for consumer-side examples.

## Quick Start

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8010
```

Health check:

```bash
curl http://localhost:8010/api/v1/health
```

Parse one screenshot:

```bash
curl -F "file=@/path/to/screenshot.jpg" \
  -F "source_platform=ths_stock" \
  http://localhost:8010/api/v1/screenshots/parse
```

## Umi-OCR

Set `OCR_PROVIDER=umi_http` and `UMI_OCR_BASE_URL=http://127.0.0.1:1224`.

For parser-only development and tests, set `OCR_PROVIDER=mock`.

## Configuration

Core environment variables:

- `APP_ENV`: `local`, `staging`, or `production`.
- `APP_PORT`: service port, default `8010`.
- `DATABASE_URL`: SQLite URL, default `sqlite:///./data/parser.db`.
- `OCR_PROVIDER`: `umi_http`, `umi_cli`, or `mock`.
- `UMI_OCR_BASE_URL`: Umi-OCR HTTP base URL.
- `API_KEY`: optional API key. If set, clients must send `X-API-Key`.

See [.env.example](.env.example) for the complete list.

## Development

```bash
python -m pytest
python -m compileall app tests
```

Docker smoke:

```bash
docker build -t asset-screenshot-parser-service:local .
docker compose up --build
```

## Release

Release and Tencent Cloud deployment steps are documented in [Release Process](docs/release-process.md) and [Tencent Cloud Deployment](docs/tencent-cloud-deploy.md).

Suggested commit and PR text are maintained in [Commit Comment](docs/commit-comment.md).
