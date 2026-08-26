# Literature review: post-hoc calibration under covariate shift (tabular)

**n_verified = 47** (target 20–40; extras retained rather than dropped).
Sources: Semantic Scholar batch verification (`/tmp/lit_sol`) + live arXiv API
title-matched IDs. Canonical file: `paper/verified.bib` / `paper/verified_papers.json`.
No citation in this document is used unless it appears in `paper/verified.bib`.

## What is known

**Calibration methods (i.i.d.).** Platt-style logistic maps, histogram binning,
and isotonic regression are the classical post-hoc tools for turning classifier
scores into probabilities
\cite{zadrozny2002multiclass,niculescumizil2005probabilities}.
Temperature scaling is a one-parameter multiclass relative of Platt scaling that
became the default deep-net calibrator
\cite{guo2017calibration}. Richer parametric maps include beta calibration
(not in our verified set: the candidate arXiv ID did not title-match; we do
**not** cite it) and Dirichlet calibration \cite{kull2019dirichlet}.
Nonparametric alternatives include binning/BBQ \cite{naeini2015bbq},
splines \cite{gupta2020splines}, and GP-style maps
\cite{wenger2020nonparametric}.
Niculescu-Mizil and Caruana already observed that **isotonic regression can
overfit small calibration sets** while Platt scaling is more stable
\cite{niculescumizil2005probabilities}.

**Metrics.** Brier's score \cite{brier1950verification} and strictly proper
scoring rules \cite{gneiting2007scoring} remain the theoretically clean
criteria. ECE via equal-width confidence bins is the de facto deep-learning
metric \cite{guo2017calibration,naeini2015bbq} but is biased/estimator-dependent
\cite{nixon2019measuring,kumar2019verified,vaicenavicius2019evaluating,popordanoska2022canonical}.
Surveys: \cite{silvafilho2021survey,wang2023survey}.

**Shift breaks uncertainty.** Under dataset shift, deep-net confidence is
systematically miscalibrated even when in-distribution ECE looks fine
\cite{ovadia2019trust,minderer2021revisiting,hendrycks2019imagenetc}.
Post-hoc temperature scaling fitted i.i.d. is a common but incomplete fix
in domain-drift settings \cite{tomani2021posthoc}.
Calibration also interacts with OOD generalization
\cite{wald2021calibration}. Unsupervised attempts to recalibrate under
covariate shift exist for neural models \cite{pampari2020unsupervised}.
High-confidence far-from-data predictions are a separate but related failure
mode \cite{hein2019relu,nalisnick2018know}.

**Conformal prediction.** Split/jackknife conformal has finite-sample coverage
under exchangeability \cite{vovk2005algorithmic,lei2016distributionfree,barber2019jackknife,angelopoulos2021gentle}.
That guarantee **does not hold under covariate shift** unless one reweights by
the density ratio \cite{tibshirani2019covariate} or drops exchangeability more
generally \cite{barber2022beyond,gibbs2021adaptive}.
Label shift has its own weighted construction \cite{podkopaev2021labelshift}.

**Tabular models.** Tree ensembles still outperform deep nets on many tabular
tasks \cite{grinsztajn2022trees}. Their probabilities are a long-standing
calibration target \cite{niculescumizil2005probabilities}, but the modern
shift/calibration literature is almost entirely vision/language neural nets.

## Gap table

| Claim in literature | Evidence base | Missing for *this* paper |
|---|---|---|
| Temp. scaling fixes ECE i.i.d. | ImageNet NNs \cite{guo2017calibration,minderer2021revisiting} | sklearn LogReg/RF/HGB on small tabular |
| Shift wrecks NN calibration | ImageNet-C / CIFAR corruptions \cite{ovadia2019trust} | Controlled *covariate* (not label) shift on tabular P(X) |
| Isotonic overfits small n_cal | i.i.d. tabular 2005 \cite{niculescumizil2005probabilities} | Same comparison **under shift** |
| Domain-drift post-hoc calibration | CNN domain drift \cite{tomani2021posthoc,pampari2020unsupervised} | Frozen classical models; no unsupervised adaptation |
| Weighted conformal restores coverage | Theory + limited experiments \cite{tibshirani2019covariate} | APS/split conformal on sklearn `predict_proba` |
| Trees need calibration i.i.d. | RF/boosting \cite{niculescumizil2005probabilities} | Whether that calibration *transfers* |

**Gap statement (honest):** We do **not** claim a new calibrator. The gap is
*measurement*: classical post-hoc maps + classical tabular models + explicit
covariate shift, with conformal coverage as a second lens. Closest prior work
is Tomani et al. and Pampari \& Ermon (neural, often domain/label mix). If
our numbers merely reproduce their qualitative story on a smaller model class,
that is still a valid analysis/negative-supporting result.

## Three candidate hypotheses (P1 GATE)

### H1 — Transfer failure

i.i.d.-fitted post-hoc calibrators (temperature, isotonic, histogram) do not
preserve ECE under covariate shift for sklearn tabular models.

- **(a) Falsifiable prediction:** For Gaussian feature mean-shift of strength
  \(s=1.5\) (in training-feature SD units, ≥3 features), mean ECE on the
  shifted test set is at least **0.02 higher** than i.i.d. test ECE for the
  same calibrator, for at least 2/3 models (logreg, rf, hgb), averaged over
  3 seeds on `breast_cancer` + `synthetic_shift`.
- **(b) Kill criterion:** If every calibrator (including `none`) has
  |ECE_shift − ECE_iid| < 0.01 on all model×dataset cells in the pilot,
  kill H1 (shift too weak or ECE already saturated).
- **(c) Compute:** 3 seeds × 2 datasets × 3 models × 4 calibrators × 1 shift
  ≈ 72 sklearn fits; **< 2 CPU-minutes**.
- **(d) Novelty check:** Ovadia/Minderer/Tomani test NNs. Niculescu-Mizil tests
  tabular i.i.d. No verified paper in our set reports this exact grid.

### H2 — Isotonic overfit grows under shift

On small calibration sets, isotonic regression has higher shifted ECE than
temperature scaling.

- **(a) Prediction:** At \(n_{cal}\in\{50,100\}\), mean shifted ECE(isotonic)
  − ECE(temperature) ≥ 0.02 on binary tasks (3 seeds, logreg+rf).
- **(b) Kill:** If isotonic ≤ temperature at every \(n_{cal}\) (shifted ECE),
  kill H2.
- **(c) Compute:** 3 seeds × 2 models × 4 n_cal × 1 dataset ≈ 24 fits;
  **< 2 CPU-minutes**.
- **(d) Novelty check:** Niculescu-Mizil documented i.i.d. overfit; our set
  has no shift×n_cal ablation for isotonic vs temperature on sklearn models.

### H3 — Conformal undercoverage vs oracle-weighted recovery

Unweighted split conformal (APS scores on `predict_proba`) undercovers under
the same covariate shift; oracle 1-D density-ratio weighting restores coverage.

- **(a) Prediction:** For \(\alpha=0.1\) and \(s=1.5\), unweighted coverage
  ≤ 0.85 on shifted tests (mean over 3 seeds), while oracle-weighted coverage
  ≥ 0.87 on the same draws.
- **(b) Kill:** If unweighted shifted coverage stays within 0.03 of \(1-\alpha\)
  **or** oracle weights fail to beat unweighted by 0.03, kill H3 as stated
  (theory may still be right; our shift/weight estimator may be too crude).
- **(c) Compute:** 3 seeds × 2 datasets × 1 model (logreg) × 2 weightings;
  **< 1 CPU-minute**.
- **(d) Novelty check:** Tibshirani et al. 2019 is the theory
  \cite{tibshirani2019covariate}. We would only be *measuring* APS+sklearn
  under a synthetic shift, not proposing a new algorithm.

## Pilot decision rule (for P2)

Pick the hypothesis with highest expected information gain per CPU-minute:
prefer a result that can support a 4–8 page analysis paper even if negative.
If H1 dies, the paper becomes “tabular calibrators *are* surprisingly robust
to this shift family” (still publishable). If H1 lives, H2/H3 become
ablations rather than alternative papers.
