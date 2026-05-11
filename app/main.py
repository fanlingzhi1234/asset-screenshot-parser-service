from __future__ import annotations

from fastapi import FastAPI

from app.api.routes import cases, health, screenshots, templates
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0")
    app.include_router(health.router, prefix="/api/v1", tags=["health"])
    app.include_router(screenshots.router, prefix="/api/v1", tags=["screenshots"])
    app.include_router(templates.router, prefix="/api/v1", tags=["templates"])
    app.include_router(cases.router, prefix="/api/v1", tags=["cases"])
    return app


app = create_app()
