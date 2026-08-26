# Calibration under covariate shift (tabular, sklearn)

Workshop-style analysis study: **do post-hoc calibrators fitted on i.i.d.
validation data stay calibrated when test covariates shift?**

This repository is the source of truth. Paper numbers come only from
`results/*.json` written by experiment scripts. Citations come only from
`paper/verified.bib` after live API verification.

## Constraints

- CPU-only, $0 API spend
- Python 3.11+
- No GPU, no torch required

## Reproduce from a fresh clone

```bash
make setup
make test
make smoke
make fresh-clone-test   # clones into /tmp and repeats setup+test+smoke
```

## Layout

- `src/calibshift/` — metrics, calibrators, shift mechanisms, conformal
- `experiments/expNN_*/` — one experiment per directory (`config.yaml`, `run.py`)
- `results/` — code-generated JSON only (never hand-edit)
- `paper/` — LaTeX + `verified.bib`
- `STATE.md` — current phase (read this first in a new session)
- `GOAL.md` — mission and gates
- `logs/decisions.md` — append-only kill/pivot log

## Integrity

Never edit files under `results/` by hand. Failed runs are persisted with
`"status": "failed"` rather than deleted.
