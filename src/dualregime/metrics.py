"""Decision metrics: FCAR, utility, coverage-of-safety. ECE is secondary."""

from __future__ import annotations

import numpy as np

ACT = "act"
DEFER = "defer"
ABORT = "abort"

DEFAULT_COSTS = {
    "u_correct_act": 1.0,
    "u_wrong_act": -10.0,
    "u_defer": -0.2,
    "u_abort": -0.5,
}


def decision_summary(
    y: np.ndarray,
    action: np.ndarray,
    p_used: np.ndarray | None = None,
    tau_act: float = 0.8,
    costs: dict | None = None,
    C_covers: np.ndarray | None = None,
) -> dict:
    """y is true seating (1=would insert). action in {act, defer, abort}.

    Acting means INSERT. yhat is therefore 1 on acts.
    """
    costs = {**DEFAULT_COSTS, **(costs or {})}
    y = np.asarray(y, dtype=int)
    action = np.asarray(action, dtype=object)
    n = len(y)
    is_act = action == ACT
    is_defer = action == DEFER
    is_abort = action == ABORT
    if p_used is None:
        p_used = np.where(is_act, 1.0, 0.5).astype(np.float64)
    else:
        p_used = np.asarray(p_used, dtype=np.float64)
    conf = p_used
    false_conf = is_act & (y == 0) & (conf >= tau_act)
    unsafe = is_act & (y == 0)
    true_act = is_act & (y == 1)
    u = np.zeros(n, dtype=np.float64)
    u[true_act] = costs["u_correct_act"]
    u[unsafe] = costs["u_wrong_act"]
    u[is_defer] = costs["u_defer"]
    u[is_abort] = costs["u_abort"]
    if C_covers is None:
        # Abort covers by refusing; defer/act cover iff we did not take a wrong act.
        C_covers = is_abort | ~unsafe
    else:
        C_covers = np.asarray(C_covers, dtype=bool)
    n_act = int(is_act.sum())
    return {
        "n": n,
        "n_act": n_act,
        "n_defer": int(is_defer.sum()),
        "n_abort": int(is_abort.sum()),
        "act_rate": float(is_act.mean()),
        "defer_rate": float(is_defer.mean()),
        "abort_rate": float(is_abort.mean()),
        "false_confident_act": int(false_conf.sum()),
        "false_confident_act_rate": float(false_conf.mean()),
        "false_confident_rate": float(false_conf.mean()),
        "unsafe_act_rate": float(unsafe.mean()),
        "precision_among_acts": float(true_act.sum() / max(n_act, 1)),
        "recall_success": float(true_act.sum() / max(int((y == 1).sum()), 1)),
        "mean_utility": float(u.mean()),
        "utility": float(u.sum()),
        "safety_coverage": float(C_covers.mean()),
        "tau_act": float(tau_act),
        "u_wrong_act": float(costs["u_wrong_act"]),
    }
