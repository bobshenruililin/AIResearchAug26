# GOAL.md — Autonomous Research Run

## Mission

Produce a complete, honest, ICLR-shaped research artifact (LaTeX 4–8 pages)
plus a fully reproducible repo, with zero fabricated content.
Optimize for: **强任务 + 强结构 + 普通数学** (task and system first;
ordinary statistics; no theorem-only contribution).

A well-executed negative or mixed result is a SUCCESS.
A hollow "novel method" with weak evidence is a FAILURE.

## Topic & scope (LOCKED 2026-08-31 — hope found)

**Direction:** Dual-regime act/abort for a contact/grasp success decision.
Two test-time changes that the previous workshop analysis showed are *not*
the same thing:

1. **Sensor perturbation** (frozen-label encoder/motor bias). \(P(Y\mid X_{\mathrm{enc}})\)
   breaks. The deployed policy only sees encoder + motor + appearance.
2. **Workspace selection** (pairs kept; camera and encoder still agree).
   Closer to covariate shift.

**Structure (the paper claim):** a residual detector (encoder vs camera,
motor vs gauge) routes to *different policies*:

- **Perturb:** switch to the watchdog channels (camera + gauge) and a
  failure-controlling probability gate fitted on those channels.
- **Select / i.i.d.:** keep the deployed-channel gate.
- This is **not** a single \(\|x-\mu\|\) abort threshold: selection moves
  location without raising residual; perturbation raises residual without
  requiring the location to be OOD.

**Task:** act vs abort with asymmetric cost (false-confident act costs
`cost_fail=8`, successful act rewards 1). Primary metrics: utility,
false-confident-act rate, recall of successes. ECE is secondary.

**Honesty:** this is a **numpy structural proxy** for a robot, not MuJoCo
and not hardware. We do not claim DexNet/GQ-CNN numbers.

**Hard constraints:** CPU-only, $0 API, sklearn/numpy/scipy, no paid APIs.
Reuse `calibshift` I/O, calibrators, and conformal helpers.

**Target venue profile:** ICLR / robotics-adjacent workshop; analysis +
system, ordinary math (quantile failure gate, residual routing).

**Why this topic (hope):** exp08 (5/5 seeds) on `results/exp08_dual_regime.json`
shows the router recovering utility under encoder bias where the deployed
i.i.d. gate does not, while matching i.i.d. utility when sensors agree.
That is the 强结构 signature a simple abort-all baseline cannot claim
(abort-all utility is 0; router is positive under perturbation).

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
  GATE: pick ONE hypothesis; kill the rest; record why in `logs/decisions.md`.
- **P3 Main experiments:** baselines first, then treatment, ≥3 seeds, ablations.
- **P4 Analysis:** figures from `figures/make_*.py` only; `analysis.md`.
- **P5 Paper:** full LaTeX draft. Abstract claims ⊆ analysis.md claims.
- **P6 Internal review:** 3 reviewer personas; mean ≥ 6 and no fabrication flags.

## Candidate hypotheses (dual-regime)

- **H-R (router helps under perturbation):** on the grasp proxy, mean utility
  of `router` under encoder/motor bias exceeds `always_iid` and exceeds
  `always_abort` (so it is not “just abort”) over ≥3 seeds.
- **H-S (selection is not perturbation):** residual stays low under workspace
  slice; detector labels selection as `select`/`iid` not `perturb`.
- **H-K (kill if always_clean equals router for the wrong reason):** if the
  detector never fires, router ≡ always_iid and H-R is void.

## Budget

- API spend: $0 / $0
- GPU: none
- Experiment CPU budget: leftover from the tabular analysis grid (seconds).
