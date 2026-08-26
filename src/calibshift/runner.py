"""Shared experiment grid used by exp01–exp03 and later main runs."""

from __future__ import annotations

import time
from typing import Any

import numpy as np
from sklearn.model_selection import train_test_split

from .calibrators import get_calibrator
from .conformal import (
    conformal_coverage,
    conformal_set_size,
    split_conformal_quantile,
    weighted_conformal_quantile,
)
from .data import load_dataset
from .eval import score_pack
from .models import get_model
from .shift import (
    gaussian_feature_shift,
    importance_resample,
    oracle_density_ratio_1d,
    quantile_slice,
)


def apply_shift(kind: str, X, y, rng, cfg: dict) -> tuple[np.ndarray, np.ndarray, dict]:
    if kind == "none":
        return np.asarray(X), np.asarray(y), {"kind": "none"}
    if kind == "gaussian_feature_shift":
        return gaussian_feature_shift(
            X,
            y,
            rng,
            strength=float(cfg.get("strength", 1.5)),
            n_features=cfg.get("n_features"),
            cols=cfg.get("cols"),
        )
    if kind == "quantile_slice":
        return quantile_slice(
            X,
            y,
            feature_index=int(cfg.get("feature_index", 0)),
            upper=bool(cfg.get("upper", True)),
            quantile=float(cfg.get("quantile", 0.5)),
        )
    if kind == "importance_resample":
        Xs, ys, _, meta = importance_resample(
            X,
            y,
            rng,
            feature_index=int(cfg.get("feature_index", 0)),
            tilt=float(cfg.get("tilt", 1.5)),
            size=cfg.get("size"),
        )
        return Xs, ys, meta
    raise ValueError(f"unknown shift {kind}")


def run_one_cell(cfg: dict) -> dict[str, Any]:
    """cfg keys: dataset, model, seed, calibrators, shift, n_cal (optional), alpha, ece_bins."""
    t0 = time.time()
    seed = int(cfg["seed"])
    ds = load_dataset(cfg["dataset"], seed=seed)
    rng = np.random.default_rng(seed)

    n_cal_target = cfg.get("n_cal")
    X_train, X_rest, y_train, y_rest = train_test_split(
        ds.X, ds.y, train_size=0.5, random_state=seed, stratify=ds.y
    )
    if n_cal_target is not None:
        n_cal_target = min(int(n_cal_target), len(y_rest) // 2)
        X_cal, X_test, y_cal, y_test = train_test_split(
            X_rest, y_rest, train_size=n_cal_target, random_state=seed + 1, stratify=y_rest
        )
    else:
        X_cal, X_test, y_cal, y_test = train_test_split(
            X_rest, y_rest, train_size=0.5, random_state=seed + 1, stratify=y_rest
        )

    model = get_model(cfg["model"], seed=seed)
    model.fit(X_train, y_train)
    p_cal_raw = model.predict_proba(X_cal)
    p_iid_raw = model.predict_proba(X_test)

    shift_cfg = cfg.get("shift") or {"kind": "gaussian_feature_shift", "strength": 1.5}
    kind = shift_cfg.get("kind", "gaussian_feature_shift")
    X_shift, y_shift, shift_meta = apply_shift(kind, X_test, y_test, rng, shift_cfg)
    p_shift_raw = model.predict_proba(X_shift)

    alpha = float(cfg.get("alpha", 0.1))
    n_bins = int(cfg.get("ece_bins", 15))
    include_rel = bool(cfg.get("include_reliability", False))

    rows = []
    for cal_name in cfg["calibrators"]:
        cal = get_calibrator(cal_name, n_bins=n_bins)
        cal.fit(p_cal_raw, y_cal)
        p_cal = cal.transform(p_cal_raw)
        p_iid = cal.transform(p_iid_raw)
        p_sh = cal.transform(p_shift_raw)
        iid = score_pack(y_test, p_iid, n_bins=n_bins)
        sh = score_pack(y_shift, p_sh, n_bins=n_bins)
        if not include_rel:
            iid.pop("reliability", None)
            sh.pop("reliability", None)
        q = split_conformal_quantile(y_cal, p_cal, alpha=alpha)
        # oracle 1D ratio on feature 0 of raw X (pre-calibrator)
        w_cal = oracle_density_ratio_1d(X_cal[:, 0], X_shift[:, 0])
        q_w = weighted_conformal_quantile(y_cal, p_cal, w_cal, alpha=alpha)
        row = {
            "calibrator": cal_name,
            "temperature_T": getattr(cal, "T", None),
            "iid": iid,
            "shifted": sh,
            "delta_ece": sh["ece"] - iid["ece"],
            "delta_brier": sh["brier"] - iid["brier"],
            "conformal": {
                "alpha": alpha,
                "q_hat": q,
                "coverage_iid": conformal_coverage(y_test, p_iid, q),
                "coverage_shifted": conformal_coverage(y_shift, p_sh, q),
                "set_size_iid": conformal_set_size(p_iid, q),
                "set_size_shifted": conformal_set_size(p_sh, q),
                "q_hat_weighted": q_w,
                "coverage_shifted_weighted": conformal_coverage(y_shift, p_sh, q_w),
                "set_size_shifted_weighted": conformal_set_size(p_sh, q_w),
            },
        }
        rows.append(row)

    return {
        "status": "ok",
        "dataset": cfg["dataset"],
        "model": cfg["model"],
        "seed": seed,
        "n_train": int(len(y_train)),
        "n_cal": int(len(y_cal)),
        "n_test": int(len(y_test)),
        "n_shifted": int(len(y_shift)),
        "n_classes": int(ds.n_classes),
        "shift": shift_meta,
        "seconds": time.time() - t0,
        "rows": rows,
    }


def run_grid(cells: list[dict]) -> dict[str, Any]:
    results = []
    failures = []
    t0 = time.time()
    for i, cell in enumerate(cells):
        try:
            results.append(run_one_cell(cell))
        except Exception as exc:  # noqa: BLE001 — persist, do not hide
            import traceback

            failures.append(
                {
                    "status": "failed",
                    "cell": cell,
                    "error": str(exc),
                    "traceback": traceback.format_exc(),
                }
            )
    return {
        "status": "ok" if not failures else "partial",
        "n_ok": len(results),
        "n_failed": len(failures),
        "seconds": time.time() - t0,
        "cells": results,
        "failures": failures,
    }
