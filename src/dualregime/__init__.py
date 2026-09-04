"""Dual-regime insert/abort: sensor perturbation vs workspace selection.

Identifying claim: frozen-label encoder perturbation breaks P(Y|X) at
the observed pose; pairing-preserving fixture selection does not. Those
regimes need opposite legal moves, not a shared i.i.d. temperature on
raw encoder probabilities.

Honesty: planar peg-in-hole kinematic cartoon, not a robot.
"""

from .detector import REGIME_IID, REGIME_PERTURB, REGIME_SELECT, RegimeDetector, physics_residual
from .metrics import ABORT, ACT, DEFER, decision_summary
from .policies import DualRegimePolicy, fit_policy
from .world import (
    CAM_IDX,
    COLS,
    DEPLOY_IDX,
    ENC_IDX,
    PegWorld,
    generate_batch,
    project_encoder_to_camera,
)

__all__ = [
    "ABORT",
    "ACT",
    "CAM_IDX",
    "COLS",
    "DEFER",
    "DEPLOY_IDX",
    "ENC_IDX",
    "DualRegimePolicy",
    "PegWorld",
    "REGIME_IID",
    "REGIME_PERTURB",
    "REGIME_SELECT",
    "RegimeDetector",
    "decision_summary",
    "fit_policy",
    "generate_batch",
    "physics_residual",
    "project_encoder_to_camera",
]
