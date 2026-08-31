# STATE.md

**Phase:** P3 dual-regime upgrade (swarm GO bar)
**Last completed step:** Replaced grasp costume with planar peg-in-hole;
physics residual vs density-ratio as opposite channels; projection onto
camera pose; unit tests passing (8/8 dual-regime).
**Next action:** Run exp09 (5 seeds); summarize; rewrite dual paper section
from JSON; compile PDF.
**Updated:** 2026-08-31

## Selected hypothesis

H-R: under optimistic encoder bias, residual→project-then-\(T\) beats
illegal source \(T\) on raw encoder probabilities and beats abort-all.
H-S: right-half fixture selection is not labeled a sensor fault.

## Locked topic

Dual-regime insert/abort on a planar peg-in-hole kinematic cartoon
(CPU, $0 API). Tabular ECE study is the motivating measurement.

## Budget tracker

| Resource | Used | Cap | Freeze-at-80% |
|---|---|---|---|
| API USD | 0 | 0 | n/a |
| GPU-hours | 0 | 0 | n/a |
| Experiment CPU-minutes | ~1 | 120 | 96 |

## Hypothesis status

- Tabular H1 (covariate shift): **withdrawn**; perturbation vs selection split kept as motivation.
- Grasp-costume exp08: **superseded** (swarm: costume + abort-more = template).
- Peg-in-hole H-R/H-S: **in progress** (unit tests pass; exp09 not yet run).
