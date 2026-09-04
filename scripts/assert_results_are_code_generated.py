#!/usr/bin/env python3
"""Guard: results/*.json must be written by calibshift.io (schema envelope)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
bad = []
for path in sorted((ROOT / "results").glob("*.json")):
    data = json.loads(path.read_text())
    if data.get("schema") != "calibshift.result.v1":
        bad.append((str(path), "missing schema envelope"))
        continue
    if "written_at_utc" not in data or "payload" not in data:
        bad.append((str(path), "incomplete envelope"))
if bad:
    print("RESULT INTEGRITY FAIL:")
    for item in bad:
        print(" ", item)
    sys.exit(1)
print(f"ok: {len(list((ROOT / 'results').glob('*.json')))} result files have schema envelope")
