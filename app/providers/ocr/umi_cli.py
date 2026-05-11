from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from app.api.schemas.screenshots import OCRPayload
from app.providers.ocr.base import OCRProvider, OCRProviderError, normalize_text_lines


class UmiCLIProvider(OCRProvider):
    name = "umi_cli"

    def __init__(self, cli_path: str = "umi-ocr", timeout_seconds: int = 30) -> None:
        self.cli_path = cli_path
        self.timeout_seconds = timeout_seconds

    def recognize(self, image_bytes: bytes, mime_type: str = "image/jpeg") -> OCRPayload:
        suffix = ".png" if mime_type == "image/png" else ".jpg"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(image_bytes)
            image_path = Path(tmp.name)
        try:
            # Keep CLI arguments configurable at the wrapper level later. The first MVP
            # expects a JSON-lines compatible Umi-OCR CLI wrapper in PATH.
            proc = subprocess.run(
                [self.cli_path, "--path", str(image_path), "--json"],
                check=False,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
            if proc.returncode != 0:
                raise OCRProviderError(proc.stderr.strip() or "Umi-OCR CLI failed")
            raw = json.loads(proc.stdout)
            lines = raw.get("lines") if isinstance(raw, dict) else raw
            if not isinstance(lines, list):
                raise OCRProviderError("Umi-OCR CLI output has no lines list")
            payload = normalize_text_lines(self.name, lines)
            payload.raw_result = raw if isinstance(raw, dict) else {"lines": raw}
            return payload
        finally:
            image_path.unlink(missing_ok=True)

