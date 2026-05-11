#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/asset-screenshot-parser-service}"
IMAGE_NAME="${IMAGE_NAME:-asset-screenshot-parser-service}"
CONTAINER_NAME="${CONTAINER_NAME:-asset-screenshot-parser-service}"
PORT="${APP_PORT:-8010}"

if [[ ! -f ".env" ]]; then
  echo "Missing .env. Create it from .env.example before deployment." >&2
  exit 1
fi

docker build -t "${IMAGE_NAME}:latest" .
docker stop "${CONTAINER_NAME}" >/dev/null 2>&1 || true
docker rm "${CONTAINER_NAME}" >/dev/null 2>&1 || true
docker run -d \
  --name "${CONTAINER_NAME}" \
  --restart unless-stopped \
  --env-file .env \
  -p "${PORT}:8010" \
  -v "${APP_DIR}/data:/app/data" \
  "${IMAGE_NAME}:latest"

echo "Deployed ${CONTAINER_NAME} on port ${PORT}"

