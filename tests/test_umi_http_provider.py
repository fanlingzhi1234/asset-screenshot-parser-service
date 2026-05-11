from __future__ import annotations

from typing import Any

import requests

from app.providers.ocr.umi_http import UmiHTTPProvider


class FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self.payload


def test_umi_http_provider_normalizes_success_response(monkeypatch) -> None:
    def fake_post(*args, **kwargs):
        return FakeResponse(
            {
                "code": 100,
                "data": [
                    {"text": "航天发展", "score": 0.98, "box": [[1, 2], [10, 2], [10, 8], [1, 8]]},
                    {"end": True},
                ],
            }
        )

    monkeypatch.setattr(requests, "post", fake_post)
    payload = UmiHTTPProvider("http://127.0.0.1:1224").recognize(b"fake")

    assert payload.provider == "umi_http"
    assert payload.lines[0].text == "航天发展"
    assert payload.lines[0].bbox == {"x_min": 1.0, "y_min": 2.0, "x_max": 10.0, "y_max": 8.0}

