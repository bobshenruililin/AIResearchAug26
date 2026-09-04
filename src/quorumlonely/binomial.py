"""Closed-form Bernoulli-flake identities.

A person is invited to a gathering of size ``k`` (including themselves).
Each invitee shows independently with probability ``p``. The gathering
happens iff at least ``q`` people show. The person is *not alone* iff they
show and the gathering happens.

The own-flake floor is ``1-p``: even a stadium cannot socialize a person
who stays home. Extra isolation above that floor is
``p * P(Bin(k-1, p) < q-1)``.
"""

from __future__ import annotations

import numpy as np
from scipy.stats import binom, norm


def p_event(k: int, p: float, q: int) -> float:
    """P(Bin(k, p) >= q)."""
    if k < 0:
        raise ValueError("k")
    if q <= 0:
        return 1.0
    if q > k:
        return 0.0
    return float(binom.sf(q - 1, k, p))


def p_attend(k: int, p: float, q: int) -> float:
    """P(a given invitee shows *and* the event meets quorum)."""
    if k < 1:
        return 0.0
    p = float(p)
    if q <= 1:
        return p
    return p * float(binom.sf(q - 2, k - 1, p))


def p_alone(k: int, p: float, q: int) -> float:
    """P(the invitee is not at a happening event)."""
    return 1.0 - p_attend(k, p, q)


def extra_isolation(k: int, p: float, q: int) -> float:
    """Isolation above the own-flake floor ``1-p``."""
    return max(0.0, p_alone(k, p, q) - (1.0 - float(p)))


def delta_alone(k_small: int, k_large: int, p: float, q: int) -> float:
    return p_alone(k_small, p, q) - p_alone(k_large, p, q)


def pair_quorum_extra(k: int, p: float) -> float:
    """For q=2: extra isolation is p*(1-p)^{k-1} (the others all flake)."""
    return float(p) * (1.0 - float(p)) ** (k - 1)


def overinvite_n(k_target: int, m: float) -> int:
    return max(int(k_target), int(round(float(m) * k_target)))


def min_invites_to_match_floor(
    p: float,
    q: int,
    floor_k: int,
    max_n: int = 200,
    tol: float = 0.005,
) -> dict:
    """Smallest n such that p_alone(n,p,q) <= p_alone(floor_k,p,q) + tol.

    For q=2 the large-k floor is nearly 1-p. A dyad cannot beat 1-p without
    changing p; it can only approach it by inviting more people (and ceasing
    to be a dyad).
    """
    target = p_alone(floor_k, p, q) + tol
    for n in range(max(q, 1), max_n + 1):
        pa = p_alone(n, p, q)
        if pa <= target:
            return {
                "n": n,
                "p_alone": pa,
                "target": target,
                "matched": True,
                "still_a_dyad": n == 2,
            }
    return {
        "n": max_n,
        "p_alone": p_alone(max_n, p, q),
        "target": target,
        "matched": False,
        "still_a_dyad": False,
    }


def equicorrelated_shows(
    n_events: int,
    k: int,
    p: float,
    rho: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """Boolean (n_events, k) with Bernoulli(p) margins.

    ``rho`` is the latent Gaussian correlation (a shared Friday-night factor).
    ``rho=0`` is independent. Unlike a logit shock, this does not move E[p].
    """
    p = float(p)
    rho = float(rho)
    if rho <= 0:
        return rng.random((n_events, k)) < p
    rho = min(max(rho, 0.0), 0.999)
    shared = rng.standard_normal(n_events)
    eps = rng.standard_normal((n_events, k))
    z = np.sqrt(rho) * shared[:, None] + np.sqrt(1.0 - rho) * eps
    thresh = float(norm.ppf(p))
    return z < thresh


def frailty_p_alone_mc(
    k: int,
    p: float,
    q: int,
    rho: float,
    rng: np.random.Generator,
    n_events: int = 40_000,
) -> float:
    """Monte Carlo p_alone with equicorrelated shows (fixed marginal p)."""
    if rho <= 0:
        return p_alone(k, p, q)
    shows = equicorrelated_shows(n_events, k, p, rho, rng)
    n_show = shows.sum(axis=1)
    attend = shows[:, 0] & (n_show >= q)
    return float(1.0 - attend.mean())
