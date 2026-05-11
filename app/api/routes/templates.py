from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.schemas.templates import TemplateItem, TemplateUpsert
from app.core.security import require_api_key
from app.dependencies import get_repository
from app.repositories.sqlite_repo import SQLiteRepository

router = APIRouter(dependencies=[Depends(require_api_key)])


@router.get("/templates", response_model=list[TemplateItem])
def list_templates(repo: SQLiteRepository = Depends(get_repository)) -> list[dict]:
    return repo.list_templates()


@router.post("/templates", response_model=TemplateItem)
def upsert_template(template: TemplateUpsert, repo: SQLiteRepository = Depends(get_repository)) -> dict:
    return repo.upsert_template(template.model_dump(mode="json"))

