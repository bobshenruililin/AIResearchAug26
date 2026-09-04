"""Calibration and scoring metrics.

ECE follows the confidence-binned definition of Guo et al. (2017): bin
examples by max predicted probability (confidence), then take the weighted
mean absolute difference between bin accuracy and bin confidence.

All functions accept integer labels y in {0,...,C-1} and probabilities
p with shape (n, C). Binary (n,) probabilities are expanded internally.
"""

from __future__ import annotations

import numpy as np


def _as_proba(p: np.ndarray) -> np.ndarray:
    p = np.asarray(p, dtype=np.float64)
    if p.ndim == 1:
        p = np.clip(p, 0.0, 1.0)
        return np.column_stack([1.0 - p, p])
    p = np.clip(p, 0.0, 1.0)
    row_sum = p.sum(axis=1, keepdims=True)
    row_sum = np.where(row_sum <= 0, 1.0, row_sum)
    return p / row_sum


def expected_calibration_error(
    y: np.ndarray,
    p: np.ndarray,
    n_bins: int = 15,
    strategy: str = "uniform",
) -> float:
    """Confidence ECE with equal-width (uniform) or equal-count (quantile) bins."""
    y = np.asarray(y, dtype=int)
    p = _as_proba(p)
    conf = p.max(axis=1)
    pred = p.argmax(axis=1)
    correct = (pred == y).astype(np.float64)
    if strategy == "quantile":
        edges = np.unique(np.quantile(conf, np.linspace(0.0, 1.0, n_bins + 1)))
        if edges.size < 2:
            return 0.0
    else:
        edges = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    n = len(y)
    for i in range(len(edges) - 1):
        lo, hi = edges[i], edges[i + 1]
        if i == len(edges) - 2:
            mask = (conf >= lo) & (conf <= hi)
        else:
            mask = (conf >= lo) & (conf < hi)
        if not np.any(mask):
            continue
        acc = correct[mask].mean()
        avg_conf = conf[mask].mean()
        ece += (mask.sum() / n) * abs(acc - avg_conf)
    return float(ece)


def maximum_calibration_error(
    y: np.ndarray,
    p: np.ndarray,
    n_bins: int = 15,
) -> float:
    y = np.asarray(y, dtype=int)
    p = _as_proba(p)
    conf = p.max(axis=1)
    pred = p.argmax(axis=1)
    correct = (pred == y).astype(np.float64)
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    mce = 0.0
    for i in range(n_bins):
        lo, hi = edges[i], edges[i + 1]
        mask = (conf >= lo) & (conf <= hi) if i == n_bins - 1 else (conf >= lo) & (conf < hi)
        if not np.any(mask):
            continue
        gap = abs(correct[mask].mean() - conf[mask].mean())
        mce = max(mce, gap)
    return float(mce)


def brier_score(y: np.ndarray, p: np.ndarray) -> float:
    """Multiclass Brier score: mean squared error vs one-hot labels."""
    y = np.asarray(y, dtype=int)
    p = _as_proba(p)
    n, c = p.shape
    onehot = np.zeros((n, c), dtype=np.float64)
    onehot[np.arange(n), y] = 1.0
    return float(np.mean(np.sum((p - onehot) ** 2, axis=1)))


def negative_log_likelihood(y: np.ndarray, p: np.ndarray, eps: float = 1e-12) -> float:
    y = np.asarray(y, dtype=int)
    p = _as_proba(p)
    return float(-np.mean(np.log(np.clip(p[np.arange(len(y)), y], eps, 1.0))))


def accuracy(y: np.ndarray, p: np.ndarray) -> float:
    y = np.asarray(y, dtype=int)
    p = _as_proba(p)
    return float(np.mean(p.argmax(axis=1) == y))


def reliability_bins(
    y: np.ndarray,
    p: np.ndarray,
    n_bins: int = 15,
) -> dict:
    """Data for a reliability diagram (not a plotted figure)."""
    y = np.asarray(y, dtype=int)
    p = _as_proba(p)
    conf = p.max(axis=1)
    pred = p.argmax(axis=1)
    correct = (pred == y).astype(np.float64)
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    bin_acc, bin_conf, bin_count = [], [], []
    for i in range(n_bins):
        lo, hi = edges[i], edges[i + 1]
        mask = (conf >= lo) & (conf <= hi) if i == n_bins - 1 else (conf >= lo) & (conf < hi)
        bin_count.append(int(mask.sum()))
        if np.any(mask):
            bin_acc.append(float(correct[mask].mean()))
            bin_conf.append(float(conf[mask].mean()))
        else:
            bin_acc.append(None)
            bin_conf.append(None)
    return {
        "edges": edges.tolist(),
        "bin_acc": bin_acc,
        "bin_conf": bin_conf,
        "bin_count": bin_count,
    }
