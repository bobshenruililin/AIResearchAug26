"""Finite-population gathering calendars.

People are partitioned into proposed gatherings each night (no double
booking). Shows are independent Bernoulli or equicorrelated (Gaussian
copula, fixed marginal p). A gathering happens iff n_show >= q.
happens iff n_show >= q. A person-night is alone unless they show *and*
the gathering happens.

Mixed worlds put a fraction of people in dyads and the rest in pubs so
the Saturday-night feed can length-bias toward surviving large events.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from .binomial import equicorrelated_shows, extra_isolation, p_alone, p_attend


def quorum_value(rule: str, k: int) -> int:
    if rule == "one":
        return 1
    if rule == "pair":
        return 2
    if rule == "half":
        return max(1, int(np.ceil(0.5 * k)))
    if rule == "target":
        return int(k)
    raise ValueError(f"unknown quorum rule {rule}")


def _shows(n_events: int, k: int, p: float, rho: float, rng: np.random.Generator) -> np.ndarray:
    """Boolean array (n_events, k). rho=0 is independent Bernoulli."""
    return equicorrelated_shows(n_events, k, p, rho, rng)


def simulate_partition(
    n_people: int,
    k: int,
    p: float,
    q: int,
    n_nights: int,
    rng: np.random.Generator,
    rho: float = 0.0,
) -> dict[str, Any]:
    """Homogeneous calendar: everyone is assigned groups of size k."""
    n_use = (n_people // k) * k
    n_events = n_use // k
    if n_events == 0:
        raise ValueError("n_people too small for k")
    shows = _shows(n_events * n_nights, k, p, rho, rng).reshape(n_nights, n_events, k)
    nshow = shows.sum(axis=2)
    happens = nshow >= q
    att = shows & happens[:, :, None]
    attended = int(att.sum())
    person_nights = n_use * n_nights
    event_nights = n_events * n_nights
    alone = person_nights - attended
    cancelled = int((~happens).sum())
    hs = nshow[happens]
    happening_sizes = hs.astype(int)
    if happening_sizes.size:
        mean_happening_event = float(happening_sizes.mean())
        mean_happening_person = float(
            np.repeat(happening_sizes, happening_sizes).mean()
        )
        feed_event = mean_happening_event
        feed_att = mean_happening_person
        n_happening = int(happening_sizes.size)
    else:
        mean_happening_event = 0.0
        mean_happening_person = 0.0
        feed_event = 0.0
        feed_att = 0.0
        n_happening = 0
    return {
        "k": k,
        "q": q,
        "p": p,
        "rho": rho,
        "n_use": n_use,
        "n_nights": n_nights,
        "person_nights": person_nights,
        "event_nights": event_nights,
        "alone_rate": alone / person_nights,
        "attend_rate": attended / person_nights,
        "cancel_rate": cancelled / event_nights,
        "exact_alone": p_alone(k, p, q) if rho <= 0 else None,
        "exact_attend": p_attend(k, p, q) if rho <= 0 else None,
        "exact_extra": extra_isolation(k, p, q) if rho <= 0 else None,
        "mean_proposed": float(k),
        "mean_happening_event": mean_happening_event,
        "mean_happening_person": mean_happening_person,
        "n_happening": n_happening,
        "n_cancelled": cancelled,
        "true_frac_out": attended / person_nights,
        "feed_size_event": feed_event,
        "feed_size_attendance": feed_att,
    }


def simulate_mixed(
    n_people: int,
    k_small: int,
    k_large: int,
    p: float,
    q_rule: str,
    n_nights: int,
    rng: np.random.Generator,
    frac_small: float = 0.5,
    rho: float = 0.0,
) -> dict[str, Any]:
    """Split the population into small-k and large-k partitions.

    Stay-home FOMO: the feed is built from *happening* events only.
    Attendance-weighted feed oversamples large surviving gatherings.
    Event-uniform feed still sees survivorship (cancelled dyads vanish)
    but not length bias within the happening set.
    """
    n_small = int(round(frac_small * n_people))
    n_small = (n_small // k_small) * k_small
    n_large = ((n_people - n_small) // k_large) * k_large
    q_s = quorum_value(q_rule, k_small)
    q_l = quorum_value(q_rule, k_large)
    small = simulate_partition(n_small, k_small, p, q_s, n_nights, rng, rho=rho)
    large = simulate_partition(n_large, k_large, p, q_l, n_nights, rng, rho=rho)

    # Rebuild feed from the two blocks using stored means * counts.
    # We need combined happening lists; re-simulate once into accumulators.
    # The two calls above already consumed rng; that is fine (independent blocks).
    pn_s, pn_l = small["person_nights"], large["person_nights"]
    out_s = small["true_frac_out"] * pn_s
    out_l = large["true_frac_out"] * pn_l
    true_frac_out = (out_s + out_l) / (pn_s + pn_l)

    # Reconstruct person-weighted and event-weighted feeds from block summaries.
    # mean_happening_person * n_happening_person_slots = sum of sizes over attendees
    # n_happening * mean_happening_event = sum of happening sizes
    n_ev_s, n_ev_l = small["n_happening"], large["n_happening"]
    sum_ev = small["mean_happening_event"] * n_ev_s + large["mean_happening_event"] * n_ev_l
    n_ev = n_ev_s + n_ev_l
    sum_person = small["mean_happening_person"] * out_s + large["mean_happening_person"] * out_l
    n_person_slots = out_s + out_l
    feed_event = (sum_ev / n_ev) if n_ev else 0.0
    feed_att = (sum_person / n_person_slots) if n_person_slots else 0.0
    n_ev_prop_s = (n_small // k_small) * n_nights
    n_ev_prop_l = (n_large // k_large) * n_nights
    mean_proposed_event = (k_small * n_ev_prop_s + k_large * n_ev_prop_l) / (
        n_ev_prop_s + n_ev_prop_l
    )
    mean_proposed_person = (k_small * pn_s + k_large * pn_l) / (pn_s + pn_l)

    # Stay-home comparison: people at home see the feed, own size 0.
    stay_s = 1.0 - small["true_frac_out"]
    stay_l = 1.0 - large["true_frac_out"]
    compare_stay = feed_att
    compare_small_out = feed_att - small["mean_happening_person"]
    compare_large_out = feed_att - large["mean_happening_person"]

    return {
        "k_small": k_small,
        "k_large": k_large,
        "q_small": q_s,
        "q_large": q_l,
        "p": p,
        "q_rule": q_rule,
        "rho": rho,
        "frac_small": frac_small,
        "n_small": n_small,
        "n_large": n_large,
        "small": small,
        "large": large,
        "pop_alone_rate": (small["alone_rate"] * pn_s + large["alone_rate"] * pn_l) / (pn_s + pn_l),
        "delta_alone_mc": small["alone_rate"] - large["alone_rate"],
        "true_frac_out": true_frac_out,
        "mean_proposed_event": mean_proposed_event,
        "mean_proposed_person": mean_proposed_person,
        "mean_proposed": mean_proposed_event,
        "feed_size_event": feed_event,
        "feed_size_attendance": feed_att,
        "inspection_ratio_attendance": (feed_att / mean_proposed_event) if mean_proposed_event else None,
        "inspection_ratio_event": (feed_event / mean_proposed_event) if mean_proposed_event else None,
        "fomo_size_gap_attendance": feed_att - mean_proposed_event,
        "fomo_size_gap_event": feed_event - mean_proposed_event,
        "stay_rate_small": stay_s,
        "stay_rate_large": stay_l,
        "compare_stay_vs_feed": compare_stay,
        "compare_small_out_vs_feed": compare_small_out,
        "compare_large_out_vs_feed": compare_large_out,
        "share_of_out_person_nights_large": (out_l / n_person_slots) if n_person_slots else None,
        "share_of_people_large": n_large / (n_small + n_large),
    }


def simulate_quality_shift(
    n_people: int,
    k_from: int,
    k_to: int,
    p: float,
    q_rule: str,
    n_nights: int,
    rng: np.random.Generator,
    rho: float = 0.0,
) -> dict[str, Any]:
    """Same person-slots, change gathering size (pubs → dyads or reverse)."""
    a = simulate_partition(
        n_people, k_from, p, quorum_value(q_rule, k_from), n_nights, rng, rho=rho
    )
    b = simulate_partition(
        n_people, k_to, p, quorum_value(q_rule, k_to), n_nights, rng, rho=rho
    )
    return {
        "k_from": k_from,
        "k_to": k_to,
        "p": p,
        "q_rule": q_rule,
        "rho": rho,
        "alone_from": a["alone_rate"],
        "alone_to": b["alone_rate"],
        "delta_alone": b["alone_rate"] - a["alone_rate"],
        "from": a,
        "to": b,
        "exact_delta": (
            p_alone(k_to, p, quorum_value(q_rule, k_to))
            - p_alone(k_from, p, quorum_value(q_rule, k_from))
            if rho <= 0
            else None
        ),
    }


def simulate_calendar(config: dict, rng: np.random.Generator) -> dict[str, Any]:
    """One seed: homogeneous curves + mixed FOMO + quality shift + frailty."""
    n_people = int(config["n_people"])
    n_nights = int(config["n_nights"])
    p = float(config["p_show"])
    k_small = int(config["k_small"])
    k_large = int(config["k_large"])
    q_rule = str(config["q_rule"])
    rho = float(config.get("rho", 0.0))
    mixed = simulate_mixed(
        n_people,
        k_small,
        k_large,
        p,
        q_rule,
        n_nights,
        rng,
        frac_small=float(config.get("frac_small", 0.5)),
        rho=rho,
    )
    quality = simulate_quality_shift(
        n_people, k_large, k_small, p, q_rule, n_nights, rng, rho=rho
    )
    all_dyad = simulate_partition(
        n_people, k_small, p, quorum_value(q_rule, k_small), n_nights, rng, rho=rho
    )
    all_pub = simulate_partition(
        n_people, k_large, p, quorum_value(q_rule, k_large), n_nights, rng, rho=rho
    )
    return {
        "p_show": p,
        "q_rule": q_rule,
        "rho": rho,
        "mixed": mixed,
        "quality_pubs_to_dyads": quality,
        "all_dyad": all_dyad,
        "all_pub": all_pub,
        "delta_alone_mc": all_dyad["alone_rate"] - all_pub["alone_rate"],
        "kill_q_is_one": q_rule == "one",
    }
