"""Evaluate a fitted calibrator on i.i.d. and shifted test sets."""

from __future__ import annotations

from typing import Any

import numpy as np

from .conformal import conformal_coverage, conformal_set_size, split_conformal_quantile
from .metrics import (
    accuracy,
    brier_score,
    expected_calibration_error,
    maximum_calibration_error,
    negative_log_likelihood,
    reliability_bins,
)


def score_pack(y: np.ndarray, p: np.ndarray, n_bins: int = 15) -> dict[str, Any]:
    return {
        "n": int(len(y)),
        "accuracy": accuracy(y, p),
        "ece": expected_calibration_error(y, p, n_bins=n_bins),
        "ece_quantile": expected_calibration_error(y, p, n_bins=n_bins, strategy="quantile"),
        "mce": maximum_calibration_error(y, p, n_bins=n_bins),
        "brier": brier_score(y, p),
        "nll": negative_log_likelihood(y, p),
        "reliability": reliability_bins(y, p, n_bins=n_bins),
    }


def conformal_pack(y_cal: np.ndarray, p_cal: np.ndarray, y_te: np.ndarray, p_te: np.ndarray, alpha: float) -> dict:
    q = split_conformal_quantile(y_cal, p_cal, alpha=alpha)
    return {
        "alpha": alpha,
        "q_hat": q,
        "coverage": conformal_coverage(y_te, p_te, q),
        "mean_set_size": conformal_set_size(p_te, q),
    }
