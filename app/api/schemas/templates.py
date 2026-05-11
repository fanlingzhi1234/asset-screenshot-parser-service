from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from app.api.schemas.common import ScreenshotType, SourcePlatform


TemplateStatus = Literal["draft", "active", "archived"]
CaseStatus = Literal["draft", "verified", "failed", "deprecated"]


class TemplateUpsert(BaseModel):
    template_id: str
    screenshot_type: ScreenshotType
    source_platform: SourcePlatform
    layout_version: str = "v1"
    status: TemplateStatus = "draft"
    field_schema: dict[str, Any] = Field(default_factory=dict)
    parser_rules: dict[str, Any] = Field(default_factory=dict)
    normalization_rules: dict[str, Any] = Field(default_factory=dict)
    notes: str | None = None


class TemplateItem(TemplateUpsert):
    created_at: str
    updated_at: str


class CaseUpsert(BaseModel):
    case_id: str
    screenshot_type: ScreenshotType
    source_platform: SourcePlatform
    template_id: str | None = None
    image_uri: str | None = None
    ocr_raw_payload: dict[str, Any] = Field(default_factory=dict)
    expected_snapshot: dict[str, Any] = Field(default_factory=dict)
    actual_snapshot: dict[str, Any] = Field(default_factory=dict)
    status: CaseStatus = "draft"
    review_notes: str | None = None


class CaseItem(CaseUpsert):
    created_at: str
    updated_at: str

