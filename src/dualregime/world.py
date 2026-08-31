"""Contact/grasp generative process with redundant sensors.

True success depends on workspace pose, yaw alignment, and force window.
Encoder and motor-current channels can be biased (perturbation) while
camera and force-gauge stay honest. Selection keeps (X, y) and restricts
the workspace. Labels always come from true physics, never from the
biased sensors.

This is a structural proxy for a robot, not a robot.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# Observation layout
ENC_X, ENC_Y, ENC_YAW = 0, 1, 2
CAM_X, CAM_Y, CAM_YAW = 3, 4, 5
FORCE_GAUGE, FORCE_MOTOR, APPEAR = 6, 7, 8
N_FEATURES = 9

COLS = {
    "enc_x": ENC_X,
    "enc_y": ENC_Y,
    "enc_yaw": ENC_YAW,
    "cam_x": CAM_X,
    "cam_y": CAM_Y,
    "cam_yaw": CAM_YAW,
    "force_gauge": FORCE_GAUGE,
    "force_motor": FORCE_MOTOR,
    "appearance": APPEAR,
}

CLEAN_IDX = np.array([CAM_X, CAM_Y, CAM_YAW, FORCE_GAUGE], dtype=int)
DEPLOY_IDX = np.array([ENC_X, ENC_Y, ENC_YAW, FORCE_MOTOR, APPEAR], dtype=int)
CORRUPTIBLE_IDX = DEPLOY_IDX


@dataclass
class GraspWorld:
    workspace: float = 1.0
    yaw_tol: float = 0.35
    force_rel_tol: float = 0.28
    cam_noise: float = 0.02
    enc_noise: float = 0.02
    force_noise: float = 0.04


def _physics_success(
    gx: np.ndarray,
    gy: np.ndarray,
    yaw: np.ndarray,
    force: np.ndarray,
    mass: np.ndarray,
    world: GraspWorld,
) -> np.ndarray:
    in_ws = (gx >= 0.0) & (gx <= world.workspace) & (gy >= 0.0) & (gy <= world.workspace)
    aligned = np.abs(yaw) <= world.yaw_tol
    need = 0.8 + 1.6 * mass
    lo = need * (1.0 - world.force_rel_tol)
    hi = need * (1.0 + world.force_rel_tol)
    force_ok = (force >= lo) & (force <= hi)
    return (in_ws & aligned & force_ok).astype(int)


def generate_batch(
    n: int,
    rng: np.random.Generator,
    world: GraspWorld | None = None,
    enc_bias: tuple[float, float, float] = (0.0, 0.0, 0.0),
    motor_bias: float = 0.0,
    gx_lo: float | None = None,
    gx_hi: float | None = None,
    oversample: int = 8,
) -> tuple[np.ndarray, np.ndarray, dict]:
    """Draw n labeled observations.

    enc_bias / motor_bias: frozen-label sensor perturbation.
    gx_lo / gx_hi: restrict true gx (selection; pairs kept). Train on a
    lower band and test on a higher band to leave support.
    """
    world = world or GraspWorld()
    bx, by, byaw = enc_bias
    xs: list[np.ndarray] = []
    ys: list[np.ndarray] = []
    meta_gx: list[np.ndarray] = []
    target = n
    tries = 0
    max_tries = max(4, oversample)
    lo = -0.15 if gx_lo is None else gx_lo
    hi = world.workspace + 0.15 if gx_hi is None else gx_hi
    while sum(v.shape[0] for v in ys) < target and tries < max_tries:
        tries += 1
        m = n * oversample
        gx = rng.uniform(lo, hi, size=m)
        gy = rng.uniform(-0.15, world.workspace + 0.15, size=m)
        yaw = rng.normal(0.0, 0.28, size=m)
        mass = rng.uniform(0.2, 1.0, size=m)
        need = 0.8 + 1.6 * mass
        force_true = need + rng.normal(0.0, 0.18, size=m)

        y = _physics_success(gx, gy, yaw, force_true, mass, world)
        cam = np.column_stack(
            [
                gx + rng.normal(0.0, world.cam_noise, size=gx.size),
                gy + rng.normal(0.0, world.cam_noise, size=gx.size),
                yaw + rng.normal(0.0, world.cam_noise, size=gx.size),
            ]
        )
        enc = np.column_stack(
            [
                gx + bx + rng.normal(0.0, world.enc_noise, size=gx.size),
                gy + by + rng.normal(0.0, world.enc_noise, size=gx.size),
                yaw + byaw + rng.normal(0.0, world.enc_noise, size=gx.size),
            ]
        )
        gauge = force_true + rng.normal(0.0, world.force_noise, size=gx.size)
        motor = force_true + motor_bias + rng.normal(0.0, world.force_noise, size=gx.size)
        appear = rng.normal(0.0, 1.0, size=gx.size)
        X = np.column_stack([enc, cam, gauge, motor, appear])
        xs.append(X)
        ys.append(y)
        meta_gx.append(gx)

    X = np.concatenate(xs, axis=0)[:n]
    y = np.concatenate(ys, axis=0)[:n]
    gx_all = np.concatenate(meta_gx, axis=0)[:n]
    meta = {
        "kind": "grasp_world",
        "n": int(len(y)),
        "enc_bias": list(enc_bias),
        "motor_bias": float(motor_bias),
        "gx_lo": lo,
        "gx_hi": hi,
        "pos_rate": float(y.mean()) if len(y) else None,
        "gx_mean": float(gx_all.mean()) if len(gx_all) else None,
    }
    return X, y, meta
