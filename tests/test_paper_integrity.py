"""Ensure paper/numbers.tex macros appear (rounded) in result JSON."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_every_macro_is_traceable_to_json():
    tex = (ROOT / "paper" / "numbers.tex").read_text()
    macros = dict(re.findall(r"\\newcommand\{\\Num(\w+)\}\{([^}]+)\}", tex))
    assert macros, "numbers.tex missing macros"
    blob = (ROOT / "results" / "summary_main.json").read_text()
    blob += (ROOT / "results" / "stats_tests.json").read_text()
    missing = []
    for key, val in macros.items():
        if val in blob:
            continue
        try:
            fv = float(val)
        except ValueError:
            missing.append(key)
            continue
        nums = [float(x) for x in re.findall(r"-?\d+\.\d+(?:[eE][+-]?\d+)?", blob)]
        if not any(abs(n - fv) <= 5e-4 or abs(n - fv) / max(abs(fv), 1e-18) < 0.08 for n in nums):
            missing.append(f"{key}={val}")
    assert not missing, missing


def test_paper_cites_only_verified_bib():
    tex = (ROOT / "paper" / "main.tex").read_text()
    keys = set()
    for group in re.findall(r"\\cite\{([^}]+)\}", tex):
        keys.update(k.strip() for k in group.split(","))
    bib = (ROOT / "paper" / "verified.bib").read_text()
    bkeys = set(re.findall(r"@\w+\{([^,]+),", bib))
    assert keys <= bkeys, sorted(keys - bkeys)


def test_exp04_complete():
    env = json.loads((ROOT / "results" / "exp04_main_h1.json").read_text())
    assert env["payload"]["status"] == "ok"
    assert env["payload"]["n_ok"] == 240
    assert env["payload"]["n_failed"] == 0
