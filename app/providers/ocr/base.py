from __future__ import annotations

from abc import ABC, abstractmethod

from app.api.schemas.screenshots import OCRLine, OCRPayload


class OCRProviderError(RuntimeError):
    """Raised when an OCR provider cannot produce a normalized result."""


class OCRProvider(ABC):
    name: str

    @abstractmethod
    def recognize(self, image_bytes: bytes, mime_type: str = "image/jpeg") -> OCRPayload:
        """Return a normalized OCR payload."""


def bbox_from_poly(poly: list[list[float]]) -> dict[str, float]:
    xs = [point[0] for point in poly if len(point) >= 2]
    ys = [point[1] for point in poly if len(point) >= 2]
    if not xs or not ys:
        return {"x_min": 0.0, "y_min": 0.0, "x_max": 0.0, "y_max": 0.0}
    return {
        "x_min": float(min(xs)),
        "y_min": float(min(ys)),
        "x_max": float(max(xs)),
        "y_max": float(max(ys)),
    }


def normalize_text_lines(provider: str, raw_lines: list[dict]) -> OCRPayload:
    lines: list[OCRLine] = []
    for item in raw_lines:
        text = str(item.get("text") or "").strip()
        if not text:
            continue
        poly = item.get("poly") or item.get("box") or []
        normalized_poly = _normalize_poly(poly)
        bbox = item.get("bbox") if isinstance(item.get("bbox"), dict) else bbox_from_poly(normalized_poly)
        lines.append(
            OCRLine(
                text=text,
                score=_to_float(item.get("score")),
                bbox={key: float(value) for key, value in bbox.items()},
                poly=normalized_poly,
            )
        )
    return OCRPayload(
        provider=provider,
        full_text="\n".join(line.text for line in lines),
        lines=lines,
        raw_result={"line_count": len(lines)},
    )


def _normalize_poly(value: object) -> list[list[float]]:
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


def _to_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

