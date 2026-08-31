#!/usr/bin/env python3
"""Figures from results JSON only. No hand-tuned numbers."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures" / "png"
OUT.mkdir(parents=True, exist_ok=True)


def load_cells(name: str):
    env = json.loads((ROOT / "results" / name).read_text())
    return env["payload"]["cells"], env["payload"]["config"]


def grouped(cells):
    G = defaultdict(list)
    for cell in cells:
        s = float(cell["shift"]["strength"])
        for row in cell["rows"]:
            G[(cell["dataset"], cell["model"], s, row["calibrator"])].append(row)
    return G


def errorbar_xy(G, ds, model, cal, strengths, field):
    means, stds = [], []
    for s in strengths:
        rows = G[(ds, model, float(s), cal)]
        if field == "delta_ece":
            xs = [r["delta_ece"] for r in rows]
        elif field in {"ece_sh", "shifted_ece"}:
            xs = [r["shifted"]["ece"] for r in rows]
        elif field == "ece_iid":
            xs = [r["iid"]["ece"] for r in rows]
        elif field == "cov_sh":
            xs = [r["conformal"]["coverage_shifted"] for r in rows]
        elif field == "acc_sh":
            xs = [r["shifted"]["accuracy"] for r in rows]
        else:
            raise ValueError(field)
        means.append(float(np.mean(xs)))
        stds.append(float(np.std(xs, ddof=1)) if len(xs) > 1 else 0.0)
    return np.array(means), np.array(stds)


def make_ece_vs_shift():
    cells, cfg = load_cells("exp04_main_h1.json")
    G = grouped(cells)
    strengths = cfg["shift_strengths"]
    datasets = cfg["dataset_list"]
    models = cfg["model_list"]
    cals = cfg["calibrators"]
    fig, axes = plt.subplots(len(datasets), len(models), figsize=(10.5, 11), sharex=True, sharey=False)
    for i, ds in enumerate(datasets):
        for j, m in enumerate(models):
            ax = axes[i, j]
            for cal in cals:
                mu, sd = errorbar_xy(G, ds, m, cal, strengths, "ece_sh")
                ax.errorbar(strengths, mu, yerr=sd, marker="o", capsize=3, label=cal)
            ax.set_title(f"{ds} / {m}", fontsize=9)
            ax.grid(True, alpha=0.3)
            if j == 0:
                ax.set_ylabel("shifted ECE")
            if i == len(datasets) - 1:
                ax.set_xlabel("Gaussian shift strength")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=4, frameon=False)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(OUT / "ece_vs_shift.png", dpi=150)
    plt.close(fig)


def make_delta_heatmap():
    cells, cfg = load_cells("exp04_main_h1.json")
    G = grouped(cells)
    datasets = cfg["dataset_list"]
    models = cfg["model_list"]
    cals = cfg["calibrators"]
    fig, axes = plt.subplots(1, 4, figsize=(11.5, 3.6), sharey=True)
    for ax, cal in zip(axes, cals):
        mat = np.zeros((len(datasets), len(models)))
        for i, ds in enumerate(datasets):
            for j, m in enumerate(models):
                xs = [r["delta_ece"] for r in G[(ds, m, 1.5, cal)]]
                mat[i, j] = float(np.mean(xs))
        im = ax.imshow(mat, cmap="RdBu_r", vmin=-0.15, vmax=0.35, aspect="auto")
        ax.set_xticks(range(len(models)), models, fontsize=8)
        ax.set_title(cal)
        for i in range(len(datasets)):
            for j in range(len(models)):
                ax.text(j, i, f"{mat[i, j]:.2f}", ha="center", va="center", fontsize=8)
        if cal == "none":
            ax.set_yticks(range(len(datasets)), datasets, fontsize=8)
    fig.colorbar(im, ax=axes.ravel().tolist(), fraction=0.02, pad=0.02, label="mean ΔECE (s=1.5)")
    fig.suptitle("Mean ECE_shifted − ECE_iid at strength 1.5 (5 seeds)")
    fig.savefig(OUT / "delta_ece_heatmap.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def make_coverage():
    cells, cfg = load_cells("exp04_main_h1.json")
    G = grouped(cells)
    strengths = cfg["shift_strengths"]
    fig, ax = plt.subplots(figsize=(6.2, 3.8))
    for ds in cfg["dataset_list"]:
        mu, sd = errorbar_xy(G, ds, "logreg", "none", strengths, "cov_sh")
        ax.errorbar(strengths, mu, yerr=sd, marker="o", capsize=3, label=ds)
    ax.axhline(0.9, ls="--", color="black", lw=1, label="1−α = 0.9")
    ax.set_xlabel("Gaussian shift strength")
    ax.set_ylabel("split-conformal coverage (shifted)")
    ax.set_ylim(0.4, 1.02)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "coverage_vs_shift.png", dpi=150)
    plt.close(fig)


def make_help_under_shift():
    cells, cfg = load_cells("exp04_main_h1.json")
    seed_ece = defaultdict(dict)
    for cell in cells:
        if float(cell["shift"]["strength"]) != 1.5:
            continue
        for row in cell["rows"]:
            seed_ece[(cell["dataset"], cell["model"], cell["seed"])][row["calibrator"]] = row["shifted"]["ece"]
    labels, data = [], {c: [] for c in ["temperature", "isotonic", "histogram"]}
    for ds in cfg["dataset_list"]:
        for m in cfg["model_list"]:
            labels.append(f"{ds.split('_')[0]}/{m}")
            for cal in data:
                diffs = []
                for seed in range(5):
                    d = seed_ece[(ds, m, seed)]
                    diffs.append(d[cal] - d["none"])
                data[cal].append(float(np.mean(diffs)))
    x = np.arange(len(labels))
    w = 0.25
    fig, ax = plt.subplots(figsize=(10.5, 3.8))
    for i, cal in enumerate(data):
        ax.bar(x + (i - 1) * w, data[cal], w, label=cal)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(x, labels, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("ECE_shifted(cal) − ECE_shifted(none)")
    ax.set_title("Does i.i.d. post-hoc calibration help under shift? (s=1.5, mean of 5 seeds)")
    ax.legend()
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / "calibration_help_under_shift.png", dpi=150)
    plt.close(fig)


def make_ablation_shift_family():
    env = json.loads((ROOT / "results" / "exp05_ablate_shift_family.json").read_text())
    H = defaultdict(list)
    for cell in env["payload"]["cells"]:
        for row in cell["rows"]:
            if row["calibrator"] != "none":
                continue
            H[(cell["shift"]["kind"], cell["dataset"], cell["model"])].append(row["delta_ece"])
    # also gaussian from exp04 at s=1.5 none
    cells4, _ = load_cells("exp04_main_h1.json")
    for cell in cells4:
        if float(cell["shift"]["strength"]) != 1.5:
            continue
        if cell["dataset"] not in {"breast_cancer", "synthetic_shift"}:
            continue
        for row in cell["rows"]:
            if row["calibrator"] == "none":
                H[("gaussian_s1.5", cell["dataset"], cell["model"])].append(row["delta_ece"])
    kinds = ["gaussian_s1.5", "quantile_slice", "importance_resample"]
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    labels = []
    means = {k: [] for k in kinds}
    for ds in ["breast_cancer", "synthetic_shift"]:
        for m in ["logreg", "rf", "hgb"]:
            labels.append(f"{ds.split('_')[0]}/{m}")
            for k in kinds:
                xs = H[(k, ds, m)]
                means[k].append(float(np.mean(xs)) if xs else np.nan)
    x = np.arange(len(labels))
    w = 0.25
    for i, k in enumerate(kinds):
        ax.bar(x + (i - 1) * w, means[k], w, label=k)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(x, labels, rotation=30, ha="right", fontsize=8)
    ax.set_ylabel("mean ΔECE (none calibrator)")
    ax.legend(fontsize=8)
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / "shift_family_ablation.png", dpi=150)
    plt.close(fig)


def make_dual_utility():
    path = ROOT / "results" / "exp08_dual_regime.json"
    if not path.exists():
        return
    cells = json.loads(path.read_text())["payload"]["cells"]
    modes = ["always_abort", "always_iid", "always_clean", "router"]
    splits = ["iid", "perturb", "select"]
    G = defaultdict(list)
    for cell in cells:
        for row in cell["rows"]:
            G[(row["split"], row["mode"])].append(row["utility"])
    fig, ax = plt.subplots(figsize=(6.4, 3.2))
    x = np.arange(len(splits))
    w = 0.18
    for i, mode in enumerate(modes):
        means = [float(np.mean(G[(s, mode)])) for s in splits]
        ax.bar(x + (i - 1.5) * w, means, w, label=mode.replace("_", " "))
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(x, splits)
    ax.set_ylabel("mean utility (5 seeds)")
    ax.legend(fontsize=7, ncol=2)
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / "dual_regime_utility.png", dpi=150)
    plt.close(fig)


def main():
    make_ece_vs_shift()
    make_delta_heatmap()
    make_coverage()
    make_help_under_shift()
    make_ablation_shift_family()
    make_dual_utility()
    print("wrote", list(OUT.glob("*.png")))


if __name__ == "__main__":
    main()
