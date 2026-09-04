"""Homogeneous dual-regime grid + mixed stream on planar peg-in-hole."""

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
from dualregime.detector import REGIME_IID, REGIME_PERTURB, REGIME_SELECT
from dualregime.metrics import decision_summary
from dualregime.policies import fit_policy
from dualregime.world import generate_batch

MODES = [
    "router",
    "detector_off",
    "always_abort",
    "illegal_T",
    "denoise_off",
    "always_project",
    "oracle",
]


def _true_regimes(n: int, name: str) -> np.ndarray:
    label = {"iid": REGIME_IID, "perturb": REGIME_PERTURB, "select": REGIME_SELECT}[name]
    return np.full(n, label, dtype=object)


def run_seed(cfg: dict, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    n_tr, n_cal, n_te = int(cfg["n_train"]), int(cfg["n_cal"]), int(cfg["n_test"])
    scale = float(cfg["enc_xy_scale"])
    X_tr, y_tr, _ = generate_batch(n_tr, rng)
    X_cal, y_cal, _ = generate_batch(n_cal, rng)
    X_iid, y_iid, meta_i = generate_batch(n_te, rng)
    X_pert, y_pert, meta_p = generate_batch(n_te, rng, enc_xy_scale=scale)
    X_sel, y_sel, meta_s = generate_batch(n_te, rng, x_lo=float(cfg["select_x_lo"]))
    pol = fit_policy(
        X_tr,
        y_tr,
        X_cal,
        y_cal,
        get_model("hgb", seed=seed),
        alpha=float(cfg["alpha"]),
        tau_act=float(cfg["tau_act"]),
    )
    rows = []
    splits = [
        ("iid", X_iid, y_iid),
        ("perturb", X_pert, y_pert),
        ("select", X_sel, y_sel),
    ]
    for split, X, y in splits:
        true = _true_regimes(len(y), split)
        for mode in MODES:
            out = pol.act(X, mode=mode, regimes=true if mode == "oracle" else None)
            summ = decision_summary(
                y,
                out["action"],
                out["p_used"],
                tau_act=float(cfg["tau_act"]),
            )
            path = out["path"]
            rows.append(
                {
                    "split": split,
                    "mode": mode,
                    "n_pred_perturb": int((out["regime"] == REGIME_PERTURB).sum()),
                    "n_pred_select": int((out["regime"] == REGIME_SELECT).sum()),
                    "n_pred_iid": int((out["regime"] == REGIME_IID).sum()),
                    "n_path_project": int((path == "project_then_T").sum()),
                    "n_path_illegal": int((path == "illegal_T_raw").sum()),
                    "n_path_abort": int((path == "abort").sum()),
                    "n_path_select": int((path == "select_weighted").sum()),
                    "domain_auc": out.get("domain_auc"),
                    **summ,
                }
            )

    # Mixed stream: iid → select → perturb blocks. Point+batch detector.
    n_block = int(cfg.get("n_stream_block", 160))
    X_si, y_si, _ = generate_batch(n_block, rng)
    X_ss, y_ss, _ = generate_batch(n_block, rng, x_lo=float(cfg["select_x_lo"]))
    X_sp, y_sp, _ = generate_batch(n_block, rng, enc_xy_scale=scale)
    X_stream = np.vstack([X_si, X_ss, X_sp])
    y_stream = np.concatenate([y_si, y_ss, y_sp])
    true_stream = np.concatenate(
        [
            _true_regimes(n_block, "iid"),
            _true_regimes(n_block, "select"),
            _true_regimes(n_block, "perturb"),
        ]
    )
    stream_out = pol.act(X_stream, mode="router", stream=True)
    stream_summ = decision_summary(
        y_stream, stream_out["action"], stream_out["p_used"], tau_act=float(cfg["tau_act"])
    )
    stream_regime_acc = float((stream_out["regime"] == true_stream).mean())
    block_rows = []
    for bname, sl in [
        ("iid", slice(0, n_block)),
        ("select", slice(n_block, 2 * n_block)),
        ("perturb", slice(2 * n_block, 3 * n_block)),
    ]:
        block_rows.append(
            {
                "block": bname,
                **decision_summary(
                    y_stream[sl],
                    stream_out["action"][sl],
                    stream_out["p_used"][sl],
                    tau_act=float(cfg["tau_act"]),
                ),
                "n_pred_perturb": int((stream_out["regime"][sl] == REGIME_PERTURB).sum()),
                "n_pred_select": int((stream_out["regime"][sl] == REGIME_SELECT).sum()),
                "n_pred_iid": int((stream_out["regime"][sl] == REGIME_IID).sum()),
                "n_path_project": int((stream_out["path"][sl] == "project_then_T").sum()),
                "n_path_abort": int((stream_out["path"][sl] == "abort").sum()),
            }
        )
    return {
        "seed": seed,
        "meta_iid": meta_i,
        "meta_perturb": meta_p,
        "meta_select": meta_s,
        "pos_rate_iid": meta_i["pos_rate"],
        "pos_rate_pert": meta_p["pos_rate"],
        "pos_rate_sel": meta_s["pos_rate"],
        "rows": rows,
        "stream": {
            "overall": stream_summ,
            "blocks": block_rows,
            "n_block": n_block,
            "regime_acc": stream_regime_acc,
        },
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--config", type=Path, default=Path(__file__).with_name("config.yaml"))
    p.add_argument("--out", type=Path, default=ROOT / "results" / "exp09_peg_insert.json")
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
            mark_failed_run(
                args.out.with_name(f"exp09_failed_seed{seed}.json"),
                str(exc),
                traceback.format_exc(),
            )
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
