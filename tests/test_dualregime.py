"""Tests for the dual-regime peg-in-hole stack."""

from __future__ import annotations

import numpy as np
from sklearn.decomposition import PCA

from calibshift.models import get_model
from dualregime.detector import (
    REGIME_IID,
    REGIME_PERTURB,
    REGIME_SELECT,
    RegimeDetector,
    physics_residual,
)
from dualregime.metrics import ABORT, ACT, DEFER, decision_summary
from dualregime.policies import fit_policy
from dualregime.world import DEPLOY_IDX, ENC_XY_IDX, generate_batch, project_encoder_to_camera


def test_perturbation_raises_physics_residual_selection_does_not():
    rng = np.random.default_rng(0)
    X_iid, y_iid, _ = generate_batch(500, rng)
    X_pert, _, _ = generate_batch(500, rng, enc_xy_scale=0.40)
    X_sel, _, meta_s = generate_batch(500, rng, x_lo=0.0)
    r_iid = physics_residual(X_iid).mean()
    r_pert = physics_residual(X_pert).mean()
    r_sel = physics_residual(X_sel).mean()
    assert r_pert > 3 * r_iid
    assert r_sel < 2 * r_iid
    assert y_iid.mean() > 0.25
    X_sel2, y_sel, _ = generate_batch(800, rng, x_lo=0.0)
    _, y_iid2, _ = generate_batch(800, rng)
    assert abs(float(y_sel.mean()) - float(y_iid2.mean())) < 0.12
    assert meta_s["x_mean"] > 0.05


def test_pca_residual_misses_optimistic_encoder():
    """Near-origin poses are on the train manifold; PCA is the wrong channel."""
    rng = np.random.default_rng(4)
    X_iid, _, _ = generate_batch(600, rng)
    X_pert, _, _ = generate_batch(400, rng, enc_xy_scale=0.40)
    pca = PCA(n_components=1, random_state=0).fit(X_iid[:, ENC_XY_IDX])

    def resid(X):
        enc = X[:, ENC_XY_IDX]
        hat = pca.inverse_transform(pca.transform(enc))
        return float(np.linalg.norm(enc - hat, axis=1).mean())

    assert physics_residual(X_pert).mean() > 3 * physics_residual(X_iid).mean()
    # Optimistic encoder is *more* in-support for PCA; residual must not rise.
    assert resid(X_pert) <= resid(X_iid) * 1.05


def test_detector_separates_regimes():
    rng = np.random.default_rng(1)
    X_iid, _, _ = generate_batch(600, rng)
    X_pert, _, _ = generate_batch(300, rng, enc_xy_scale=0.40)
    X_sel, _, _ = generate_batch(300, rng, x_lo=0.0)
    det = RegimeDetector().fit(X_iid)
    p_pert = det.predict(X_pert, use_batch=True)
    p_sel = det.predict(X_sel, use_batch=True)
    p_iid = det.predict(X_iid, use_batch=True)
    assert (p_pert == REGIME_PERTURB).mean() >= 0.8
    assert (p_sel == REGIME_SELECT).mean() >= 0.6
    assert (p_iid == REGIME_IID).mean() >= 0.55
    assert (p_sel == REGIME_PERTURB).mean() < 0.15


def test_projection_recovers_pose_for_the_same_model():
    rng = np.random.default_rng(2)
    X_tr, y_tr, _ = generate_batch(700, rng)
    X_te, y_te, _ = generate_batch(400, rng, enc_xy_scale=0.40)
    model = get_model("hgb", seed=2)
    model.fit(X_tr[:, DEPLOY_IDX], y_tr)
    acc_raw = float((model.predict(X_te[:, DEPLOY_IDX]) == y_te).mean())
    Xp = project_encoder_to_camera(X_te)
    acc_proj = float((model.predict(Xp[:, DEPLOY_IDX]) == y_te).mean())
    assert acc_proj > acc_raw + 0.15
    assert acc_proj >= 0.80


def test_router_beats_illegal_T_and_abort_under_perturbation():
    rng = np.random.default_rng(3)
    X_tr, y_tr, _ = generate_batch(700, rng)
    X_cal, y_cal, _ = generate_batch(400, rng)
    X_te, y_te, _ = generate_batch(400, rng, enc_xy_scale=0.40)
    pol = fit_policy(X_tr, y_tr, X_cal, y_cal, get_model("hgb", seed=3), alpha=0.1)
    routed = pol.act(X_te, mode="router")
    illegal = pol.act(X_te, mode="illegal_T")
    abort = pol.act(X_te, mode="always_abort")
    u_r = decision_summary(y_te, routed["action"], routed["p_used"])
    u_i = decision_summary(y_te, illegal["action"], illegal["p_used"])
    u_a = decision_summary(y_te, abort["action"], abort["p_used"])
    assert u_r["mean_utility"] > u_i["mean_utility"]
    assert u_r["mean_utility"] > u_a["mean_utility"]
    assert u_r["false_confident_act_rate"] < u_i["false_confident_act_rate"] - 0.05
    assert u_r["act_rate"] > 0.15
    assert u_r["abort_rate"] < 0.5


def test_selection_never_aborts_as_sensor_fault():
    rng = np.random.default_rng(5)
    X_tr, y_tr, _ = generate_batch(700, rng)
    X_cal, y_cal, _ = generate_batch(400, rng)
    X_sel, y_sel, _ = generate_batch(400, rng, x_lo=0.0)
    pol = fit_policy(X_tr, y_tr, X_cal, y_cal, get_model("hgb", seed=5), alpha=0.1)
    out = pol.act(X_sel, mode="router")
    u = decision_summary(y_sel, out["action"], out["p_used"])
    assert u["abort_rate"] < 0.05
    assert (out["regime"] == REGIME_PERTURB).mean() < 0.2
    assert u["act_rate"] > 0.10


def test_stream_rolling_window_does_not_contaminate_iid_block():
    rng = np.random.default_rng(6)
    X_tr, y_tr, _ = generate_batch(500, rng)
    X_cal, y_cal, _ = generate_batch(300, rng)
    pol = fit_policy(X_tr, y_tr, X_cal, y_cal, get_model("hgb", seed=6), alpha=0.1)
    n = 80
    X_i, _, _ = generate_batch(n, rng)
    X_s, _, _ = generate_batch(n, rng, x_lo=0.0)
    X_p, _, _ = generate_batch(n, rng, enc_xy_scale=0.40)
    X = np.vstack([X_i, X_s, X_p])
    out = pol.act(X, mode="router", stream=True)
    iid_r = out["regime"][:n]
    sel_r = out["regime"][n : 2 * n]
    per_r = out["regime"][2 * n :]
    assert (iid_r == REGIME_PERTURB).mean() < 0.2
    assert (sel_r == REGIME_PERTURB).mean() < 0.25
    assert (per_r == REGIME_PERTURB).mean() >= 0.5
    assert (out["path"][2 * n :] == "project_then_T").mean() >= 0.4


def test_decision_summary_identity():
    y = np.array([1, 1, 0, 0])
    action = np.array([ACT, DEFER, ACT, ABORT], dtype=object)
    p = np.array([0.9, 0.4, 0.95, 0.5])
    s = decision_summary(y, action, p, tau_act=0.8)
    assert s["false_confident_act"] == 1
    assert s["n_defer"] == 1
    assert s["n_abort"] == 1
    assert abs(s["mean_utility"] - (1.0 - 0.2 + (-10.0) + (-0.5)) / 4) < 1e-9
