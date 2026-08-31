"""Dual-regime act/abort stack: sensor perturbation vs selection.

The structure is a regime detector plus two different policies.
Perturbation path switches to redundant (camera / gauge) channels.
Selection path keeps the i.i.d. calibrator. That is not a single
OOD-threshold abort.
"""

from .detector import RegimeDetector, REGIME_IID, REGIME_PERTURB, REGIME_SELECT
from .policies import DualRegimePolicy
from .world import CLEAN_IDX, COLS, DEPLOY_IDX, GraspWorld, generate_batch

__all__ = [
    "COLS",
    "CLEAN_IDX",
    "DEPLOY_IDX",
    "GraspWorld",
    "generate_batch",
    "RegimeDetector",
    "REGIME_IID",
    "REGIME_PERTURB",
    "REGIME_SELECT",
    "DualRegimePolicy",
]
