"""Opposite legal moves for i.i.d. / selection / perturbation.

i.i.d.: source T + unweighted LAC → act / defer. Never abort.
selection: same T + multivariate density-ratio conformal → act / defer.
          Never abort-as-sensor-fault. Never project-as-if-encoder-lied.
perturbation: MUST NOT apply source T to raw encoder probabilities.
          Project encoder onto camera pose, then T_iid(p(x_hat));
          abort if residual is huge. Never Tibshirani-weight the encoder.

Ablation modes isolate those constraints.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.base import BaseEstimator

from calibshift.calibrators import TemperatureCalibrator
from calibshift.conformal import split_conformal_quantile, weighted_conformal_quantile

from .density import DensityRatioResult, fit_density_ratio_mv
from .detector import REGIME_IID, REGIME_PERTURB, REGIME_SELECT, RegimeDetector, physics_residual
from .metrics import ABORT, ACT, DEFER
from .world import DEPLOY_IDX, project_encoder_to_camera


def _p_success_raw(model: BaseEstimator, X: np.ndarray) -> np.ndarray:
    p = np.asarray(model.predict_proba(X[:, DEPLOY_IDX]), dtype=np.float64)
    classes = list(model.classes_)
    if 1 in classes:
        return p[:, classes.index(1)]
    return np.zeros(len(X))


def _mapped_p(cal: TemperatureCalibrator, p1: np.ndarray) -> np.ndarray:
    p = cal.transform(np.column_stack([1.0 - p1, p1]))
    return p[:, 1]


def _singleton_success(p1: np.ndarray, q_hat: float, tau_act: float) -> np.ndarray:
    """LAC set is {success} iff p_success >= 1-q and p_fail < 1-q, plus tau."""
    p1 = np.asarray(p1, dtype=np.float64)
    include_pos = p1 >= (1.0 - q_hat)
    include_neg = (1.0 - p1) >= (1.0 - q_hat)
    singleton_pos = include_pos & (~include_neg)
    return singleton_pos & (p1 >= tau_act)


@dataclass
class DualRegimePolicy:
    detector: RegimeDetector
    model: BaseEstimator
    cal: TemperatureCalibrator
    q_iid: float
    tau_act: float = 0.8
    alpha: float = 0.1
    X_cal: np.ndarray | None = None
    y_cal: np.ndarray | None = None
    p_cal_mapped: np.ndarray | None = None

    def p_mapped(self, X: np.ndarray) -> np.ndarray:
        return _mapped_p(self.cal, _p_success_raw(self.model, X))

    def _selection_q(self, X_target: np.ndarray) -> tuple[float, DensityRatioResult | None]:
        if self.X_cal is None or self.p_cal_mapped is None or self.y_cal is None:
            return self.q_iid, None
        dr = fit_density_ratio_mv(self.X_cal, X_target, seed=0)
        if dr.unreliable or dr.domain_auc < 0.55:
            return self.q_iid, dr
        q_w = weighted_conformal_quantile(self.y_cal, self.p_cal_mapped, dr.w_cal, alpha=self.alpha)
        return float(q_w), dr

    def act(
        self,
        X: np.ndarray,
        mode: str = "router",
        regimes: np.ndarray | None = None,
        stream: bool = False,
    ) -> dict:
        """Modes: router, detector_off, always_abort, illegal_T,
        denoise_off, oracle, always_project.
        """
        X = np.asarray(X, dtype=np.float64)
        n = len(X)
        X_hat = project_encoder_to_camera(X)
        resid = physics_residual(X)
        p_raw = self.p_mapped(X)
        p_proj = self.p_mapped(X_hat)

        if mode == "always_abort":
            action = np.full(n, ABORT, dtype=object)
            return {
                "action": action,
                "act": np.zeros(n, dtype=bool),
                "regime": np.full(n, REGIME_PERTURB, dtype=object),
                "p_used": np.full(n, 0.5),
                "path": np.full(n, "abort", dtype=object),
            }

        if mode == "oracle":
            if regimes is None:
                raise ValueError("oracle mode needs true regimes")
            pred = np.asarray(regimes, dtype=object)
        elif mode in {"detector_off", "always_iid"}:
            pred = np.full(n, REGIME_IID, dtype=object)
        elif mode == "always_project":
            pred = np.full(n, REGIME_PERTURB, dtype=object)
        elif mode == "illegal_T":
            # Force perturbation DGP handling with the *illegal* map.
            pred = np.full(n, REGIME_PERTURB, dtype=object)
        elif mode == "denoise_off":
            pred = (
                self.detector.predict_stream(X, p_fn=self.p_mapped)
                if stream
                else self.detector.predict(X, p_fn=self.p_mapped)
            )
        else:
            pred = (
                self.detector.predict_stream(X, p_fn=self.p_mapped)
                if stream
                else self.detector.predict(X, p_fn=self.p_mapped)
            )

        q_sel, dr = self._selection_q(X)
        action = np.full(n, DEFER, dtype=object)
        p_used = np.array(p_raw, copy=True)
        path = np.full(n, "iid_T_raw", dtype=object)
        covers = np.ones(n, dtype=bool)

        for i in range(n):
            r = pred[i]
            if mode == "illegal_T":
                # Negative control: source T on raw corrupted p, no project, no abort.
                p_used[i] = p_raw[i]
                path[i] = "illegal_T_raw"
                if _singleton_success(p_raw[i : i + 1], self.q_iid, self.tau_act)[0]:
                    action[i] = ACT
                    covers[i] = True
                else:
                    action[i] = DEFER
                continue

            if mode == "always_project" or (r == REGIME_PERTURB and mode != "detector_off"):
                if mode == "denoise_off" or (
                    mode == "router" and resid[i] > self.detector.t_abort
                ):
                    action[i] = ABORT
                    p_used[i] = 0.5
                    path[i] = "abort"
                    covers[i] = True
                    continue
                # Legal perturbation: T_iid on projected (camera) pose.
                p_used[i] = p_proj[i]
                path[i] = "project_then_T"
                if _singleton_success(p_proj[i : i + 1], self.q_iid, self.tau_act)[0]:
                    action[i] = ACT
                else:
                    action[i] = DEFER
                continue

            if r == REGIME_SELECT and mode in {"router", "oracle", "denoise_off"}:
                p_used[i] = p_raw[i]
                path[i] = "select_weighted"
                q_use = q_sel
                if _singleton_success(p_raw[i : i + 1], q_use, self.tau_act)[0]:
                    action[i] = ACT
                else:
                    action[i] = DEFER
                # Never abort on selection.
                continue

            # i.i.d. (and detector_off / always_iid on every row)
            p_used[i] = p_raw[i]
            path[i] = "iid_T_raw"
            if _singleton_success(p_raw[i : i + 1], self.q_iid, self.tau_act)[0]:
                action[i] = ACT
            else:
                action[i] = DEFER

        return {
            "action": action,
            "act": action == ACT,
            "regime": pred,
            "p_used": p_used,
            "p_raw": p_raw,
            "p_proj": p_proj,
            "path": path,
            "resid": resid,
            "q_sel": q_sel,
            "domain_auc": None if dr is None else dr.domain_auc,
            "C_covers": covers,
        }


def fit_policy(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_cal: np.ndarray,
    y_cal: np.ndarray,
    model: BaseEstimator,
    alpha: float = 0.1,
    tau_act: float = 0.8,
) -> DualRegimePolicy:
    model.fit(X_train[:, DEPLOY_IDX], y_train)
    cal = TemperatureCalibrator().fit(model.predict_proba(X_cal[:, DEPLOY_IDX]), y_cal)
    p1_cal = _mapped_p(cal, _p_success_raw(model, X_cal))
    p2_cal = np.column_stack([1.0 - p1_cal, p1_cal])
    q_iid = split_conformal_quantile(y_cal, p2_cal, alpha=alpha)

    pol = DualRegimePolicy(
        detector=RegimeDetector(),
        model=model,
        cal=cal,
        q_iid=q_iid,
        tau_act=tau_act,
        alpha=alpha,
        X_cal=np.asarray(X_cal, dtype=np.float64),
        y_cal=np.asarray(y_cal, dtype=int),
        p_cal_mapped=p2_cal,
    )
    pol.detector.fit(X_cal, p_fn=pol.p_mapped)
    return pol
