# Analysis (P4)

All numbers below are copied from `results/summary_main.json` or
`results/stats_tests.json` (themselves produced by `scripts/stats_and_summary.py`
from experiment JSONs). Roundings in the paper go through `paper/numbers.tex`.

## Setup recap

Primary experiment `exp04_main_h1`: 240/240 cells ok in 23.0s. Four datasets,
three sklearn models, four calibrators, five seeds, Gaussian mean-shift on
columns `[0,1,2,3]` at strengths `{0, 1.0, 1.5, 2.5}`.

## What the evidence **does** support

1. **I.i.d. sanity matches the classical picture.** Logistic regression on
   `breast_cancer` has mean accuracy 0.979 and ECE 0.032±0.010
   (`iid_sanity_s0_none.breast_cancer|logreg|none`). Random forests on `wine`
   are badly calibrated i.i.d. (ECE 0.147±0.020), while temperature scaling
   brings i.i.d. ECE down (cell `wine|rf|s0.0|temperature` ECE 0.032). This
   is the Niculescu-Mizil/Caruana + Guo qualitative pattern, not ImageNet-scale
   ECE, but it is in the right ballpark for these models.

2. **Gaussian feature perturbation (frozen labels) usually raises ECE**
   relative to the matched i.i.d. test set. At strength 1.5, pooled over
   4 datasets × 3 models × 5 seeds (n=60): mean ΔECE is
   +0.113±0.149 (none). Sign counts: 51/60 positive. Sklearn-only
   (breast_cancer+wine, n=30) mean ΔECE 0.042 (25/30 positive);
   synthetics (n=30) mean 0.184 (26/30 positive). Seed-averaged
   uncalibrated dataset×model means: 12/12 positive. Pooled n=60 Wilcoxon
   p-values overstate independence and are exploratory (one-sided).

3. **i.i.d.-fitted post-hoc calibrators do not prevent that increase.**
   Temperature/isotonic/histogram still have large positive pooled ΔECE.
   The H1 prediction (ΔECE ≥ 0.02 for ≥2/3 models) holds in the *pooled*
   sense; it does **not** hold in every dataset×model cell (see exceptions).

4. **Split conformal coverage falls as shift strength grows**, as expected
   when exchangeability is broken. Uncalibrated logreg coverage (α=0.1):
   breast_cancer 0.913 → 0.778 (s=1.5) → 0.608 (s=2.5);
   synthetic_shift 0.896 → 0.634 (s=1.5). i.i.d. coverage is near 0.90–0.92.

5. **Shift family matters, and the headline mechanism is not covariate
   shift.** Frozen-label Gaussian feature mean-shift changes $P(Y|X)$.
   Quantile slicing on feature 0 (selection; $P(Y|X)$ preserved) was run
   on 6 dataset×model cells (breast_cancer and synthetic_shift only) and
   produces small ΔECE (cell-mean ≈ 0.016), with a milder accuracy drop
   than matched Gaussian perturbation on those cells (ΔECE ≈ 0.105). Importance resampling is mixed. The
   H1 story as originally stated about covariate shift is **not
   supported**; the supported story is feature perturbation.

6. **On synthetic_shift, shifting trailing columns hurts RF/HGB less than
   shifting the first four** (exp07 RF none ΔECE 0.009 vs exp04 0.041).
   LogReg still breaks under trailing-column shift (linear model uses all
   coordinates). This supports a “shift of used covariates” reading more than
   “any mean shift whatsoever.”

## What the evidence does **not** support

1. **Not that i.i.d. post-hoc calibration fails under covariate shift.**
   Selection shifts that preserve $(X,y)$ have small ΔECE. The original
   H1 wording is withdrawn. Frozen-label feature perturbation is the
   supported mechanism.
2. **Not a universal law even for feature perturbation.**
   `breast_cancer` × HGB × none at s=1.5 has ΔECE 0.002±0.009.

3. **Not “post-hoc calibration helps under shift.”** Sign of
   ECE_shifted(cal) − ECE_shifted(none) is **dataset/model dependent**.
   Wine RF: isotonic *helps* by −0.123 ECE (trees were badly calibrated).
   Breast-cancer logreg: isotonic *hurts* by +0.074. We do not claim a
   winner among temperature / isotonic / histogram under shift.

4. **Not H2 as a general isotonic-overfit law.** exp06 iso−temp shifted ECE
   is positive for some n_cal×model cells and negative for others
   (breast_cancer RF at n_cal=100 and 142). Killed as a primary claim.

5. **Not “oracle-weighted conformal restores coverage.”** Pilot exp03: 1-D
   histogram density ratio on feature 0 did not beat unweighted coverage
   (0.744 vs 0.747 at s=1.5). The 4-feature mean-shift is not that 1-D
   shift. H3-as-stated is killed.

6. **Not ImageNet / deep-net calibration.** These are sklearn models on
   ≤2000-point tabular sets. ECE magnitudes are not comparable to Guo/Ovadia.

7. **Not that accuracy is preserved.** Shifted accuracy drops with strength
   (synthetic logreg 0.932 → 0.620 at s=1.5). Some ECE increase is entangled
   with accuracy drop / confidence on the wrong class. We report both.

8. **Not causal identification of “pure covariate shift.”** Gaussian
   mean-shift changes P(X) and, because X is predictive, the test label
   mix and Bayes error can move. Quantile slice has the same caveat.

## Sanity vs published ballparks

| Check | Our number | Expected | Verdict |
|---|---|---|---|
| Breast-cancer logreg accuracy | 0.979±0.011 | typically ≳0.95 with linear models | plausible |
| Wine RF i.i.d. ECE | 0.147 | trees overconfident (Niculescu-Mizil) | qualitative match |
| Logreg i.i.d. ECE | 0.03–0.07 | already fairly calibrated | qualitative match |
| Split conformal i.i.d. coverage, α=0.1 | 0.90–0.92 | ≥0.9 finite-sample | match |
| ImageNet temp-scaling ECE | n/a | Guo ~1–4% | **not comparable; not claimed** |

## Paper claims allowed (abstract ⊆ this list)

- Under frozen-label Gaussian feature perturbation at s=1.5, uncalibrated
  ECE on the perturbed test is higher than i.i.d. ECE in 51/60 seed-level
  cells and in all 12 uncalibrated dataset×model seed-averaged means
  (sign count; models sharing a dataset are not independent). Pooled
  mean ΔECE mixes sklearn cells (~0.042) with synthetics (~0.184).
- i.i.d. post-hoc maps do not reliably prevent that increase; they can help
  or hurt vs. none. Wine RF isotonic *helps* shifted ECE (0.175 → 0.052);
  breast-cancer logreg isotonic *hurts*.
- Selection-based shifts that preserve (X,y) pairs (closer to covariate
  shift) were measured on 6 dataset×model cells from two datasets, are
  not strength-matched to s=1.5 perturbation, and yield smaller ΔECE.
  They do **not** support a general “calibration fails under covariate
  shift” claim.
- Unweighted split-conformal (LAC, not APS) coverage declines under
  feature perturbation (report seed sd).
- The HGB-on-breast-cancer cell is a small-effect exception.
- Pooled ΔBrier and ΔNLL on the same uncalibrated s=1.5 cells are
  positive; mean accuracy change is negative.

## Dual-regime insert/abort (exp09; peg-in-hole)

Source: `results/exp09_peg_insert.json` / `results/summary_dual.json`.
Planar geometric clearance; 5 seeds; HistGradientBoosting; costs
u_wrong=-10, u_correct=1, u_defer=-0.2, u_abort=-0.5; tau_act=0.8.
Optimistic encoder scale 0.4 vs right-half fixture `x>=0`.
Kill criteria fired: none.

Success rates (difficulty match): i.i.d. 0.458, perturb 0.464, select 0.426.

**Does support**

- Under optimistic encoder bias, `router` mean utility +0.093 beats
  `illegal_T` / `detector_off` (−3.000, FCAR 0.342) and `always_abort`
  (−0.500). FCAR drops to 0.014. Insert rate 0.396 (not abort-all).
  Project-then-T path rate 0.890; abort 0.110 is the huge-residual tail.
- `denoise_off` under perturbation equals abort-all (−0.500): the utility
  comes from **projection**, not from refusing more.
- PCA residual on encoder xy *falls* under optimistic bias; physics
  residual rises. The detector is not reconstruction OOD.
- Selection abort rate 0.000; utility +0.158 vs abort-all −0.500.
  Residual false-perturbation on the slice is ~0.012. Weighted conformal
  does not need to beat detector_off on this DGP; the legal move is
  “do not abort as a sensor fault.”
- i.i.d. router +0.177 vs detector_off +0.176 (no large tax).
- Mixed stream: slice block 0.949 density-labeled; bias block 0.929
  residual-labeled, 0.804 project-then-T.

**Does not support**

- Not a physical robot / DexNet / MuJoCo result.
- Not that multivariate weighted conformal *helps* selection utility
  (router 0.158 vs detector_off 0.160; within seed noise).
- Not that the router beats always-project under perturbation (oracle /
  always_project 0.126 vs router 0.093 because of the huge-residual abort
  tail). Disclose the gap.
- Not an ICLR method gap vs Tibshirani / Luo abort / DetectShift.
- No receding delayed-label calibrator in the homogeneous grid.

**Paper claims allowed (dual section)**

- Source T on raw optimistic-encoder probabilities is a false-confident
  insert policy; project-then-T is not, and is not abort-all.
- Fixture-slice selection is not aborted as a sensor fault.
- Numpy kinematic cartoon only. Kill criteria: none fired.
