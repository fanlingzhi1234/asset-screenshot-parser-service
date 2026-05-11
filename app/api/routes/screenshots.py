from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.api.schemas.common import ScreenshotType, SourcePlatform
from app.api.schemas.screenshots import ScreenshotParseJsonRequest, ScreenshotParseResponse
from app.core.security import require_api_key
from app.dependencies import get_parse_service
from app.services.screenshot_service import ScreenshotParseService

router = APIRouter(dependencies=[Depends(require_api_key)])


@router.post("/screenshots/parse", response_model=ScreenshotParseResponse)
async def parse_screenshot_upload(
    file: UploadFile = File(...),
    source_platform: SourcePlatform | None = Form(default=None),
    screenshot_type_hint: ScreenshotType | None = Form(default=None),
    service: ScreenshotParseService = Depends(get_parse_service),
) -> ScreenshotParseResponse:
    image_bytes = await file.read()
    return service.parse_image_bytes(
        image_bytes=image_bytes,
        mime_type=file.content_type or "image/jpeg",
        source_platform=source_platform,
        screenshot_type_hint=screenshot_type_hint,
    )


@router.post("/screenshots/parse-json", response_model=ScreenshotParseResponse)
def parse_screenshot_json(
    request: ScreenshotParseJsonRequest,
    service: ScreenshotParseService = Depends(get_parse_service),
) -> ScreenshotParseResponse:
    return service.parse_base64(
        image_base64=request.image_base64,
        mime_type=request.mime_type,
        source_platform=request.source_platform,
        screenshot_type_hint=request.screenshot_type_hint,
    )

