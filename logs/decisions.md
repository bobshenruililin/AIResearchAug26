# Decision log (append-only)

## 2026-08-26 — Topic lock (P0)

**Decision:** Study post-hoc probability calibration under covariate shift on
small tabular datasets with sklearn models (LogReg, RandomForest,
HistGradientBoosting). Calibrators: none / temperature scaling / isotonic /
histogram binning. Also measure split-conformal coverage as a secondary lens.

**Why:** Environment is 4×CPU, 16 GB RAM, no GPU, $0 API. LLM/RAG/GRPO topics
in the GOAL template are infeasible without fabricating scale. Calibration
under shift is a real literature gap for *classical tabular* models (most
evidence is ImageNet/deep nets). Negative results are acceptable and likely.

**Rejected alternatives:**
- GRPO reward hacking: needs GPU + RL training.
- RAG retrieval-noise: needs embeddings + reader LM.
- Jailbreak transfer: API cost and dual-use risk; not reproducible at $0.

**Integrity:** All numbers from `results/*.json`. No hand-edited results.

## 2026-08-26 — Engineer proposals (P0)

Fable and Sol both proposed sklearn + venv + experiment dirs. **Agreement:**
metrics, shift mechanisms, atomic JSON writer, no OpenML in tests.
**Disagreement:** Sol wanted `results/` gitignored. **Rejected** — GOAL.md
requires `results/*.json` as the paper's source of truth, so they are
committed. Package name: kept `calibshift` (fable). Pins: the versions that
actually installed and passed tests on this machine.

## 2026-08-26 — Literature merge (P1)

Sol delivered 27 S2-verified papers. Orchestrator arXiv pass added
title-matched IDs. Union after dedupe: **47 verified**. Fable lit agent had
not finished writing `/tmp/lit_fable/papers.json` at merge time; Sol +
orchestrator already exceeded the 20-paper floor with API evidence, so P1
was not blocked. Unverified classics (Platt 1999, Zadrozny 2001, Shimodaira
2000, beta-calibration arXiv mismatch) were **excluded** from `verified.bib`.

## 2026-08-26 — P2 hypothesis selection

Pilots: `results/exp01_pilot_h1.json` (18/18 ok, 7.7s),
`results/exp02_pilot_h2.json` (48/48 ok, 6.4s),
`results/exp03_pilot_h3.json` (24/24 ok, 2.8s).

**KEEP H1 as the paper's primary hypothesis.** Every dataset×model×calibrator
cell had |mean ΔECE| ≥ 0.01 (kill threshold), and all three models had mean
ΔECE ≥ 0.02 for every calibrator. Additional signal: isotonic often *raises*
shifted ECE above the uncalibrated model (e.g. breast_cancer/hgb).

**Kill H2 as primary.** Directionally consistent at n_cal=50 (mean iso−temp
shifted ECE = +0.026) but heterogeneous (synthetic logreg ≈ 0; breast_cancer
RF reverses at the capped n_cal=142). Retain as an ablation, not the title
claim.

**Kill H3 as stated.** Unweighted coverage at s=1.5 is 0.747 (≤ 0.85, first
half holds) but oracle 1-D weighted coverage is 0.744 (does not recover
≥ 0.87). Kill criterion: weights fail to beat unweighted by 0.03. Cause:
the 4-feature Gaussian shift is not a 1-D shift on feature 0, so “oracle”
weights are misspecified. Keep unweighted undercoverage as a *secondary*
plot from the main grid; do not claim weighted conformal recovery.

**P3 implication:** Fix shifted feature indices (pilot seed 2 on
synthetic_shift often had ΔECE≈0 because random columns missed predictive
features). Add a noise-feature-shift *control*.

## 2026-08-26 — P3 complete / P4 analysis

exp04 240/240 ok (23s); exp05 60/60; exp06 60/60; exp07 30/30. No failed
runs. Headline: pooled ΔECE at s=1.5 is +0.113 (none) with 51/60 positive,
Wilcoxon p=2.2e-10. Exceptions and mixed calibrator-help documented in
analysis.md. H2/H3 remain killed as primary claims.
