# GOAL.md — Autonomous Research Run

## Mission

Produce a complete, honest, ICLR-shaped research artifact (LaTeX 4–8 pages)
plus a fully reproducible repo, with zero fabricated content.
Optimize for: **强任务 + 强结构 + 普通数学** (task and system first;
ordinary statistics; no theorem-only contribution).

A well-executed negative or mixed result is a SUCCESS.
A hollow "novel method" with weak evidence is a FAILURE.

## Topic & scope (LOCKED 2026-08-31 — swarm GO bar)

**Direction:** Dual-regime *insert vs abort* on a **planar peg-in-hole**
kinematic cartoon (geometric clearance). Not wine/breast_cancer as the
headline task. Not a physical robot.

Two test-time changes that the tabular measurement already showed are
*not* the same thing:

1. **Sensor perturbation** (optimistic encoder: reports the peg closer to
   the hole than the true pose; labels frozen). \(P(Y\mid X_{\mathrm{enc}})\)
   breaks. Near-origin poses exist in training, so PCA/OOD on encoder
   coordinates need not fire.
2. **Workspace selection** (keep pairs with \(x\ge 0\), right-half fixture).
   Encoder and camera still agree. \(P(Y\mid X)\) preserved. Difficulty-
   matched success rate vs i.i.d.

**Structure (the paper claim — opposite legal moves):**

- **Channel 1, physics residual** (encoder vs camera, plus
  \(p(\mathrm{raw})\) vs \(p(\mathrm{projected})\)). Routes to
  **project encoder onto the camera pose, then apply source \(T\)**
  (same deployed model). Abort only if residual is huge. **Forbidden:**
  source \(T\) on raw corrupted encoder probabilities; Tibshirani weights
  on \(X\).
- **Channel 2, density ratio** (camera-\(xy\) domain classifier / kNN).
  Routes to **the same \(T\) + multivariate weighted LAC**. Act or
  **defer**. **Forbidden:** abort-as-sensor-fault; project-as-if-the-encoder-lied.
- i.i.d.: source \(T\) + unweighted LAC → act / defer.

This is not a single \(\|x-\mu\|\) abort threshold and not a second
classifier on camera features.

**Task:** INSERT vs ABORT/DEFER with asymmetric cost
(`u_wrong_act=-10`, `u_correct_act=+1`, `u_defer=-0.2`, `u_abort=-0.5`).
Primary metrics: mean utility, FCAR, act/abort/defer rates,
coverage-of-safety. ECE is secondary.

**Honesty:** planar geometric clearance, not MuJoCo, not DexNet, not
hardware. We do **not** claim an ICLR method gap versus DetectShift /
Tibshirani / Luo abort; the contribution is the *routed decision stack*
on an identifying DGP, using redundant sensors to separate unlabeled
perturbation from selection.

**Hard constraints:** CPU-only, $0 API, sklearn/numpy/scipy, no paid APIs.
Reuse `calibshift` I/O, calibrators, and conformal helpers.

**Target venue profile:** ICLR / robotics-adjacent workshop; analysis +
system; ordinary math.

**Ablations that must exist in JSON:** detector_off, always_abort,
illegal_T (source \(T\) on raw encoder), denoise_off (abort, no project),
always_project, oracle.

**Kill criteria (from the structure spec):** policy collapse vs illegal_T;
ECE-only win; always-abort wins utility; selection abort_rate > 0.25;
no action difference under perturbation; Tibshirani weights as the
perturbation fix.

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
- **P2 Pilot:** cheapest experiment per hypothesis.
- **P3 Main experiments:** baselines first, then treatment, ≥3 seeds, ablations.
- **P4 Analysis:** figures from `figures/make_*.py` only; `analysis.md`.
- **P5 Paper:** full LaTeX draft. Abstract claims ⊆ analysis.md claims.
- **P6 Internal review:** 3 reviewer personas; mean ≥ 6 and no fabrication flags.

## Candidate hypotheses (dual-regime)

- **H-R (project, don't trust raw \(T\)):** under optimistic encoder bias,
  `router` mean utility exceeds `illegal_T` / `detector_off` and exceeds
  `always_abort`. FCAR drops vs illegal_T. Projection path is used.
- **H-S (selection is not a sensor fault):** residual stays low; abort_rate
  on the right-half fixture stays ≈ 0; success rate is difficulty-matched
  to i.i.d.
- **H-K:** if `router` ≡ `illegal_T` on FCAR and utility, the stack is a
  template. Kill.

## Budget

- API spend: $0 / $0
- GPU: none
- Experiment CPU budget: leftover from the tabular analysis grid (seconds).
