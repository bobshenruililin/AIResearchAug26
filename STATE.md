# STATE.md

**Phase:** P6 complete (gate passed)
**Last completed step:** Cycle 2 mean overall 6.67 (≥6), no fabrication flags. Must-fixes applied; `paper/main.pdf` is 5 pages; pytest 18/18.
**Next action:** none (research run complete).
**Updated:** 2026-08-26

## Selected hypothesis

H1 (reframed): i.i.d.-fitted post-hoc maps do not keep ECE from rising under Gaussian mean-shift of test features with labels held fixed. Genuine covariate shift (selection on X) is a control, not the headline.

## Locked topic

Post-hoc calibration under feature perturbation vs selection shift on small tabular data (CPU, $0 API).

## Budget tracker

| Resource | Used | Cap | Freeze-at-80% |
|---|---|---|---|
| API USD | 0 | 0 | n/a |
| GPU-hours | 0 | 0 | n/a |
| Experiment CPU-minutes | ~1 (all grids <1 min wall) | 120 | 96 |
| Wall clock | this agent run | this agent run | n/a |

## Cycle 1 scores (no fabrication)

| Persona | Overall |
|---|---|
| methods-skeptic | 6 |
| stats-pedant | 5 |
| novelty-cynic | 6 |
| **mean** | **5.67** |

## Cycle 2 scores (no fabrication) — GATE PASS

| Persona | Overall |
|---|---|
| methods-skeptic | 7 |
| stats-pedant | 6 |
| novelty-cynic | 7 |
| **mean** | **6.67** |

## Hypothesis status

- H1 as originally worded (covariate shift): **withdrawn**; supported claim is frozen-label feature perturbation.
- H2: **killed** as primary (heterogeneous).
- H3: **killed** as stated (1-D weights misspecified).
