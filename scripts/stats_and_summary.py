#!/usr/bin/env python3
"""Compute summary statistics and Wilcoxon tests from results/*.json.

Writes results/summary_main.json and results/stats_tests.json.
Never edits experiment JSONs.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import wilcoxon

ROOT = Path(__file__).resolve().parents[1]


def load(name: str) -> dict:
    return json.loads((ROOT / "results" / name).read_text())


def mean_std(xs: list[float]) -> dict:
    a = np.asarray(xs, dtype=float)
    return {
        "n": int(a.size),
        "mean": float(a.mean()) if a.size else None,
        "std": float(a.std(ddof=1)) if a.size > 1 else 0.0,
        "min": float(a.min()) if a.size else None,
        "max": float(a.max()) if a.size else None,
    }


def wilcoxon_gt0(xs: list[float]) -> dict:
    a = np.asarray(xs, dtype=float)
    # Wilcoxon on paired difference vs 0; alternative greater.
    try:
        stat, p = wilcoxon(a, alternative="greater", zero_method="wilcox")
        return {"stat": float(stat), "p_greater": float(p), "n": int(a.size)}
    except ValueError as exc:
        return {"error": str(exc), "n": int(a.size)}


def main() -> None:
    env = load("exp04_main_h1.json")
    payload = env["payload"]
    G = defaultdict(list)
    for cell in payload["cells"]:
        s = float(cell["shift"]["strength"])
        for row in cell["rows"]:
            G[(cell["dataset"], cell["model"], s, row["calibrator"])].append(
                {
                    "seed": cell["seed"],
                    "ece_iid": row["iid"]["ece"],
                    "ece_sh": row["shifted"]["ece"],
                    "delta_ece": row["delta_ece"],
                    "brier_iid": row["iid"]["brier"],
                    "brier_sh": row["shifted"]["brier"],
                    "acc_iid": row["iid"]["accuracy"],
                    "acc_sh": row["shifted"]["accuracy"],
                    "nll_iid": row["iid"]["nll"],
                    "nll_sh": row["shifted"]["nll"],
                    "cov_iid": row["conformal"]["coverage_iid"],
                    "cov_sh": row["conformal"]["coverage_shifted"],
                    "cov_sh_w": row["conformal"]["coverage_shifted_weighted"],
                }
            )

    datasets = payload["config"]["dataset_list"]
    models = payload["config"]["model_list"]
    cals = payload["config"]["calibrators"]
    strengths = payload["config"]["shift_strengths"]

    cells_summary = {}
    for ds in datasets:
        for m in models:
            for s in strengths:
                for cal in cals:
                    xs = G[(ds, m, float(s), cal)]
                    cells_summary[f"{ds}|{m}|s{s}|{cal}"] = {
                        "delta_ece": mean_std([x["delta_ece"] for x in xs]),
                        "ece_iid": mean_std([x["ece_iid"] for x in xs]),
                        "ece_shifted": mean_std([x["ece_sh"] for x in xs]),
                        "brier_iid": mean_std([x["brier_iid"] for x in xs]),
                        "brier_shifted": mean_std([x["brier_sh"] for x in xs]),
                        "acc_iid": mean_std([x["acc_iid"] for x in xs]),
                        "acc_shifted": mean_std([x["acc_sh"] for x in xs]),
                        "coverage_iid": mean_std([x["cov_iid"] for x in xs]),
                        "coverage_shifted": mean_std([x["cov_sh"] for x in xs]),
                    }

    pooled = {}
    tests = {"source": "results/exp04_main_h1.json", "tests": []}
    for cal in cals:
        diffs = []
        for ds in datasets:
            for m in models:
                diffs.extend(x["delta_ece"] for x in G[(ds, m, 1.5, cal)])
        pooled[cal] = {
            "s": 1.5,
            "delta_ece": mean_std(diffs),
            "n_pos": int(sum(d > 1e-12 for d in diffs)),
            "n_neg": int(sum(d < -1e-12 for d in diffs)),
            "n": len(diffs),
        }
        w = wilcoxon_gt0(diffs)
        tests["tests"].append(
            {
                "name": f"wilcoxon_delta_ece_gt0_s1.5_{cal}_pooled",
                "calibrator": cal,
                "shift_strength": 1.5,
                "hypothesis": "delta_ece > 0 (ECE_shifted > ECE_iid)",
                **w,
                "n_pos": pooled[cal]["n_pos"],
                "n_neg": pooled[cal]["n_neg"],
            }
        )

    # One ΔECE per (dataset, model), averaging seeds (n=12; less pseudo-replication).
    cell_means_none = []
    for ds in datasets:
        for m in models:
            diffs = [x["delta_ece"] for x in G[(ds, m, 1.5, "none")]]
            cell_means_none.append(float(np.mean(diffs)))
    tests["tests"].append(
        {
            "name": "wilcoxon_delta_ece_gt0_s1.5_none_dataset_model_means",
            "calibrator": "none",
            "shift_strength": 1.5,
            "hypothesis": "seed-averaged delta_ece > 0 over dataset x model cells",
            **wilcoxon_gt0(cell_means_none),
            "n_pos": int(sum(d > 1e-12 for d in cell_means_none)),
            "n_neg": int(sum(d < -1e-12 for d in cell_means_none)),
            "delta_ece": mean_std(cell_means_none),
        }
    )

    # per-dataset pooled over models/seeds
    for ds in datasets:
        for cal in cals:
            diffs = []
            for m in models:
                diffs.extend(x["delta_ece"] for x in G[(ds, m, 1.5, cal)])
            tests["tests"].append(
                {
                    "name": f"wilcoxon_delta_ece_gt0_s1.5_{cal}_{ds}",
                    "calibrator": cal,
                    "dataset": ds,
                    "shift_strength": 1.5,
                    **wilcoxon_gt0(diffs),
                    "delta_ece": mean_std(diffs),
                }
            )

    # calibration help under shift: ECE_sh(cal) - ECE_sh(none)
    help_rows = {}
    for ds in datasets:
        for m in models:
            none = {x["seed"]: x["ece_sh"] for x in G[(ds, m, 1.5, "none")]}
            for cal in cals:
                if cal == "none":
                    continue
                diffs = [x["ece_sh"] - none[x["seed"]] for x in G[(ds, m, 1.5, cal)]]
                help_rows[f"{ds}|{m}|{cal}"] = mean_std(diffs)

    # i.i.d. sanity s=0
    iid_sanity = {}
    for ds in datasets:
        for m in models:
            xs = G[(ds, m, 0.0, "none")]
            iid_sanity[f"{ds}|{m}|none"] = {
                "ece": mean_std([x["ece_iid"] for x in xs]),
                "acc": mean_std([x["acc_iid"] for x in xs]),
                "coverage": mean_std([x["cov_iid"] for x in xs]),
            }

    # exp05 / 06 / 07 compact
    def shift_kind_summary(fname: str) -> dict:
        p = load(fname)["payload"]
        H = defaultdict(list)
        for cell in p["cells"]:
            kind = cell["shift"]["kind"]
            for row in cell["rows"]:
                H[(cell["dataset"], cell["model"], kind, row["calibrator"])].append(row["delta_ece"])
        out = {}
        for k, xs in H.items():
            out["|".join(map(str, k))] = mean_std(xs)
        return {"n_ok": p["n_ok"], "n_failed": p["n_failed"], "seconds": p["seconds"], "delta_ece": out}

    e7 = load("exp07_noise_feature_control.json")["payload"]
    noise = defaultdict(list)
    for cell in e7["cells"]:
        for row in cell["rows"]:
            noise[(cell["dataset"], cell["model"], row["calibrator"])].append(row["delta_ece"])
    noise_out = {"|".join(map(str, k)): mean_std(xs) for k, xs in noise.items()}

    e6 = load("exp06_ablate_ncal.json")["payload"]
    ncal = defaultdict(list)
    for cell in e6["cells"]:
        iso = next(r["shifted"]["ece"] for r in cell["rows"] if r["calibrator"] == "isotonic")
        tmp = next(r["shifted"]["ece"] for r in cell["rows"] if r["calibrator"] == "temperature")
        ncal[(cell["dataset"], cell["model"], cell["n_cal"])].append(iso - tmp)
    ncal_out = {"|".join(map(str, k)): mean_std(xs) for k, xs in ncal.items()}

    e5s = shift_kind_summary("exp05_ablate_shift_family.json")
    qs_none = [v["mean"] for k, v in e5s["delta_ece"].items() if k.endswith("|quantile_slice|none")]
    imp_none = [v["mean"] for k, v in e5s["delta_ece"].items() if k.endswith("|importance_resample|none")]

    from calibshift.io import write_result

    write_result(
        ROOT / "results" / "summary_main.json",
        {
            "status": "ok",
            "source_experiments": [
                "exp04_main_h1.json",
                "exp05_ablate_shift_family.json",
                "exp06_ablate_ncal.json",
                "exp07_noise_feature_control.json",
            ],
            "exp04_n_ok": payload["n_ok"],
            "exp04_n_failed": payload["n_failed"],
            "exp04_seconds": payload["seconds"],
            "pooled_delta_ece_s1.5": pooled,
            "dataset_model_mean_delta_ece_s1.5_none": mean_std(cell_means_none),
            "cells": cells_summary,
            "ece_shifted_minus_none_s1.5": help_rows,
            "iid_sanity_s0_none": iid_sanity,
            "exp05": e5s,
            "exp06_isotonic_minus_temperature_shifted_ece": ncal_out,
            "exp07_noise_feature_delta_ece": noise_out,
            "exp05_none_quantile_slice_cellmean_delta_ece": mean_std(qs_none),
            "exp05_none_importance_resample_cellmean_delta_ece": mean_std(imp_none),
        },
    )
    write_result(ROOT / "results" / "stats_tests.json", tests)
    print("wrote results/summary_main.json and results/stats_tests.json")
    for t in tests["tests"][:4]:
        print(t["name"], "p=", t.get("p_greater"), "n=", t.get("n"))


if __name__ == "__main__":
    main()
