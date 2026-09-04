"""Unit tests for the dyad-fragility loneliness cartoon."""

from __future__ import annotations

import numpy as np
import pytest

from quorumlonely.binomial import (
    extra_isolation,
    min_invites_to_match_floor,
    p_alone,
    p_attend,
    pair_quorum_extra,
    frailty_p_alone_mc,
)
from quorumlonely.world import quorum_value, simulate_partition, simulate_quality_shift


def test_q1_kill_delta_is_zero():
    p = 0.7
    assert p_alone(2, p, 1) == pytest.approx(1 - p)
    assert p_alone(24, p, 1) == pytest.approx(1 - p)
    assert p_alone(2, p, 1) - p_alone(24, p, 1) == pytest.approx(0.0)


def test_pair_extra_is_p_times_all_others_flake():
    for k in (2, 4, 24):
        for p in (0.5, 0.7, 0.9):
            assert extra_isolation(k, p, 2) == pytest.approx(pair_quorum_extra(k, p), abs=1e-12)
            assert extra_isolation(k, p, 2) == pytest.approx(p * (1 - p) ** (k - 1), abs=1e-12)


def test_dyad_more_alone_than_pub_at_pair_quorum():
    p = 0.7
    delta = p_alone(2, p, 2) - p_alone(24, p, 2)
    assert delta > 0.15
    assert p_alone(2, p, 2) == pytest.approx(1 - p * p)
    assert p_alone(24, p, 2) == pytest.approx(1 - p, abs=0.01)


def test_p1_nobody_alone_if_q_ok():
    assert p_alone(4, 1.0, 2) == pytest.approx(0.0)
    assert p_alone(2, 0.0, 2) == pytest.approx(1.0)


def test_quality_shift_pubs_to_dyads_raises_isolation():
    p = 0.7
    assert (p_alone(2, p, 2) - p_alone(24, p, 2)) > 0.15


def test_overinvite_destroys_dyad_to_approach_floor():
    p = 0.7
    rec = min_invites_to_match_floor(p, q=2, floor_k=24, tol=0.01)
    assert rec["matched"]
    assert rec["n"] > 2
    assert rec["still_a_dyad"] is False
    assert p_alone(rec["n"], p, 2) <= p_alone(24, p, 2) + 0.01 + 1e-12


def test_mc_partition_matches_exact():
    rng = np.random.default_rng(0)
    out = simulate_partition(n_people=1200, k=2, p=0.7, q=2, n_nights=40, rng=rng)
    assert out["alone_rate"] == pytest.approx(out["exact_alone"], abs=0.03)


def test_mc_q1_gap_near_zero():
    rng = np.random.default_rng(1)
    a = simulate_partition(800, 2, 0.6, 1, 20, rng)
    b = simulate_partition(800, 24, 0.6, 1, 20, rng)
    assert abs(a["alone_rate"] - b["alone_rate"]) < 0.04


def test_frailty_helps_dyads():
    rng = np.random.default_rng(2)
    ind = p_alone(2, 0.7, 2)
    corr = frailty_p_alone_mc(2, 0.7, 2, rho=0.6, rng=rng, n_events=20000)
    assert corr < ind - 0.02


def test_quality_shift_mc_positive():
    rng = np.random.default_rng(3)
    rec = simulate_quality_shift(1200, 24, 2, 0.7, "pair", 15, rng)
    assert rec["delta_alone"] > 0.12
    assert rec["exact_delta"] == pytest.approx(p_alone(2, 0.7, 2) - p_alone(24, 0.7, 2))


def test_quorum_rules():
    assert quorum_value("one", 24) == 1
    assert quorum_value("pair", 24) == 2
    assert quorum_value("half", 24) == 12
    assert quorum_value("target", 4) == 4


def test_attend_plus_alone():
    assert p_attend(8, 0.55, 2) + p_alone(8, 0.55, 2) == pytest.approx(1.0)


def test_mixed_feed_is_length_biased_vs_event_calendar():
    rng = np.random.default_rng(4)
    from quorumlonely.world import simulate_mixed

    mix = simulate_mixed(2400, 2, 24, 0.7, "pair", 20, rng)
    assert mix["mean_proposed_event"] < 6
    assert mix["feed_size_attendance"] > mix["mean_proposed_event"] + 3
    assert mix["inspection_ratio_attendance"] > 1.5
