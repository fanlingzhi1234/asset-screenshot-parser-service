# AGENTS.md

This repository follows a small-service workflow.

- Do not hardcode secrets, user paths, ports, tokens, or cloud host addresses.
- Add new configuration keys to `.env.example` and the relevant docs.
- Keep API contract changes backwards-compatible where possible.
- Prefer small parser/provider abstractions over parallel one-off implementations.
- Do not run `git commit`, `git tag`, or `git push` unless explicitly confirmed.
- For code changes, run at least the nearest deterministic checks before delivery.
- For deployment changes, document the target pipeline, rollback path, and unverified risks.

Default validation:

```bash
python -m pytest
python -m py_compile $(find app tests -name "*.py")
```

