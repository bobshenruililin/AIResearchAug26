# exp04_main_h1

Primary H1 grid. Baseline calibrator is `none`; treatments are temperature,
isotonic, and histogram binning. Shifted feature indices are **fixed**
(first 4 columns) so seeds do not confound *which* covariates move.

- Datasets: breast_cancer, wine, synthetic_shift, synthetic_multiclass
- Models: logreg, rf, hgb
- Seeds: 0–4 (5 seeds)
- Shift strengths: 0, 1.0, 1.5, 2.5 (s=0 is the i.i.d. sanity / baseline)

Cells: 4×3×5×4 = 240 model fits.
