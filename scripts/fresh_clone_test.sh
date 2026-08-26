#!/usr/bin/env bash
# Prove a fresh clone can install and produce a results JSON without this
# working tree's venv or caches.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d /tmp/calibshift-fresh-XXXXXX)"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

git clone --local --no-hardlinks "$ROOT" "$TMP/repo"
cd "$TMP/repo"
# Drop any accidental local env
rm -rf .venv
python3 -m venv .venv
.venv/bin/pip install -U pip
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install -e .
.venv/bin/pytest -q
.venv/bin/python experiments/exp00_smoke/run.py --out results/exp00_smoke.json
python3 - <<'PY'
import json, sys
from pathlib import Path
p = Path("results/exp00_smoke.json")
data = json.loads(p.read_text())
assert data["schema"] == "calibshift.result.v1"
assert data["payload"]["status"] == "ok"
assert len(data["payload"]["rows"]) == 4
print("fresh-clone test PASS")
PY
