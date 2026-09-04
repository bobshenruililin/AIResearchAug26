"""Post-hoc calibrators fitted on a frozen model's validation probabilities.

Temperature scaling uses a single scalar T on log-probabilities
(softmax(log p / T)), fitted by NLL (Guo et al. 2017 style, adapted to
probability outputs so tree models without logits still work).

Isotonic regression is fitted per positive-class probability for binary
tasks, or as a single isotonic map on confidence for multiclass (a
deliberately simple baseline; we do not claim it is the best multiclass
isotonic method).

Histogram binning follows Zadrozny-style equal-width bins on the
positive-class probability (binary) or confidence (multiclass).
"""

from __future__ import annotations

from typing import Protocol

import numpy as np
from scipy.optimize import minimize_scalar
from sklearn.isotonic import IsotonicRegression

from .metrics import negative_log_likelihood


def _as_proba(p: np.ndarray) -> np.ndarray:
    p = np.asarray(p, dtype=np.float64)
    if p.ndim == 1:
        p = np.clip(p, 0.0, 1.0)
        return np.column_stack([1.0 - p, p])
    p = np.clip(p, 1e-12, 1.0)
    p = p / p.sum(axis=1, keepdims=True)
    return p


def _softmax_from_logp(logp: np.ndarray, temperature: float) -> np.ndarray:
    z = logp / max(temperature, 1e-6)
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


class Calibrator(Protocol):
    name: str

    def fit(self, p: np.ndarray, y: np.ndarray) -> "Calibrator": ...

    def transform(self, p: np.ndarray) -> np.ndarray: ...


class IdentityCalibrator:
    name = "none"

    def fit(self, p: np.ndarray, y: np.ndarray) -> "IdentityCalibrator":
        return self

    def transform(self, p: np.ndarray) -> np.ndarray:
        return _as_proba(p)


class TemperatureCalibrator:
    name = "temperature"

    def __init__(self) -> None:
        self.T: float = 1.0

    def fit(self, p: np.ndarray, y: np.ndarray) -> "TemperatureCalibrator":
        p = _as_proba(p)
        y = np.asarray(y, dtype=int)
        logp = np.log(np.clip(p, 1e-12, 1.0))

        def nll(t: float) -> float:
            return negative_log_likelihood(y, _softmax_from_logp(logp, float(t)))

        result = minimize_scalar(nll, bounds=(0.05, 10.0), method="bounded")
        self.T = float(result.x)
        return self

    def transform(self, p: np.ndarray) -> np.ndarray:
        p = _as_proba(p)
        logp = np.log(np.clip(p, 1e-12, 1.0))
        return _softmax_from_logp(logp, self.T)


class IsotonicCalibrator:
    """Binary isotonic on p(y=1); multiclass: isotonic on confidence, then renormalize."""

    name = "isotonic"

    def __init__(self) -> None:
        self._iso: IsotonicRegression | None = None
        self._binary: bool = True
        self._n_classes: int = 2

    def fit(self, p: np.ndarray, y: np.ndarray) -> "IsotonicCalibrator":
        p = _as_proba(p)
        y = np.asarray(y, dtype=int)
        self._n_classes = p.shape[1]
        self._binary = self._n_classes == 2
        self._iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
        if self._binary:
            self._iso.fit(p[:, 1], y)
        else:
            conf = p.max(axis=1)
            correct = (p.argmax(axis=1) == y).astype(np.float64)
            self._iso.fit(conf, correct)
        return self

    def transform(self, p: np.ndarray) -> np.ndarray:
        if self._iso is None:
            raise RuntimeError("IsotonicCalibrator.fit must be called first")
        p = _as_proba(p)
        if self._binary:
            p1 = self._iso.predict(p[:, 1])
            p1 = np.clip(p1, 1e-12, 1.0 - 1e-12)
            return np.column_stack([1.0 - p1, p1])
        conf = p.max(axis=1)
        new_conf = np.clip(self._iso.predict(conf), 1e-12, 1.0 - 1e-12)
        pred = p.argmax(axis=1)
        out = np.full_like(p, (1.0 - new_conf)[:, None] / (p.shape[1] - 1))
        out[np.arange(len(p)), pred] = new_conf
        out = out / out.sum(axis=1, keepdims=True)
        return out


class HistogramBinningCalibrator:
    name = "histogram"

    def __init__(self, n_bins: int = 15) -> None:
        self.n_bins = n_bins
        self._bin_freq: np.ndarray | None = None
        self._edges: np.ndarray | None = None
        self._binary: bool = True

    def fit(self, p: np.ndarray, y: np.ndarray) -> "HistogramBinningCalibrator":
        p = _as_proba(p)
        y = np.asarray(y, dtype=int)
        self._binary = p.shape[1] == 2
        score = p[:, 1] if self._binary else p.max(axis=1)
        self._edges = np.linspace(0.0, 1.0, self.n_bins + 1)
        target = y.astype(np.float64) if self._binary else (p.argmax(axis=1) == y).astype(np.float64)
        freq = np.zeros(self.n_bins, dtype=np.float64)
        for i in range(self.n_bins):
            lo, hi = self._edges[i], self._edges[i + 1]
            mask = (score >= lo) & (score <= hi) if i == self.n_bins - 1 else (score >= lo) & (score < hi)
            freq[i] = target[mask].mean() if np.any(mask) else (lo + hi) / 2.0
        self._bin_freq = freq
        return self

    def transform(self, p: np.ndarray) -> np.ndarray:
        if self._bin_freq is None or self._edges is None:
            raise RuntimeError("HistogramBinningCalibrator.fit must be called first")
        p = _as_proba(p)
        score = p[:, 1] if self._binary else p.max(axis=1)
        idx = np.digitize(score, self._edges[1:-1], right=False)
        idx = np.clip(idx, 0, self.n_bins - 1)
        mapped = self._bin_freq[idx]
        mapped = np.clip(mapped, 1e-12, 1.0 - 1e-12)
        if self._binary:
            return np.column_stack([1.0 - mapped, mapped])
        pred = p.argmax(axis=1)
        out = np.full_like(p, (1.0 - mapped)[:, None] / (p.shape[1] - 1))
        out[np.arange(len(p)), pred] = mapped
        out = out / out.sum(axis=1, keepdims=True)
        return out


def get_calibrator(name: str, n_bins: int = 15) -> Calibrator:
    mapping = {
        "none": IdentityCalibrator,
        "temperature": TemperatureCalibrator,
        "isotonic": IsotonicCalibrator,
        "histogram": lambda: HistogramBinningCalibrator(n_bins=n_bins),
    }
    if name not in mapping:
        raise ValueError(f"Unknown calibrator: {name}")
    ctor = mapping[name]
    return ctor() if name != "histogram" else ctor()
