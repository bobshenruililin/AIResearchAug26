"""JSON result I/O. Results must only be written by code, never edited by hand."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def write_result(path: str | Path, payload: dict[str, Any]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    envelope = {
        "written_at_utc": datetime.now(timezone.utc).isoformat(),
        "schema": "calibshift.result.v1",
        "payload": payload,
    }
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(envelope, indent=2, sort_keys=True) + "\n")
    tmp.replace(path)
    return path


def read_result(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def mark_failed_run(path: str | Path, error: str, traceback_text: str) -> Path:
    return write_result(
        path,
        {
            "status": "failed",
            "error": error,
            "traceback": traceback_text,
        },
    )
