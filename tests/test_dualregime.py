"""Tests for the dual-regime grasp stack (no fabrication; local physics)."""

from __future__ import annotations

import numpy as np

from dualregime.detector import REGIME_IID, REGIME_PERTURB, REGIME_SELECT, RegimeDetector
from dualregime.metrics import decision_summary
from dualregime.policies import fit_policy
from dualregime.world import generate_batch
from calibshift.models import get_model


def test_perturbation_raises_residual_selection_does_not():
    rng = np.random.default_rng(0)
    X_iid, y_iid, _ = generate_batch(400, rng)
    X_pert, _, _ = generate_batch(400, rng, enc_bias=(0.45, 0.0, 0.0), motor_bias=0.5)
    X_sel, _, _ = generate_batch(400, rng, gx_lo=0.65, gx_hi=1.15)
    det = RegimeDetector().fit(X_iid)
    r_iid = det.pose_residual(X_iid).mean()
    r_pert = det.pose_residual(X_pert).mean()
    r_sel = det.pose_residual(X_sel).mean()
    assert r_pert > 3 * r_iid
    assert r_sel < 2 * r_iid
    assert y_iid.mean() > 0.15


def test_detector_separates_regimes():
    rng = np.random.default_rng(1)
    X_iid, _, _ = generate_batch(500, rng, gx_lo=-0.05, gx_hi=0.55)
    X_pert, _, _ = generate_batch(300, rng, enc_bias=(0.5, 0.1, 0.2), motor_bias=0.6)
    X_sel, _, _ = generate_batch(300, rng, gx_lo=0.72, gx_hi=1.15)
    det = RegimeDetector(resid_q=0.98, support_q=0.10).fit(X_iid)
    p_pert = det.predict(X_pert)
    p_sel = det.predict(X_sel)
    p_iid = det.predict(X_iid)
    assert (p_pert == REGIME_PERTURB).mean() >= 0.8
    assert (p_sel == REGIME_SELECT).mean() >= 0.6
    assert (p_iid == REGIME_IID).mean() >= 0.7
    # Selection must not be called perturbation just because location moved.
    assert (p_sel == REGIME_PERTURB).mean() < 0.2


def test_channel_switch_beats_always_iid_under_perturbation():
    rng = np.random.default_rng(2)
    X_tr, y_tr, _ = generate_batch(700, rng)
    X_cal, y_cal, _ = generate_batch(400, rng)
    X_te, y_te, _ = generate_batch(400, rng, enc_bias=(0.55, 0.0, 0.15), motor_bias=0.7)
    pol = fit_policy(
        X_tr,
        y_tr,
        X_cal,
        y_cal,
        get_model("hgb", seed=2),
        get_model("hgb", seed=3),
        alpha=0.1,
    )
    routed = pol.act(X_te, mode="router")
    blindly = pol.act(X_te, mode="always_iid")
    u_r = decision_summary(y_te, routed["act"])
    u_b = decision_summary(y_te, blindly["act"])
    # Channel-switch should recover successful acts instead of aborting
    # everyone after the encoder is biased.
    assert u_r["utility"] > u_b["utility"]
    assert u_r["recall_success"] >= 0.5
    assert u_r["precision_among_acts"] >= 0.7


def test_decision_summary_identity():
    y = np.array([1, 1, 0, 0])
    act = np.array([True, False, True, False])
    s = decision_summary(y, act, cost_fail=8.0, reward_success=1.0)
    assert s["false_confident_act"] == 1
    assert s["missed_success"] == 1
    assert s["utility"] == 1.0 - 8.0
