# Feature perturbation vs selection shift (tabular, sklearn)

Workshop-style analysis study: **do post-hoc calibrators fitted on i.i.d.
validation data stay calibrated when test features are perturbed with
frozen labels, versus when test points are selected on \(X\)?**

The headline mechanism is **not** covariate shift. Frozen-label Gaussian
mean-shift changes \(P(Y\mid X)\) at the observed \(x\). Selection
controls that keep \((X,y)\) pairs are closer to covariate shift and
show a much smaller ECE change.

This repository is the source of truth. Paper numbers come only from
`results/*.json` written by experiment scripts. Citations come only from
`paper/verified.bib` after live API verification. Draft: `paper/main.pdf`.

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
make summary            # stats + figures + paper/numbers.tex
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
