# Release Process

This document describes the standard release flow for `asset-screenshot-parser-service`.

## Branch Rule

- Production releases come from `main`.
- Feature work should land through a feature branch or a reviewed local changeset before merging into `main`.
- Do not publish from a dirty working tree.

## Local Gate

Run before every release:

```bash
python -m pytest
python -m compileall app tests
docker build -t asset-screenshot-parser-service:local .
```

If Docker Hub is slow or blocked, keep the default mirror image:

```env
PYTHON_IMAGE=mirror.gcr.io/library/python:3.11-slim
```

## CI Gate

Pushing to `main` triggers GitHub Actions:

- Python dependency installation.
- Unit tests.
- Python compile check.
- Docker image build.

CI must be green before cloud deployment.

## Commit Message

Recommended initial release commit:

```text
feat: bootstrap asset screenshot parser service
```

Do not add `Co-Authored-By`.

## Tagging

For the first stable release:

```bash
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0
```

Only tag after CI passes on `main`.

## Tencent Cloud Deployment

After CI passes:

```bash
rsync -az --delete ./ <user>@<host>:/opt/asset-screenshot-parser-service/
ssh <user>@<host> 'cd /opt/asset-screenshot-parser-service && bash scripts/deploy-production.sh'
```

Then verify:

```bash
curl -H "X-API-Key: <key>" http://<host>:8010/api/v1/health
```

## Rollback

Rollback is commit based:

```bash
ssh <user>@<host>
cd /opt/asset-screenshot-parser-service
git checkout <previous_commit>
bash scripts/deploy-production.sh
```

If Docker image tagging is introduced later, prefer immutable image tags for rollback.

## Release Evidence

Record the following in the release note:

- Commit SHA.
- GitHub Actions run URL.
- Local test command result.
- Docker build result.
- Cloud health check response.
- Rollback target.
