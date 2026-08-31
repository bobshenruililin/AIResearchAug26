"""Regime detector: residual (sensor disagreement) vs support (workspace slice).

A single ||x - mu|| threshold cannot separate the two regimes: selection
moves location but encoder and camera still agree; perturbation keeps
location but they disagree. That disagreement is the structure.
"""

from __future__ import annotations

import numpy as np

from .world import (
    CAM_X,
    CAM_Y,
    CAM_YAW,
    ENC_X,
    ENC_Y,
    ENC_YAW,
    FORCE_GAUGE,
    FORCE_MOTOR,
)

REGIME_IID = "iid"
REGIME_PERTURB = "perturb"
REGIME_SELECT = "select"


class RegimeDetector:
    def __init__(self, resid_q: float = 0.99, support_q: float = 0.08):
        self.resid_q = float(resid_q)
        self.support_q = float(support_q)
        self.resid_thresh: float = 0.0
        self.support_mean: np.ndarray | None = None
        self.support_std: np.ndarray | None = None
        self.support_thresh: float = 0.0

    @staticmethod
    def pose_residual(X: np.ndarray) -> np.ndarray:
        X = np.asarray(X, dtype=np.float64)
        dxy = np.hypot(X[:, ENC_X] - X[:, CAM_X], X[:, ENC_Y] - X[:, CAM_Y])
        dyaw = np.abs(X[:, ENC_YAW] - X[:, CAM_YAW])
        dforce = np.abs(X[:, FORCE_MOTOR] - X[:, FORCE_GAUGE])
        return dxy + dyaw + dforce

    @staticmethod
    def cam_xy(X: np.ndarray) -> np.ndarray:
        return np.asarray(X, dtype=np.float64)[:, [CAM_X, CAM_Y]]

    def fit(self, X_iid: np.ndarray) -> "RegimeDetector":
        X_iid = np.asarray(X_iid, dtype=np.float64)
        r = self.pose_residual(X_iid)
        self.resid_thresh = float(np.quantile(r, self.resid_q))
        loc = self.cam_xy(X_iid)
        self.support_mean = loc.mean(axis=0)
        self.support_std = loc.std(axis=0) + 1e-8
        z = np.abs((loc - self.support_mean) / self.support_std).max(axis=1)
        # Low support score = in-distribution; high = away from train cam location.
        self.support_thresh = float(np.quantile(z, 1.0 - self.support_q))
        return self

    def support_z(self, X: np.ndarray) -> np.ndarray:
        loc = self.cam_xy(X)
        assert self.support_mean is not None and self.support_std is not None
        return np.abs((loc - self.support_mean) / self.support_std).max(axis=1)

    def predict(self, X: np.ndarray) -> np.ndarray:
        X = np.asarray(X, dtype=np.float64)
        r = self.pose_residual(X)
        z = self.support_z(X)
        out = np.full(len(X), REGIME_IID, dtype=object)
        # Perturbation wins if sensors disagree, even if location looks familiar.
        perturb = r > self.resid_thresh
        select = (~perturb) & (z > self.support_thresh)
        out[perturb] = REGIME_PERTURB
        out[select] = REGIME_SELECT
        return out
