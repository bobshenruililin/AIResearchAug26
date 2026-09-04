"""Planar peg-in-hole insert vs abort (kinematic cartoon, not a robot).

True pose is (x, y, θ) relative to a round hole at the origin.
Success Y=1 iff geometric clearance:

    hypot(x, y) + k_theta * |θ|  <=  r_clear

The deployed policy sees encoder pose + an unused appearance channel.
A camera pose is a watchdog: it is *not* a training feature of the
deployed model. Labels always come from true seating, never from the
encoder.

Two test-time operators that the tabular paper already distinguished:

- Perturbation (optimistic encoder): scale encoder (x,y) toward the
  origin so the sensor reports a pose closer to seated than the truth.
  Frozen labels. P(Y | X_enc) breaks. Encoder–camera residual rises.
  Near-origin poses exist in training, so a PCA residual on encoder
  coordinates need not fire.
- Selection: keep (x, y, θ, Y) pairs with x >= x_lo (right-half fixture).
  Encoder and camera still agree. P(Y|X) is preserved.

Honesty: planar geometric clearance, not MuJoCo, not DexNet, not hardware.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

ENC_X, ENC_Y, ENC_TH = 0, 1, 2
CAM_X, CAM_Y, CAM_TH = 3, 4, 5
APPEAR = 6
N_FEATURES = 7

COLS = {
    "enc_x": ENC_X,
    "enc_y": ENC_Y,
    "enc_th": ENC_TH,
    "cam_x": CAM_X,
    "cam_y": CAM_Y,
    "cam_th": CAM_TH,
    "appearance": APPEAR,
}

# Deployed model: encoder + unused appearance. Camera is watchdog only.
DEPLOY_IDX = np.array([ENC_X, ENC_Y, ENC_TH, APPEAR], dtype=int)
CAM_IDX = np.array([CAM_X, CAM_Y, CAM_TH], dtype=int)
ENC_IDX = np.array([ENC_X, ENC_Y, ENC_TH], dtype=int)
CAM_XY_IDX = np.array([CAM_X, CAM_Y], dtype=int)
ENC_XY_IDX = np.array([ENC_X, ENC_Y], dtype=int)

@dataclass
class PegWorld:
    r_clear: float = 0.42
    k_theta: float = 0.55
    r_near: float = 0.50
    r_far: float = 1.10
    near_frac: float = 0.55
    theta_std: float = 0.22
    cam_noise: float = 0.03
    enc_noise: float = 0.03


def seating_success(
    x: np.ndarray,
    y: np.ndarray,
    th: np.ndarray,
    world: PegWorld,
) -> np.ndarray:
    radial = np.hypot(x, y) + world.k_theta * np.abs(th)
    return (radial <= world.r_clear).astype(int)


def sample_true_pose(
    n: int,
    rng: np.random.Generator,
    world: PegWorld,
    x_lo: float | None = None,
    x_hi: float | None = None,
    oversample: int = 6,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Draw n true (x, y, θ). Optional half-plane slice is selection."""
    xs: list[np.ndarray] = []
    ys: list[np.ndarray] = []
    ths: list[np.ndarray] = []
    tries = 0
    max_tries = max(8, oversample * 3)
    while sum(v.size for v in xs) < n and tries < max_tries:
        tries += 1
        m = n * oversample
        near = rng.random(m) < world.near_frac
        r = np.where(
            near,
            rng.uniform(0.0, world.r_near, size=m),
            rng.uniform(0.15, world.r_far, size=m),
        )
        phi = rng.uniform(-np.pi, np.pi, size=m)
        x = r * np.cos(phi)
        y = r * np.sin(phi)
        th = rng.normal(0.0, world.theta_std, size=m)
        mask = np.ones(m, dtype=bool)
        if x_lo is not None:
            mask &= x >= x_lo
        if x_hi is not None:
            mask &= x <= x_hi
        xs.append(x[mask])
        ys.append(y[mask])
        ths.append(th[mask])
    x = np.concatenate(xs)[:n]
    y = np.concatenate(ys)[:n]
    th = np.concatenate(ths)[:n]
    if x.size < n:
        raise RuntimeError(f"pose sampler only produced {x.size}/{n}")
    return x, y, th


def project_encoder_to_camera(X: np.ndarray) -> np.ndarray:
    """Physics repair: replace lying encoder with camera pose.

    Appearance is left as-is. This is an observation projection onto the
    camera-consistent pose, not a closed-loop regrasp.
    """
    Xp = np.array(X, dtype=np.float64, copy=True)
    Xp[:, ENC_IDX] = Xp[:, CAM_IDX]
    return Xp


def generate_batch(
    n: int,
    rng: np.random.Generator,
    world: PegWorld | None = None,
    enc_xy_scale: float = 1.0,
    enc_bias: tuple[float, float, float] = (0.0, 0.0, 0.0),
    x_lo: float | None = None,
    x_hi: float | None = None,
    oversample: int = 6,
) -> tuple[np.ndarray, np.ndarray, dict]:
    """Draw n labeled observations.

    enc_xy_scale < 1: optimistic frozen-label perturbation (encoder
    reports the peg closer to the hole than it is).
    x_lo / x_hi: pairing-preserving workspace slice (selection).
    """
    world = world or PegWorld()
    bx, by, bth = enc_bias
    x, y, th = sample_true_pose(n, rng, world, x_lo=x_lo, x_hi=x_hi, oversample=oversample)
    lab = seating_success(x, y, th, world)
    cam = np.column_stack(
        [
            x + rng.normal(0.0, world.cam_noise, size=n),
            y + rng.normal(0.0, world.cam_noise, size=n),
            th + rng.normal(0.0, world.cam_noise, size=n),
        ]
    )
    enc = np.column_stack(
        [
            enc_xy_scale * x + bx + rng.normal(0.0, world.enc_noise, size=n),
            enc_xy_scale * y + by + rng.normal(0.0, world.enc_noise, size=n),
            th + bth + rng.normal(0.0, world.enc_noise, size=n),
        ]
    )
    appear = rng.normal(0.0, 1.0, size=n)
    X = np.column_stack([enc, cam, appear])
    meta = {
        "kind": "peg_in_hole",
        "n": int(n),
        "enc_xy_scale": float(enc_xy_scale),
        "enc_bias": list(enc_bias),
        "x_lo": x_lo,
        "x_hi": x_hi,
        "pos_rate": float(lab.mean()),
        "x_mean": float(x.mean()),
        "r_median": float(np.median(np.hypot(x, y))),
    }
    return X, lab, meta
