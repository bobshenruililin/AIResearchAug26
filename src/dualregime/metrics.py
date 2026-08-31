"""Decision metrics: false-confident acts and utility, not ECE-only."""

from __future__ import annotations

import numpy as np


def decision_summary(
    y: np.ndarray,
    act: np.ndarray,
    cost_fail: float = 8.0,
    reward_success: float = 1.0,
) -> dict:
    y = np.asarray(y, dtype=int)
    act = np.asarray(act, dtype=bool)
    n = len(y)
    n_act = int(act.sum())
    n_abort = int((~act).sum())
    false_conf = int((act & (y == 0)).sum())
    true_act = int((act & (y == 1)).sum())
    missed = int((~act & (y == 1)).sum())
    utility = reward_success * true_act - cost_fail * false_conf
    return {
        "n": n,
        "n_act": n_act,
        "n_abort": n_abort,
        "false_confident_act": false_conf,
        "false_confident_rate": float(false_conf / max(n, 1)),
        "precision_among_acts": float(true_act / max(n_act, 1)),
        "recall_success": float(true_act / max(int((y == 1).sum()), 1)),
        "missed_success": missed,
        "utility": float(utility),
        "utility_per_episode": float(utility / max(n, 1)),
    }
