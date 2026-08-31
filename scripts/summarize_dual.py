#!/usr/bin/env python3
"""Summarize exp08 dual-regime utilities into results/summary_dual.json."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import json

import numpy as np

from calibshift.io import write_result

ROOT = Path(__file__).resolve().parents[1]


def mean_std(xs: list[float]) -> dict:
    a = np.asarray(xs, dtype=float)
    return {
        "n": int(a.size),
        "mean": float(a.mean()) if a.size else None,
        "std": float(a.std(ddof=1)) if a.size > 1 else 0.0,
    }


def main() -> None:
    env = json_load()
    payload = env["payload"]
    G = defaultdict(list)
    for cell in payload["cells"]:
        for row in cell["rows"]:
            G[(row["split"], row["mode"])].append(row)
    out = {"source": "exp08_dual_regime.json", "n_seeds": payload["n_ok"], "cells": {}}
    for (split, mode), rows in G.items():
        out["cells"][f"{split}|{mode}"] = {
            "utility": mean_std([r["utility"] for r in rows]),
            "false_confident_rate": mean_std([r["false_confident_rate"] for r in rows]),
            "recall_success": mean_std([r["recall_success"] for r in rows]),
            "precision_among_acts": mean_std([r["precision_among_acts"] for r in rows]),
        }
    write_result(ROOT / "results" / "summary_dual.json", out)
    print("wrote results/summary_dual.json")


def json_load():
    return json.loads((ROOT / "results" / "exp08_dual_regime.json").read_text())


if __name__ == "__main__":
    main()
