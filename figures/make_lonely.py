#!/usr/bin/env python3
"""Loneliness-track figures from results JSON only."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures" / "png"
OUT.mkdir(parents=True, exist_ok=True)


def load_summary():
    return json.loads((ROOT / "results" / "summary_lonely.json").read_text())["payload"]


def make_alone_vs_k():
    s = load_summary()
    grid = s["exact_grid"]
    p = 0.7
    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    for rule, label, ls in [
        ("one", r"$q=1$ (kill)", "--"),
        ("pair", r"$q=2$ (need one other person)", "-"),
        ("half", r"$q=\lceil k/2\rceil$", ":"),
    ]:
        rows = [r for r in grid if r["q_rule"] == rule and abs(r["p"] - p) < 1e-9]
        rows = sorted(rows, key=lambda r: r["k"])
        ax.plot([r["k"] for r in rows], [r["p_alone"] for r in rows], ls, marker="o", label=label)
    ax.axhline(1 - p, color="0.5", lw=1, label=r"own-flake floor $1-p$")
    ax.set_xlabel("proposed gathering size $k$")
    ax.set_ylabel(r"$P(\mathrm{alone})$")
    ax.set_title(r"Independent flakes, $p=0.7$")
    ax.grid(True, alpha=0.3)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "lonely_alone_vs_k.png", dpi=150)
    plt.close(fig)


def make_quality_and_kill():
    s = load_summary()
    h = s["headline_mc"]
    k1 = s["kill_q1_mc"]
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.4))
    ax = axes[0]
    labs = ["dyad $k=2$", "pub $k=24$"]
    means = [h["dyad_alone"]["mean"], h["pub_alone"]["mean"]]
    stds = [h["dyad_alone"]["std"], h["pub_alone"]["std"]]
    ax.bar(labs, means, yerr=stds, capsize=4, color=["#c44e52", "#4c72b0"])
    ax.axhline(s["headline_exact"]["own_flake_floor"], color="0.4", ls="--", label="flake floor")
    ax.set_ylabel("nights alone")
    ax.set_title(r"$q=2$, $p=0.7$ (MC, 5 seeds)")
    ax.legend(frameon=False, fontsize=8)
    ax.set_ylim(0, 0.7)
    ax = axes[1]
    labs = [r"$q=2$", r"$q=1$ kill"]
    means = [h["delta_alone_mc"]["mean"], k1["delta_alone_mc"]["mean"]]
    stds = [h["delta_alone_mc"]["std"], k1["delta_alone_mc"]["std"]]
    ax.bar(labs, means, yerr=stds, capsize=4, color=["#c44e52", "#55a868"])
    ax.axhline(0, color="0.3", lw=1)
    ax.set_ylabel(r"$\Delta_{\mathrm{alone}}$ (dyad $-$ pub)")
    ax.set_title("Quorum is the mechanism")
    fig.tight_layout()
    fig.savefig(OUT / "lonely_quality_kill.png", dpi=150)
    plt.close(fig)


def make_fomo_feed():
    s = load_summary()
    h = s["headline_mc"]
    fig, ax = plt.subplots(figsize=(6.0, 3.5))
    labs = ["proposed mix", "happening events", "attendance feed"]
    means = [h["mean_proposed"]["mean"], h["feed_event"]["mean"], h["feed_att"]["mean"]]
    stds = [h["mean_proposed"]["std"], h["feed_event"]["std"], h["feed_att"]["std"]]
    ax.bar(labs, means, yerr=stds, capsize=4, color=["#8c8c8c", "#4c72b0", "#c44e52"])
    ax.set_ylabel("mean gathering size")
    ax.set_title("50/50 dyad–pub world, $q=2$, $p=0.7$")
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / "lonely_fomo_feed.png", dpi=150)
    plt.close(fig)


def make_overinvite():
    s = load_summary()
    rows = sorted(s["overinvite_p07"], key=lambda r: r["m"])
    fig, ax = plt.subplots(figsize=(6.2, 3.5))
    ax.plot([r["n_invited"] for r in rows], [r["p_alone_overinvite"] for r in rows], "o-", label="over-invited 'date'")
    ax.axhline(rows[0]["p_alone_pub"], color="#4c72b0", ls="--", label="pub $k=24$")
    ax.axhline(rows[0]["own_flake_floor"], color="0.4", ls=":", label=r"floor $1-p$")
    ax.set_xlabel("people invited to the 'date' (still $q=2$)")
    ax.set_ylabel(r"$P(\mathrm{alone})$")
    ax.set_title(r"Airline overbooking, $p=0.7$")
    ax.legend(frameon=False, fontsize=8)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / "lonely_overinvite.png", dpi=150)
    plt.close(fig)


def main() -> None:
    make_alone_vs_k()
    make_quality_and_kill()
    make_fomo_feed()
    make_overinvite()
    print(f"wrote figures in {OUT}")


if __name__ == "__main__":
    main()
