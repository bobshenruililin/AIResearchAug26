"""Multivariate density-ratio weights for the selection path.

Replaces the killed H3 1-D histogram ratio on feature 0. Fitted as a
domain classifier in camera-xy (the coordinates a workspace slice moves).
Never used as a perturbation fix: Tibshirani weights assume P(Y|X)
invariant, which frozen-label encoder bias violates.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .world import CAM_XY_IDX


@dataclass
class DensityRatioResult:
    w_cal: np.ndarray
    ess: float
    domain_auc: float
    unreliable: bool
    n_cal: int
    n_target: int


def camera_xy(X: np.ndarray) -> np.ndarray:
    return np.asarray(X, dtype=np.float64)[:, CAM_XY_IDX]


def fit_density_ratio_mv(
    X_cal: np.ndarray,
    X_target: np.ndarray,
    w_min: float = 0.05,
    w_max: float = 20.0,
    seed: int = 0,
) -> DensityRatioResult:
    """w(x) ≈ p_target(x) / p_cal(x) on camera xy, clipped.

    Labels: 0 = calibration (source), 1 = unlabeled target. No y_test.
    """
    z_cal = camera_xy(X_cal)
    z_tgt = camera_xy(X_target)
    n_cal = len(z_cal)
    n_tgt = len(z_tgt)
    if n_cal < 16 or n_tgt < 16:
        w = np.ones(n_cal)
        return DensityRatioResult(w, float(n_cal), 0.5, True, n_cal, n_tgt)

    Z = np.vstack([z_cal, z_tgt])
    y = np.concatenate([np.zeros(n_cal, dtype=int), np.ones(n_tgt, dtype=int)])
    # AUC on a disjoint half so we do not score the same points we train on.
    try:
        Z_tr, Z_te, y_tr, y_te = train_test_split(
            Z, y, test_size=0.5, random_state=seed, stratify=y
        )
    except ValueError:
        Z_tr, Z_te, y_tr, y_te = Z, Z, y, y
    clf = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("lr", LogisticRegression(max_iter=1000, random_state=seed)),
        ]
    )
    clf.fit(Z_tr, y_tr)
    try:
        auc = float(roc_auc_score(y_te, clf.predict_proba(Z_te)[:, 1]))
    except ValueError:
        auc = 0.5

    # Refit on all unlabeled target + cal for the actual weights.
    clf.fit(Z, y)
    pi = np.clip(clf.predict_proba(z_cal)[:, 1], 1e-6, 1.0 - 1e-6)
    w = (pi / (1.0 - pi)) * (n_cal / max(n_tgt, 1))
    w = np.clip(w, w_min, w_max)
    ess = float((w.sum() ** 2) / max((w**2).sum(), 1e-12))
    # No detectable P(X) change → weights ≈ 1 (do not invent a slice).
    if auc < 0.55:
        w = np.ones(n_cal)
        ess = float(n_cal)
        unreliable = False
    else:
        unreliable = ess < 0.25 * n_cal
        if unreliable:
            w = np.ones(n_cal)
            ess = float(n_cal)
    return DensityRatioResult(
        w_cal=w,
        ess=ess,
        domain_auc=auc,
        unreliable=unreliable,
        n_cal=n_cal,
        n_target=n_tgt,
    )
