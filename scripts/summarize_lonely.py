#!/usr/bin/env python3
"""Aggregate exp10 into results/summary_lonely.json (code-generated envelope)."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from calibshift.io import write_result

ROOT = Path(__file__).resolve().parents[1]


def _ms(xs: list[float]) -> dict:
    a = np.asarray(xs, dtype=float)
    return {
        "mean": float(a.mean()),
        "std": float(a.std(ddof=1)) if a.size > 1 else 0.0,
        "n": int(a.size),
        "min": float(a.min()) if a.size else None,
        "max": float(a.max()) if a.size else None,
    }


def _ok(cals: list[dict]) -> list[dict]:
    return [c for c in cals if c.get("status") != "failed"]


def main() -> None:
    env = json.loads((ROOT / "results" / "exp10_quorum_lonely.json").read_text())
    p = env["payload"]
    cals = _ok(p["calendars"])
    cells = defaultdict(list)
    for c in cals:
        key = (round(float(c["p_show"]), 2), c["q_rule"], round(float(c["rho"]), 2))
        cells[key].append(c)

    def pack(p_show: float, q_rule: str, rho: float) -> dict:
        rows = cells[(round(p_show, 2), q_rule, round(rho, 2))]
        return {
            "n_seeds": len(rows),
            "delta_alone_mc": _ms([r["delta_alone_mc"] for r in rows]),
            "dyad_alone": _ms([r["all_dyad"]["alone_rate"] for r in rows]),
            "pub_alone": _ms([r["all_pub"]["alone_rate"] for r in rows]),
            "quality_delta": _ms([r["quality_pubs_to_dyads"]["delta_alone"] for r in rows]),
            "mixed_delta": _ms([r["mixed"]["delta_alone_mc"] for r in rows]),
            "mixed_pop_alone": _ms([r["mixed"]["pop_alone_rate"] for r in rows]),
            "feed_att": _ms([r["mixed"]["feed_size_attendance"] for r in rows]),
            "feed_event": _ms([r["mixed"]["feed_size_event"] for r in rows]),
            "mean_proposed": _ms([r["mixed"]["mean_proposed"] for r in rows]),
            "insp_att": _ms([r["mixed"]["inspection_ratio_attendance"] for r in rows]),
            "insp_event": _ms([r["mixed"]["inspection_ratio_event"] for r in rows]),
            "fomo_att": _ms([r["mixed"]["fomo_size_gap_attendance"] for r in rows]),
            "share_out_large": _ms([r["mixed"]["share_of_out_person_nights_large"] for r in rows]),
            "share_people_large": _ms([r["mixed"]["share_of_people_large"] for r in rows]),
            "compare_stay": _ms([r["mixed"]["compare_stay_vs_feed"] for r in rows]),
            "compare_small_out": _ms([r["mixed"]["compare_small_out_vs_feed"] for r in rows]),
            "dyad_cancel": _ms([r["all_dyad"]["cancel_rate"] for r in rows]),
            "pub_cancel": _ms([r["all_pub"]["cancel_rate"] for r in rows]),
        }

    headline = pack(0.7, "pair", 0.0)
    kill = pack(0.7, "one", 0.0)
    half = pack(0.7, "half", 0.0)
    corr = pack(0.7, "pair", 0.5)

    frailty = {}
    for row in p["frailty"]:
        frailty[f"k{row['k']}_rho{round(float(row['rho']), 1)}"] = row

    match = {f"p{round(float(m['p']), 2)}": m for m in p["match_floor"]}
    over = [
        r
        for r in p["overinvite_grid"]
        if abs(r["p"] - 0.7) < 1e-9
    ]

    payload = {
        "status": "ok",
        "experiment": "exp10_quorum_lonely",
        "n_ok": p["n_ok"],
        "n_failed": p["n_failed"],
        "seconds": p["seconds"],
        "n_people": int(p["config"]["n_people"]),
        "n_nights": int(p["config"]["n_nights"]),
        "headline_exact": p["headline_exact"],
        "headline_mc": headline,
        "kill_q1_mc": kill,
        "half_quorum_mc": half,
        "rho05_mc": corr,
        "frailty": frailty,
        "match_floor": match,
        "overinvite_p07": over,
        "by_cell": {f"{k[0]}|{k[1]}|{k[2]}": pack(k[0], k[1], k[2]) for k in cells},
        "exact_grid": p["exact_grid"],
    }
    out = ROOT / "results" / "summary_lonely.json"
    write_result(out, payload)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
