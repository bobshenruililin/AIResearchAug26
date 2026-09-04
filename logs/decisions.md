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

## 2026-08-26 — P6 cycle 1 scores and pivot

Overall: methods 6, stats 5, novelty 6. Mean **5.67 < 6**. No fabrication
flags. Methods-skeptic: frozen-label Gaussian mean-shift is input
corruption, not covariate shift; selection controls that preserve
P(Y|X) show ΔECE ≈ 0.016. **We weaken the claim** to that distinction
rather than defending the original H1 wording. Also rename conformal
score from APS to LAC; add n=12 seed-averaged Wilcoxon (p=2.4e-4).

Novelty-cynic overall 6, fabrication_flag false. Stats-pedant overall 5,
fabrication_flag false. Methods-skeptic overall 6, fabrication_flag false
(cycle-1 set complete; mean 5.67). Cycle-2 independent re-review launched
on the reframed PDF.
Applied: scoped novelty claim; Pampari \& Ermon; prior work predicts
headlines; Wilcoxon described as exploratory; sd labelled as heterogeneity;
HGB ``interval includes 0'' removed; protocol numbers taken from exp04
JSON where possible.

exp04 240/240 ok (23s); exp05 60/60; exp06 60/60; exp07 30/30. No failed
runs. Headline: pooled ΔECE at s=1.5 is +0.113 (none) with 51/60 positive,
Wilcoxon p=2.2e-10. Exceptions and mixed calibrator-help documented in
analysis.md. H2/H3 remain killed as primary claims.

## 2026-08-26 — P6 cycle 2 gate

Overall: methods 7, stats 6, novelty 7. Mean **6.67 ≥ 6**. No fabrication
flags. GATE PASS. Remaining must-fixes applied without a third review
cycle: sklearn vs synthetic split in abstract/table; 12/12 bound to
uncalibrated cells and treated as a sign count; Table 1 drops n=60
Wilcoxon p as a primary column; one-sided tests labeled; wine RF
isotonic parenthetical no longer mixes in temperature ECE; exp05 n=6
on two datasets with matched Gaussian ΔECE/Δacc; Brier/NLL pooled Δ
reported; Pampari and Ermon / Tomani et al. named in running text;
dataset-level sign test n=4 p=0.0625 disclosed; wine n_test/n_cal from
JSON. NumNTests is now 22.

## 2026-08-31 — Hope: dual-regime act/abort

Swarm + implementation: 强任务 is act/abort with asymmetric cost on a
numpy grasp proxy (not wine). 强结构 is residual routing
(encoder vs camera) plus channel-switch, not a single OOD abort.
exp08 5/5 seeds: perturb router utility +93 vs always_iid −184 vs
abort-all 0. Locked into GOAL.md. Not a physical robot.

## 2026-08-31 — Swarm GO bar: peg-in-hole, opposite moves, projection

Four swarm personas finished after the grasp stack shipped. Combined lock:

- **Task:** planar peg-in-hole insert vs abort (geometric clearance), not
  grasp close/regrasp and not wine. Honest kinematic cartoon, not a robot.
- **Structure:** physics residual (encoder vs camera) and density ratio
  (camera xy) are separate channels with opposite legal moves.
  Perturbation: project encoder onto camera, then source T; never T on
  raw corrupted p. Selection: keep T, multivariate weighted LAC, defer
  not abort.
- **Lit:** do not claim an ICLR method gap. Tibshirani weights are invalid
  under frozen-label perturbation, so unlabeled identification is a
  precondition for using them.
- **Skeptic kill:** numpy grasp + OOD + abort more is a template. PCA
  residual is the wrong channel for optimistic encoder bias (near-origin
  is on the training manifold; PCA residual falls).

exp08 grasp JSON is frozen and superseded. Headline stack is exp09.

## 2026-09-04 — Seminar briefs: repo-only leftover identification

OpenAI / Jane Street / IAS / YC signed: not 3–5 AI directions, not Notion.
Object is leftover identification + one decision. Skills in
`.cursor/skills/seminar*`; files in `seminars/`. Pilot
`2026-09-01-pagliarini.md` is SKIP on a thin listing (legal).

## 2026-09-04 — Loneliness Ig Nobel track: dyad fragility

Not a costume on peg-in-hole. Lock file: `LONELINESS.md`.

**Question:** holding invitation rate and per-person show-up $p$ fixed,
does wanting a dyad ($k=2$, $q=2$) produce more nights alone than wanting
a pub ($k=24$), and does a length-biased Saturday-night feed overstate
how gregarious the calendar of *events* is?

**Killed angles:** retitling Feld 1991; ATUS-only isolation snapshots;
left-on-read blogs; logit frailty that moves $E[p]$.

**Kept:** independent Bernoulli flakes + hard quorum; $q=1$ kill;
pubs→dyads quality shift; attendance-weighted feed vs event-weighted
proposed mean; Gaussian copula with fixed margins.

Perlman & Peplau 1981 chapter did not verify (no DOI/arxiv); discrepancy
language cites Hawkley \& Cacioppo 2010 and Hughes et al.\ 2004 instead.



