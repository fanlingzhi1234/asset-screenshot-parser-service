# Tencent Cloud Deployment

## Target

Deploy `asset-screenshot-parser-service` as a small Docker service on a Tencent Cloud CVM.

## Recommended Runtime

- 2 vCPU / 4 GB RAM minimum.
- Ubuntu 22.04 LTS.
- Docker and Docker Compose plugin installed.
- Inbound access restricted to the upstream apps or a private reverse proxy.
- Public API should set `API_KEY`.

## Steps

1. Build and validate locally.

```bash
python -m pytest
python -m compileall app tests
docker build -t asset-screenshot-parser-service:local .
```

2. Prepare server directory.

```bash
sudo mkdir -p /opt/asset-screenshot-parser-service/data
sudo chown -R "$USER":"$USER" /opt/asset-screenshot-parser-service
```

3. Sync files to server.

```bash
rsync -az --delete ./ <user>@<host>:/opt/asset-screenshot-parser-service/
```

4. Create `.env` on server from `.env.example`.

Required production values:

- `APP_ENV=production`
- `DATABASE_URL=sqlite:///./data/parser.db`
- `PYTHON_IMAGE=mirror.gcr.io/library/python:3.11-slim`
- `OCR_PROVIDER=umi_http`
- `UMI_OCR_BASE_URL=http://<umi-ocr-host>:1224`
- `API_KEY=<strong-random-key>`

5. Deploy.

```bash
cd /opt/asset-screenshot-parser-service
scripts/deploy-production.sh
curl -H "X-API-Key: <key>" http://127.0.0.1:8010/api/v1/health
```

The deploy script pulls `main`, validates the release guard, validates Docker Compose, rebuilds the `parser` service, and checks health.

```bash
bash scripts/guard-production-release.sh
```

## Rollback

Keep the previous Docker image tag or previous git commit on the server.

```bash
docker stop asset-screenshot-parser-service
docker rm asset-screenshot-parser-service
git checkout <previous_commit>
bash scripts/deploy-production.sh
```

## Current Caveat

This repository only wraps Umi-OCR. Umi-OCR itself must already be running on the same CVM or another reachable host.

If Umi-OCR is not ready yet, use `OCR_PROVIDER=mock` only for local contract testing. Do not use the mock provider for production.
