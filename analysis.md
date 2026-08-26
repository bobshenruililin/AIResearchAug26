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

2. **Gaussian covariate shift usually raises ECE relative to the matched i.i.d.
   test set.** At strength 1.5, pooled over 4 datasets × 3 models × 5 seeds
   (n=60): mean ΔECE = ECE_shifted − ECE_iid is
   +0.113±0.149 (none), +0.124±0.150 (temperature), +0.141±0.151 (isotonic),
   +0.141±0.151 (histogram). Sign counts: 51/60, 56/60, 53/60, 57/60 positive.
   One-sided Wilcoxon vs 0: p = 2.2e-10, 3.1e-11, 4.6e-11, 3.3e-11
   (`stats_tests.json` pooled tests). Per-dataset tests for `none` are also
   p < 0.005 on breast_cancer, wine, synthetic_shift, synthetic_multiclass.

3. **i.i.d.-fitted post-hoc calibrators do not prevent that increase.**
   Temperature/isotonic/histogram still have large positive pooled ΔECE.
   The H1 prediction (ΔECE ≥ 0.02 for ≥2/3 models) holds in the *pooled*
   sense; it does **not** hold in every dataset×model cell (see exceptions).

4. **Split conformal coverage falls as shift strength grows**, as expected
   when exchangeability is broken. Uncalibrated logreg coverage (α=0.1):
   breast_cancer 0.913 → 0.778 (s=1.5) → 0.608 (s=2.5);
   synthetic_shift 0.896 → 0.634 (s=1.5). i.i.d. coverage is near 0.90–0.92.

5. **Shift family matters.** Quantile slicing on feature 0 produces small
   ΔECE (typically 0.01–0.02). Importance resampling is mixed and can even
   *lower* ECE on breast_cancer (easier resampled subpopulation). The H1
   story is about **mean-shift of several features**, not all selection
   mechanisms.

6. **On synthetic_shift, shifting trailing columns hurts RF/HGB less than
   shifting the first four** (exp07 RF none ΔECE 0.009 vs exp04 0.041).
   LogReg still breaks under trailing-column shift (linear model uses all
   coordinates). This supports a “shift of used covariates” reading more than
   “any mean shift whatsoever.”

## What the evidence does **not** support

1. **Not a universal law that “calibration always fails under covariate
   shift.”** `breast_cancer` × HGB × none at s=1.5 has ΔECE 0.002±0.009
   (crosses zero). Several cells have negative ΔECE (9/60 for none).

2. **Not “post-hoc calibration helps under shift.”** Sign of
   ECE_shifted(cal) − ECE_shifted(none) is **dataset/model dependent**.
   Wine RF: isotonic *helps* by −0.123 ECE (trees were badly calibrated).
   Breast-cancer logreg: isotonic *hurts* by +0.074. We do not claim a
   winner among temperature / isotonic / histogram under shift.

3. **Not H2 as a general isotonic-overfit law.** exp06 iso−temp shifted ECE
   is positive for some n_cal×model cells and negative for others
   (breast_cancer RF at n_cal=100 and 142). Killed as a primary claim.

4. **Not “oracle-weighted conformal restores coverage.”** Pilot exp03: 1-D
   histogram density ratio on feature 0 did not beat unweighted coverage
   (0.744 vs 0.747 at s=1.5). The 4-feature mean-shift is not that 1-D
   shift. H3-as-stated is killed.

5. **Not ImageNet / deep-net calibration.** These are sklearn models on
   ≤2000-point tabular sets. ECE magnitudes are not comparable to Guo/Ovadia.

6. **Not that accuracy is preserved.** Shifted accuracy drops with strength
   (synthetic logreg 0.932 → 0.620 at s=1.5). Some ECE increase is entangled
   with accuracy drop / confidence on the wrong class. We report both.

7. **Not causal identification of “pure covariate shift.”** Gaussian
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

- Under a Gaussian mean-shift of four covariates, ECE on the shifted test
  set is higher than i.i.d. ECE for sklearn LogReg/RF/HGB in most cells
  (n=60 sign count; pooled Wilcoxon $p$-values are exploratory), including after i.i.d. temperature/isotonic/
  histogram calibration.
- That increase is **not** uniform: HGB on breast_cancer is a clear exception
  (descriptive mean and seed sd, not a confidence interval).
- i.i.d. post-hoc maps are **not** a reliable remedy; they can help or hurt.
- Unweighted split-conformal coverage declines with shift strength.
- Alternative shift families and noise-feature controls limit how far we
  generalize.
