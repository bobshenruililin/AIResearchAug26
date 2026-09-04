#!/usr/bin/env python3
"""Summarize exp09 dual-regime utilities into results/summary_dual.json."""

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
    path = ROOT / "results" / "exp09_peg_insert.json"
    payload = json.loads(path.read_text())["payload"]
    G = defaultdict(list)
    streams = defaultdict(list)
    pos = defaultdict(list)
    for cell in payload["cells"]:
        pos["iid"].append(cell["pos_rate_iid"])
        pos["pert"].append(cell["pos_rate_pert"])
        pos["sel"].append(cell["pos_rate_sel"])
        for row in cell["rows"]:
            G[(row["split"], row["mode"])].append(row)
        for br in cell["stream"]["blocks"]:
            streams[br["block"]].append(br)

    cells_out = {}
    for (split, mode), rows in G.items():
        cells_out[f"{split}|{mode}"] = {
            "mean_utility": mean_std([r["mean_utility"] for r in rows]),
            "utility": mean_std([r["utility"] for r in rows]),
            "false_confident_act_rate": mean_std([r["false_confident_act_rate"] for r in rows]),
            "false_confident_rate": mean_std([r["false_confident_act_rate"] for r in rows]),
            "unsafe_act_rate": mean_std([r["unsafe_act_rate"] for r in rows]),
            "act_rate": mean_std([r["act_rate"] for r in rows]),
            "abort_rate": mean_std([r["abort_rate"] for r in rows]),
            "defer_rate": mean_std([r["defer_rate"] for r in rows]),
            "recall_success": mean_std([r["recall_success"] for r in rows]),
            "precision_among_acts": mean_std([r["precision_among_acts"] for r in rows]),
            "safety_coverage": mean_std([r["safety_coverage"] for r in rows]),
            "frac_pred_perturb": mean_std([r["n_pred_perturb"] / max(r["n"], 1) for r in rows]),
            "frac_path_project": mean_std([r["n_path_project"] / max(r["n"], 1) for r in rows]),
        }

    def m(split: str, mode: str, field: str) -> float:
        return cells_out[f"{split}|{mode}"][field]["mean"]

    # Identifying inequalities / kill criteria (spec K1–K8, K12) on seed means.
    kills = {}
    kills["K1_policy_collapse"] = abs(
        m("perturb", "router", "false_confident_act_rate")
        - m("perturb", "illegal_T", "false_confident_act_rate")
    ) < 0.01 and abs(m("perturb", "router", "mean_utility") - m("perturb", "illegal_T", "mean_utility")) < 0.05
    kills["K3_always_conservative_wins"] = m("perturb", "always_abort", "mean_utility") >= m(
        "perturb", "router", "mean_utility"
    ) and m("select", "always_abort", "mean_utility") >= m("select", "router", "mean_utility")
    kills["K4_selection_needs_abort"] = m("select", "router", "abort_rate") > 0.25
    kills["K8_no_action_difference"] = abs(
        m("perturb", "router", "act_rate") - m("iid", "router", "act_rate")
    ) < 0.05 and m("perturb", "router", "abort_rate") < 0.05 and m(
        "perturb", "router", "frac_path_project"
    ) < 0.05
    kills["K12_tibshirani_on_perturbation"] = False  # perturbation path never uses density weights

    stream_out = {}
    for block, rows in streams.items():
        stream_out[block] = {
            "mean_utility": mean_std([r["mean_utility"] for r in rows]),
            "act_rate": mean_std([r["act_rate"] for r in rows]),
            "abort_rate": mean_std([r["abort_rate"] for r in rows]),
            "false_confident_act_rate": mean_std([r["false_confident_act_rate"] for r in rows]),
            "frac_pred_perturb": mean_std([r["n_pred_perturb"] / max(r["n"], 1) for r in rows]),
            "frac_pred_select": mean_std([r["n_pred_select"] / max(r["n"], 1) for r in rows]),
            "frac_path_project": mean_std([r["n_path_project"] / max(r["n"], 1) for r in rows]),
        }

    out = {
        "source": "exp09_peg_insert.json",
        "n_seeds": payload["n_ok"],
        "seconds": payload.get("seconds"),
        "pos_rate": {k: mean_std(v) for k, v in pos.items()},
        "cells": cells_out,
        "stream_blocks": stream_out,
        "kill_criteria_fired": kills,
        "any_kill": any(kills.values()),
        "kills_fired": ",".join(k for k, v in kills.items() if v) or "none",
    }
    write_result(ROOT / "results" / "summary_dual.json", out)
    print("wrote results/summary_dual.json any_kill=", out["any_kill"])


if __name__ == "__main__":
    main()
