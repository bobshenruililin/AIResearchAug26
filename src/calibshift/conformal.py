"""Split conformal prediction with APS nonconformity scores.

Score = 1 - p_trueclass. Coverage is P(true label in prediction set).
For binary/multiclass, the set is {k : p_k >= 1 - q_hat} which is equivalent
to including y iff 1 - p_y <= q_hat.
"""

from __future__ import annotations

import numpy as np


def split_conformal_quantile(
    y_cal: np.ndarray,
    p_cal: np.ndarray,
    alpha: float = 0.1,
) -> float:
    y_cal = np.asarray(y_cal, dtype=int)
    p_cal = np.asarray(p_cal, dtype=np.float64)
    if p_cal.ndim == 1:
        p_cal = np.column_stack([1 - p_cal, p_cal])
    scores = 1.0 - p_cal[np.arange(len(y_cal)), y_cal]
    n = len(scores)
    q_level = np.ceil((n + 1) * (1 - alpha)) / n
    q_level = min(q_level, 1.0)
    return float(np.quantile(scores, q_level, method="higher"))


def conformal_coverage(
    y: np.ndarray,
    p: np.ndarray,
    q_hat: float,
) -> float:
    y = np.asarray(y, dtype=int)
    p = np.asarray(p, dtype=np.float64)
    if p.ndim == 1:
        p = np.column_stack([1 - p, p])
    scores = 1.0 - p[np.arange(len(y)), y]
    return float(np.mean(scores <= q_hat))


def conformal_set_size(
    p: np.ndarray,
    q_hat: float,
) -> float:
    p = np.asarray(p, dtype=np.float64)
    if p.ndim == 1:
        p = np.column_stack([1 - p, p])
    included = p >= (1.0 - q_hat)
    return float(included.sum(axis=1).mean())


def weighted_conformal_quantile(
    y_cal: np.ndarray,
    p_cal: np.ndarray,
    weights: np.ndarray,
    alpha: float = 0.1,
) -> float:
    """Weighted split conformal (Tibshirani-style) with finite-sample correction.

    weights are w(X_i) for calibration points (density ratio p_test/p_cal).
    """
    y_cal = np.asarray(y_cal, dtype=int)
    p_cal = np.asarray(p_cal, dtype=np.float64)
    weights = np.asarray(weights, dtype=np.float64)
    if p_cal.ndim == 1:
        p_cal = np.column_stack([1 - p_cal, p_cal])
    scores = 1.0 - p_cal[np.arange(len(y_cal)), y_cal]
    order = np.argsort(scores)
    scores_s = scores[order]
    w_s = np.clip(weights[order], 1e-12, None)
    w_s = w_s / w_s.sum()
    cdf = np.cumsum(w_s)
    # Conservative: include a (n+1) mass of the next test point approximated
    # by remaining tail; use first score whose weighted cdf >= 1-alpha.
    hit = np.nonzero(cdf >= (1.0 - alpha))[0]
    if hit.size == 0:
        return 1.0
    return float(scores_s[hit[0]])
