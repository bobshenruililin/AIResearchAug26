"""P3-style grid: dual-regime router vs always-iid / always-clean / abort."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from calibshift.io import mark_failed_run, write_result
from calibshift.models import get_model
from dualregime.metrics import decision_summary
from dualregime.policies import fit_policy
from dualregime.world import generate_batch


def run_seed(cfg: dict, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    X_tr, y_tr, _ = generate_batch(
        int(cfg["n_train"]),
        rng,
        gx_lo=float(cfg["train_gx_lo"]),
        gx_hi=float(cfg["train_gx_hi"]),
    )
    X_cal, y_cal, _ = generate_batch(
        int(cfg["n_cal"]),
        rng,
        gx_lo=float(cfg["train_gx_lo"]),
        gx_hi=float(cfg["train_gx_hi"]),
    )
    X_iid, y_iid, _ = generate_batch(
        int(cfg["n_test"]),
        rng,
        gx_lo=float(cfg["train_gx_lo"]),
        gx_hi=float(cfg["train_gx_hi"]),
    )
    X_pert, y_pert, meta_p = generate_batch(
        int(cfg["n_test"]),
        rng,
        enc_bias=tuple(cfg["enc_bias"]),
        motor_bias=float(cfg["motor_bias"]),
        gx_lo=float(cfg["train_gx_lo"]),
        gx_hi=float(cfg["train_gx_hi"]),
    )
    X_sel, y_sel, meta_s = generate_batch(
        int(cfg["n_test"]),
        rng,
        gx_lo=float(cfg["select_gx_lo"]),
        gx_hi=float(cfg["select_gx_hi"]),
    )
    pol = fit_policy(
        X_tr,
        y_tr,
        X_cal,
        y_cal,
        get_model("hgb", seed=seed),
        get_model("hgb", seed=seed + 17),
        alpha=float(cfg["alpha"]),
    )
    cost = float(cfg["cost_fail"])
    rows = []
    for split, X, y in [("iid", X_iid, y_iid), ("perturb", X_pert, y_pert), ("select", X_sel, y_sel)]:
        for mode in ["router", "always_iid", "always_clean", "always_abort"]:
            out = pol.act(X, mode=mode)
            summ = decision_summary(y, out["act"], cost_fail=cost)
            rows.append(
                {
                    "split": split,
                    "mode": mode,
                    "n_pred_perturb": int((out["regime"] == "perturb").sum()),
                    "n_pred_select": int((out["regime"] == "select").sum()),
                    "n_pred_iid": int((out["regime"] == "iid").sum()),
                    **summ,
                }
            )
    return {
        "seed": seed,
        "meta_perturb": meta_p,
        "meta_select": meta_s,
        "rows": rows,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--config", type=Path, default=Path(__file__).with_name("config.yaml"))
    p.add_argument("--out", type=Path, default=ROOT / "results" / "exp08_dual_regime.json")
    args = p.parse_args()
    cfg = yaml.safe_load(args.config.read_text())
    t0 = time.time()
    cells = []
    failed = []
    for seed in cfg["seeds"]:
        try:
            cells.append(run_seed(cfg, int(seed)))
        except Exception as exc:  # noqa: BLE001
            import traceback

            failed.append({"seed": seed, "error": str(exc)})
            mark_failed_run(args.out.with_name(f"exp08_failed_seed{seed}.json"), str(exc), traceback.format_exc())
    write_result(
        args.out,
        {
            "status": "ok" if not failed else "partial",
            "config": cfg,
            "n_ok": len(cells),
            "n_failed": len(failed),
            "seconds": time.time() - t0,
            "cells": cells,
            "failed": failed,
        },
    )
    print(f"wrote {args.out} n_ok={len(cells)} n_failed={len(failed)}")


if __name__ == "__main__":
    main()
