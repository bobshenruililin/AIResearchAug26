"""Dyad-fragility loneliness cartoon. Writes results/exp10_quorum_lonely.json."""

from __future__ import annotations

import argparse
import sys
import time
import traceback
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from calibshift.io import mark_failed_run, write_result
from quorumlonely.binomial import (
    delta_alone,
    extra_isolation,
    min_invites_to_match_floor,
    overinvite_n,
    p_alone,
    p_attend,
    pair_quorum_extra,
    frailty_p_alone_mc,
)
from quorumlonely.world import quorum_value, simulate_calendar


def exact_grid(config: dict) -> list[dict]:
    rows = []
    for p in config["p_show_list"]:
        for rule in config["q_rules"]:
            for k in config["k_grid"]:
                q = quorum_value(rule, int(k))
                rows.append(
                    {
                        "p": float(p),
                        "q_rule": rule,
                        "k": int(k),
                        "q": int(q),
                        "p_alone": p_alone(int(k), float(p), q),
                        "p_attend": p_attend(int(k), float(p), q),
                        "extra": extra_isolation(int(k), float(p), q),
                        "pair_extra_identity": pair_quorum_extra(int(k), float(p))
                        if rule == "pair"
                        else None,
                    }
                )
    return rows


def overinvite_grid(config: dict) -> list[dict]:
    rows = []
    k_small = int(config["k_small"])
    k_large = int(config["k_large"])
    for p in config["p_show_list"]:
        for m in config["overinvite_m"]:
            n = overinvite_n(k_small, float(m))
            q = 2
            rows.append(
                {
                    "p": float(p),
                    "m": float(m),
                    "n_invited": n,
                    "still_a_dyad": n == 2,
                    "p_alone_overinvite": p_alone(n, float(p), q),
                    "p_alone_pub": p_alone(k_large, float(p), q),
                    "p_alone_dyad": p_alone(k_small, float(p), q),
                    "gap_vs_pub": p_alone(n, float(p), q) - p_alone(k_large, float(p), q),
                    "own_flake_floor": 1.0 - float(p),
                }
            )
    return rows


def match_floor_rows(config: dict) -> list[dict]:
    rows = []
    for p in config["p_show_list"]:
        rec = min_invites_to_match_floor(float(p), q=2, floor_k=int(config["k_large"]))
        rec["p"] = float(p)
        rec["floor_k"] = int(config["k_large"])
        rec["dyad_alone"] = p_alone(int(config["k_small"]), float(p), 2)
        rec["pub_alone"] = p_alone(int(config["k_large"]), float(p), 2)
        rec["floor_1mp"] = 1.0 - float(p)
        rows.append(rec)
    return rows


def frailty_rows(config: dict, rng: np.random.Generator) -> list[dict]:
    rows = []
    p = float(config["headline_p"])
    n_mc = int(config["frailty_mc_events"])
    for rho in config["rho_list"]:
        for k in (int(config["k_small"]), int(config["k_dinner"]), int(config["k_large"])):
            pa = frailty_p_alone_mc(k, p, 2, float(rho), rng, n_events=n_mc)
            rows.append(
                {
                    "p": p,
                    "k": k,
                    "q": 2,
                    "rho": float(rho),
                    "p_alone_mc": pa,
                    "p_alone_independent": p_alone(k, p, 2),
                }
            )
    return rows


def run(config: dict) -> dict:
    t0 = time.time()
    exact = exact_grid(config)
    over = overinvite_grid(config)
    match = match_floor_rows(config)
    rng_f = np.random.default_rng(123456)
    frailty = frailty_rows(config, rng_f)

    calendars = []
    n_ok = 0
    n_failed = 0
    for seed in config["seeds"]:
        for p in config["p_show_list"]:
            for rule in config["q_rules"]:
                for rho in config["rho_list"]:
                    p_id = list(config["p_show_list"]).index(p)
                    r_id = list(config["q_rules"]).index(rule)
                    s_id = list(config["rho_list"]).index(rho)
                    rng = np.random.default_rng(
                        int(seed) * 1_000_003 + p_id * 10_007 + r_id * 97 + s_id
                    )
                    cfg = {
                        "n_people": int(config["n_people"]),
                        "n_nights": int(config["n_nights"]),
                        "p_show": float(p),
                        "k_small": int(config["k_small"]),
                        "k_large": int(config["k_large"]),
                        "frac_small": float(config["frac_small"]),
                        "q_rule": rule,
                        "rho": float(rho),
                    }
                    try:
                        cal = simulate_calendar(cfg, rng)
                        cal["seed"] = int(seed)
                        calendars.append(cal)
                        n_ok += 1
                    except Exception as exc:  # noqa: BLE001
                        n_failed += 1
                        calendars.append(
                            {
                                "status": "failed",
                                "seed": int(seed),
                                "p_show": float(p),
                                "q_rule": rule,
                                "rho": float(rho),
                                "error": str(exc),
                            }
                        )

    p_h = float(config["headline_p"])
    k_s = int(config["k_small"])
    k_d = int(config["k_dinner"])
    k_l = int(config["k_large"])
    headline_exact = {
        "p": p_h,
        "q": 2,
        "k_dyad": k_s,
        "k_dinner": k_d,
        "k_pub": k_l,
        "alone_dyad": p_alone(k_s, p_h, 2),
        "alone_dinner": p_alone(k_d, p_h, 2),
        "alone_pub": round(p_alone(k_l, p_h, 2), 6),
        "delta_dyad_pub": round(delta_alone(k_s, k_l, p_h, 2), 6),
        "delta_dinner_pub": round(delta_alone(k_d, k_l, p_h, 2), 6),
        "extra_dyad": extra_isolation(k_s, p_h, 2),
        "extra_dinner": extra_isolation(k_d, p_h, 2),
        "extra_pub": 0.0 if extra_isolation(k_l, p_h, 2) < 1e-9 else extra_isolation(k_l, p_h, 2),
        "pair_identity_dyad": pair_quorum_extra(k_s, p_h),
        "own_flake_floor": 1.0 - p_h,
        "kill_q1_dyad": p_alone(k_s, p_h, 1),
        "kill_q1_pub": p_alone(k_l, p_h, 1),
        "kill_q1_delta": p_alone(k_s, p_h, 1) - p_alone(k_l, p_h, 1),
        "quality_shift_exact": round(p_alone(k_s, p_h, 2) - p_alone(k_l, p_h, 2), 6),
    }

    return {
        "status": "ok",
        "experiment": "exp10_quorum_lonely",
        "config": config,
        "seconds": time.time() - t0,
        "n_ok": n_ok,
        "n_failed": n_failed,
        "headline_exact": headline_exact,
        "exact_grid": exact,
        "overinvite_grid": over,
        "match_floor": match,
        "frailty": frailty,
        "calendars": calendars,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(Path(__file__).with_name("config.yaml")))
    parser.add_argument("--out", default=str(ROOT / "results" / "exp10_quorum_lonely.json"))
    args = parser.parse_args()
    config = yaml.safe_load(Path(args.config).read_text())
    try:
        payload = run(config)
        write_result(args.out, payload)
        print(f"wrote {args.out} n_ok={payload['n_ok']} n_failed={payload['n_failed']} s={payload['seconds']:.1f}")
    except Exception as exc:  # noqa: BLE001
        mark_failed_run(args.out, str(exc), traceback.format_exc())
        raise


if __name__ == "__main__":
    main()
