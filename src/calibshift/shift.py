"""Covariate-shift mechanisms that change P(X) without relabeling.

All methods return (X_out, y_out, meta). Labels are never shuffled.
"""

from __future__ import annotations

import numpy as np


def gaussian_feature_shift(
    X: np.ndarray,
    y: np.ndarray,
    rng: np.random.Generator,
    strength: float,
    n_features: int | None = None,
    cols: list[int] | None = None,
) -> tuple[np.ndarray, np.ndarray, dict]:
    """Add a mean shift to a subset of features (test-time only)."""
    X = np.asarray(X, dtype=np.float64).copy()
    d = X.shape[1]
    if cols is not None:
        cols = np.asarray(cols, dtype=int)
        cols = cols[(cols >= 0) & (cols < d)]
        if cols.size == 0:
            cols = np.array([0], dtype=int)
    else:
        k = d if n_features is None else min(n_features, d)
        cols = rng.choice(d, size=k, replace=False)
    scales = X.std(axis=0)
    scales = np.where(scales < 1e-8, 1.0, scales)
    X[:, cols] = X[:, cols] + strength * scales[cols]
    meta = {"kind": "gaussian_feature_shift", "strength": strength, "cols": cols.tolist()}
    return X, np.asarray(y), meta


def quantile_slice(
    X: np.ndarray,
    y: np.ndarray,
    feature_index: int,
    upper: bool,
    quantile: float = 0.5,
) -> tuple[np.ndarray, np.ndarray, dict]:
    """Keep examples on one side of a feature quantile (selection shift)."""
    X = np.asarray(X, dtype=np.float64)
    y = np.asarray(y)
    thresh = np.quantile(X[:, feature_index], quantile)
    mask = X[:, feature_index] >= thresh if upper else X[:, feature_index] < thresh
    if mask.sum() < 10:
        mask = np.ones(len(X), dtype=bool)
    meta = {
        "kind": "quantile_slice",
        "feature_index": int(feature_index),
        "upper": bool(upper),
        "quantile": float(quantile),
        "kept": int(mask.sum()),
    }
    return X[mask], y[mask], meta


def importance_resample(
    X: np.ndarray,
    y: np.ndarray,
    rng: np.random.Generator,
    feature_index: int,
    tilt: float,
    size: int | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
    """Resample with weights exp(tilt * z_j) on a standardized feature.

    Returns X, y, weights_of_drawn (unnormalized original weights), meta.
    """
    X = np.asarray(X, dtype=np.float64)
    y = np.asarray(y)
    z = (X[:, feature_index] - X[:, feature_index].mean()) / (X[:, feature_index].std() + 1e-8)
    w = np.exp(tilt * z)
    w = w / w.sum()
    n = len(X) if size is None else size
    idx = rng.choice(len(X), size=n, replace=True, p=w)
    meta = {
        "kind": "importance_resample",
        "feature_index": int(feature_index),
        "tilt": float(tilt),
        "size": int(n),
    }
    return X[idx], y[idx], w[idx], meta


def oracle_density_ratio_1d(
    x_source: np.ndarray,
    x_target: np.ndarray,
    bins: int = 20,
) -> np.ndarray:
    """Histogram density-ratio w(x) = p_target(x) / p_source(x) on 1D scores."""
    x_source = np.asarray(x_source, dtype=np.float64)
    x_target = np.asarray(x_target, dtype=np.float64)
    lo = min(x_source.min(), x_target.min())
    hi = max(x_source.max(), x_target.max())
    edges = np.linspace(lo, hi, bins + 1)
    hs, _ = np.histogram(x_source, bins=edges, density=True)
    ht, _ = np.histogram(x_target, bins=edges, density=True)
    ratio = ht / np.clip(hs, 1e-8, None)
    idx = np.digitize(x_source, edges[1:-1], right=False)
    idx = np.clip(idx, 0, bins - 1)
    return ratio[idx]
