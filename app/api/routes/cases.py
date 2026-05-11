from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.schemas.templates import CaseItem, CaseUpsert
from app.core.security import require_api_key
from app.dependencies import get_repository
from app.repositories.sqlite_repo import SQLiteRepository

router = APIRouter(dependencies=[Depends(require_api_key)])


@router.get("/cases", response_model=list[CaseItem])
def list_cases(repo: SQLiteRepository = Depends(get_repository)) -> list[dict]:
    return repo.list_cases()


@router.post("/cases", response_model=CaseItem)
def upsert_case(case: CaseUpsert, repo: SQLiteRepository = Depends(get_repository)) -> dict:
    return repo.upsert_case(case.model_dump(mode="json"))

