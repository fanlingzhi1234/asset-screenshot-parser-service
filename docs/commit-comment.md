# Commit Comment

## Commit Message

```text
feat: bootstrap asset screenshot parser service
```

## Commit Body

```text
- add FastAPI service skeleton for reusable asset screenshot parsing
- add OCR provider abstraction with Umi-OCR HTTP, Umi-OCR CLI, and mock providers
- migrate Tonghuashun stock and Alipay fund screenshot parsers
- add template, case, and snapshot persistence over SQLite
- add Docker, GitHub Actions CI, release, and Tencent Cloud deployment docs
```

## PR / Release Summary

```text
## Summary
- Bootstrap standalone asset-screenshot-parser-service.
- Provide OCR provider abstraction and initial Umi-OCR integration.
- Add parser support for Tonghuashun stock holdings and Alipay fund holdings screenshots.
- Add template/case/snapshot APIs and SQLite-backed persistence.
- Add Docker, CI, release, and Tencent Cloud deployment documentation.

## Validation
- python -m pytest
- python -m compileall app tests
- docker build -t asset-screenshot-parser-service:local .

## Rollback
- Revert this commit or redeploy the previous server commit/image.
```

