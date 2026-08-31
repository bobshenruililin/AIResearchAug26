"""Decision policies: i.i.d. conformal vs channel-switch under perturbation.

Selection keeps the source calibrator. Perturbation ignores encoder/motor
and uses a backup model trained only on camera+gauge. Both can abort.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.base import BaseEstimator

from calibshift.calibrators import TemperatureCalibrator
from calibshift.conformal import split_conformal_quantile

from .detector import REGIME_IID, REGIME_PERTURB, REGIME_SELECT, RegimeDetector
from .world import CLEAN_IDX, DEPLOY_IDX


def _p_success(model: BaseEstimator, X: np.ndarray) -> np.ndarray:
    p = np.asarray(model.predict_proba(X), dtype=np.float64)
    classes = list(model.classes_)
    if 1 in classes:
        return p[:, classes.index(1)]
    return np.zeros(len(X))


@dataclass
class DualRegimePolicy:
    """Act if the routed policy says success is in the conformal set."""

    detector: RegimeDetector
    model_full: BaseEstimator
    model_clean: BaseEstimator
    cal_full: TemperatureCalibrator
    cal_clean: TemperatureCalibrator
    q_full: float
    q_clean: float
    t_full: float
    t_clean: float
    abort_on_huge_resid: bool = False
    huge_resid_mult: float = 3.0

    def p_full(self, X: np.ndarray) -> np.ndarray:
        p1 = _p_success(self.model_full, X[:, DEPLOY_IDX])
        p = self.cal_full.transform(np.column_stack([1.0 - p1, p1]))
        return p[:, 1]

    def p_clean(self, X: np.ndarray) -> np.ndarray:
        p1 = _p_success(self.model_clean, X[:, CLEAN_IDX])
        p = self.cal_clean.transform(np.column_stack([1.0 - p1, p1]))
        return p[:, 1]

    def act(
        self,
        X: np.ndarray,
        mode: str = "router",
        regimes: np.ndarray | None = None,
    ) -> dict:
        """mode: router | always_iid | always_clean | always_abort | oracle

        oracle requires `regimes` with true labels {iid,perturb,select}.
        """
        X = np.asarray(X, dtype=np.float64)
        n = len(X)
        if mode == "always_abort":
            return {
                "act": np.zeros(n, dtype=bool),
                "regime": np.array([REGIME_PERTURB] * n, dtype=object),
            }
        if mode == "oracle":
            if regimes is None:
                raise ValueError("oracle mode needs true regimes")
            pred = np.asarray(regimes, dtype=object)
        elif mode == "always_iid":
            pred = np.full(n, REGIME_IID, dtype=object)
        elif mode == "always_clean":
            pred = np.full(n, REGIME_PERTURB, dtype=object)
        else:
            pred = self.detector.predict(X)

        s_full = self.p_full(X)
        s_clean = self.p_clean(X)
        resid = self.detector.pose_residual(X)
        act = np.zeros(n, dtype=bool)
        for i in range(n):
            r = pred[i]
            if r == REGIME_PERTURB:
                if self.abort_on_huge_resid and resid[i] > self.huge_resid_mult * self.detector.resid_thresh:
                    act[i] = False
                else:
                    act[i] = s_clean[i] >= self.t_clean
            else:
                act[i] = s_full[i] >= self.t_full
        return {"act": act, "regime": pred, "p_full": s_full, "p_clean": s_clean}


def fit_policy(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_cal: np.ndarray,
    y_cal: np.ndarray,
    model_full: BaseEstimator,
    model_clean: BaseEstimator,
    alpha: float = 0.1,
) -> DualRegimePolicy:
    model_full.fit(X_train[:, DEPLOY_IDX], y_train)
    model_clean.fit(X_train[:, CLEAN_IDX], y_train)
    det = RegimeDetector().fit(X_cal)
    cal_full = TemperatureCalibrator().fit(model_full.predict_proba(X_cal[:, DEPLOY_IDX]), y_cal)
    cal_clean = TemperatureCalibrator().fit(model_clean.predict_proba(X_cal[:, CLEAN_IDX]), y_cal)
    p_full = cal_full.transform(model_full.predict_proba(X_cal[:, DEPLOY_IDX]))[:, 1]
    p_clean = cal_clean.transform(model_clean.predict_proba(X_cal[:, CLEAN_IDX]))[:, 1]
    yb = np.asarray(y_cal, dtype=int)
    neg = yb == 0
    t_full = float(np.quantile(p_full[neg], 1.0 - alpha)) if neg.any() else 0.5
    t_clean = float(np.quantile(p_clean[neg], 1.0 - alpha)) if neg.any() else 0.5
    p2_full = cal_full.transform(model_full.predict_proba(X_cal[:, DEPLOY_IDX]))
    p2_clean = cal_clean.transform(model_clean.predict_proba(X_cal[:, CLEAN_IDX]))
    q_full = split_conformal_quantile(y_cal, p2_full, alpha=alpha)
    q_clean = split_conformal_quantile(y_cal, p2_clean, alpha=alpha)
    return DualRegimePolicy(
        detector=det,
        model_full=model_full,
        model_clean=model_clean,
        cal_full=cal_full,
        cal_clean=cal_clean,
        q_full=q_full,
        q_clean=q_clean,
        t_full=t_full,
        t_clean=t_clean,
    )
