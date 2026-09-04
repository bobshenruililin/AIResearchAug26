"""Loneliness-track paper numbers and citations are JSON/API backed."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_lonely_macros_traceable_to_json():
    tex = (ROOT / "paper" / "lonely_numbers.tex").read_text()
    macros = dict(re.findall(r"\\newcommand\{\\Num(\w+)\}\{([^}]+)\}", tex))
    assert macros, "lonely_numbers.tex missing macros"
    blob = (ROOT / "results" / "summary_lonely.json").read_text()
    blob += (ROOT / "results" / "exp10_quorum_lonely.json").read_text()
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
        nums += [float(x) for x in re.findall(r"(?<![\d.])\d+(?![\d.])", blob)]
        if not any(abs(n - fv) <= 5e-4 or abs(n - fv) / max(abs(fv), 1e-18) < 0.08 for n in nums):
            missing.append(f"{key}={val}")
    assert not missing, missing


def test_lonely_paper_cites_only_verified_bib():
    tex = (ROOT / "paper" / "lonely.tex").read_text()
    keys = set()
    for group in re.findall(r"\\cite\{([^}]+)\}", tex):
        keys.update(k.strip() for k in group.split(","))
    bib = (ROOT / "paper" / "lonely_verified.bib").read_text()
    bkeys = set(re.findall(r"@\w+\{([^,]+),", bib))
    assert keys, "lonely.tex has no citations"
    assert keys <= bkeys, sorted(keys - bkeys)


def test_exp10_complete():
    env = json.loads((ROOT / "results" / "exp10_quorum_lonely.json").read_text())
    assert env["schema"] == "calibshift.result.v1"
    assert env["payload"]["status"] == "ok"
    assert env["payload"]["n_ok"] == 120
    assert env["payload"]["n_failed"] == 0
    ex = env["payload"]["headline_exact"]
    assert ex["kill_q1_delta"] == 0.0
    assert ex["delta_dyad_pub"] > 0.15
