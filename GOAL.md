# GOAL.md — Autonomous Research Run

## Mission

Produce a complete, honest, workshop-grade ML research paper (LaTeX, 4–8 pages)
plus a fully reproducible repo, with zero fabricated content.
Optimize for: verifiable rigor > novelty > polish.

A well-executed negative or analysis result is a SUCCESS.
A hollow "novel method" with weak evidence is a FAILURE.

## Topic & scope (LOCKED 2026-08-26)

**Direction:** Post-hoc probability calibration under covariate shift on small
tabular datasets. Do temperature scaling, isotonic regression, and histogram
binning — fitted on an i.i.d. validation split — preserve ECE, Brier score, NLL,
and (for conformal prediction) coverage when test covariates are shifted?

**Hard constraints:** CPU-only (no GPU in this environment), $0 API spend,
sklearn/numpy/scipy only, no paid model APIs, no downloads that require auth.
Wall-clock target: finish P0–P6 in this agent run. Freeze experiments at 80% of
allocated CPU-experiment budget (see STATE.md).

**Target venue profile:** ML workshop (negative/analysis results welcome),
approximately NeurIPS/ICML workshop formatting (4–8 pages).

**Why this topic:** The environment has 4 CPU cores, 16 GB RAM, no GPU, and an
empty repo. Deep-net / LLM studies are out of budget. Calibration under shift is
well-studied for ImageNet-scale neural nets but under-measured for classical
tabular models, which is a legitimate analysis-paper gap.

## Non-negotiable integrity rules

1. Every number in the paper must be traceable to a file in `results/*.json`
   produced by code in this repo. Grep-verify before writing any number.
2. Every citation must be verified to exist via arXiv/Semantic Scholar API;
   store verified BibTeX in `paper/verified.bib`. No citation outside that file.
3. Never edit results files by hand. Never delete failed runs; mark them.
4. Report all seeds (≥3), variance, and every ablation attempted, including failures.
5. If a claim cannot be supported, weaken the claim — never strengthen the evidence.

## State protocol

- `STATE.md`: current phase, last completed step, next action, open risks.
  Update after EVERY unit of work.
- Commit to git after every unit of work with descriptive messages.
- Each experiment = `experiments/expNN_name/` with `config.yaml`, `run.py`, `README.md`.
- `logs/decisions.md`: append-only log of every pivot/kill decision + reasoning.

## Phase gates

- **P0 Setup:** env reproducible from scratch (fresh-clone test passes).
- **P1 Literature:** 20–40 verified papers → `lit_review.md` with a gap table.
  GATE: 3 candidate hypotheses, each with (a) falsifiable prediction,
  (b) kill criterion, (c) compute estimate, (d) novelty check.
- **P2 Pilot:** cheapest experiment per hypothesis (<10% budget each).
  GATE: pick ONE hypothesis; kill the rest; record why in `decisions.md`.
- **P3 Main experiments:** baselines first, then treatment, ≥3 seeds, ablations.
- **P4 Analysis:** figures from `figures/make_*.py` only; `analysis.md`.
- **P5 Paper:** full LaTeX draft. Abstract claims ⊆ analysis.md claims.
- **P6 Internal review:** 3 reviewer personas; mean ≥ 6 and no fabrication flags.

## Candidate hypotheses (to be refined in P1)

- **H1 (transfer failure):** i.i.d.-fitted post-hoc calibrators do not preserve
  ECE under covariate shift (shifted ECE ≥ uncalibrated ECE and > i.i.d. ECE).
- **H2 (isotonic overfit):** on small calibration sets (n_cal ≤ 200), isotonic
  regression has higher shifted ECE than temperature scaling.
- **H3 (conformal coverage):** unweighted split conformal undercovers under
  shift; oracle-weighted conformal recovers nominal coverage.

## Budget

- API spend: $0 / $0
- GPU: none
- Experiment CPU budget: ~120 core-minutes planned; freeze at 96 core-minutes
  (80%) and move to P4 with whatever exists.
