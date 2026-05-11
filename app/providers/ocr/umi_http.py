from __future__ import annotations

import base64
from typing import Any

import requests

from app.api.schemas.screenshots import OCRLine, OCRPayload
from app.providers.ocr.base import OCRProvider, OCRProviderError, bbox_from_poly


class UmiHTTPProvider(OCRProvider):
    name = "umi_http"

    def __init__(self, base_url: str, timeout_seconds: int = 30) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def recognize(self, image_bytes: bytes, mime_type: str = "image/jpeg") -> OCRPayload:
        encoded = base64.b64encode(image_bytes).decode("ascii")
        response = requests.post(
            f"{self.base_url}/api/ocr",
            json={"base64": encoded, "options": {}},
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        body = response.json()
        if body.get("code") != 100:
            raise OCRProviderError(f"Umi-OCR failed: {body.get('message') or body.get('data') or body}")
        return self._normalize_response(body)

    def _normalize_response(self, body: dict[str, Any]) -> OCRPayload:
        raw_items = body.get("data")
        if not isinstance(raw_items, list):
            raise OCRProviderError("Umi-OCR response data is not a list")

        lines: list[OCRLine] = []
        for item in raw_items:
            if not isinstance(item, dict) or item.get("end") is True:
                continue
            text = str(item.get("text") or "").strip()
            if not text:
                continue
            poly = self._normalize_box(item.get("box"))
            lines.append(
                OCRLine(
                    text=text,
                    score=self._to_float(item.get("score")),
                    bbox=bbox_from_poly(poly),
                    poly=poly,
                )
            )
        return OCRPayload(
            provider=self.name,
            model="umi-ocr",
            full_text="\n".join(line.text for line in lines),
            lines=lines,
            raw_result=body,
        )

    @staticmethod
    def _normalize_box(value: object) -> list[list[float]]:
        if not isinstance(value, list):
            return []
        result: list[list[float]] = []
        for point in value:
            if isinstance(point, (list, tuple)) and len(point) >= 2:
                try:
                    result.append([float(point[0]), float(point[1])])
                except (TypeError, ValueError):
                    continue
        return result

    @staticmethod
    def _to_float(value: object) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

