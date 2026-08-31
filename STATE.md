# STATE.md

**Phase:** P5 dual-regime (hope locked; paper being updated)
**Last completed step:** Dual-regime stack implemented; exp08 5/5 seeds; GOAL.md relocked to 强任务+强结构.
**Next action:** Compile paper; integrity tests; then P6 if time.
**Updated:** 2026-08-31

## Selected hypothesis

H-R: residual router + channel switch recovers act/abort utility under encoder/motor bias vs deployed-channel i.i.d. gating, and is not abort-all.

## Locked topic

Dual-regime act/abort: sensor perturbation vs workspace selection on a numpy grasp proxy (CPU, $0 API). Previous tabular ECE study is the motivating measurement.

## Budget tracker

| Resource | Used | Cap | Freeze-at-80% |
|---|---|---|---|
| API USD | 0 | 0 | n/a |
| GPU-hours | 0 | 0 | n/a |
| Experiment CPU-minutes | ~1 | 120 | 96 |

## Hypothesis status

- Tabular H1 (covariate shift): **withdrawn**; perturbation vs selection split kept as motivation.
- Dual-regime H-R: **supported** in exp08 (proxy only).
- Dual-regime far-band selection: **not** solved; all policies have bad utility.
