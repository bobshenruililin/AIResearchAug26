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
API-verified BibTeX. Tabular/dual-regime draft: `paper/main.pdf`.
Loneliness cartoon (Ig Nobel track): `paper/lonely.pdf`.

A second stack (`src/dualregime/`, `experiments/exp09_peg_insert/`) turns
that measurement into an **insert vs abort** decision on a planar
peg-in-hole cartoon: physics residual (encoder vs camera) projects then
applies source \(T\); a density-ratio channel on camera \(xy\) defers
under workspace selection and never aborts as if the encoder lied.
This is not a robot.

A third stack (`src/quorumlonely/`, `experiments/exp10_quorum_lonely/`) is
a **dyad-fragility** cartoon of the loneliness epidemic: independent
Bernoulli flakes plus a hard quorum of two. Date night is fragile; pubs
are not. Not a human survey.

Pre-seminar leftover briefs live in [`seminars/`](seminars/README.md) (repo-only; no Notion). Dump a talk, run `/seminar`.

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
make lonely-paper       # exp10 + lonely figures + paper/lonely.pdf
```

## Layout

- `src/calibshift/` — metrics, calibrators, shift mechanisms, conformal
- `src/dualregime/` — peg-in-hole DGP, two-channel detector, opposite policies
- `src/quorumlonely/` — dyad-fragility / quorum-failure loneliness cartoon
- `experiments/expNN_*/` — one experiment per directory (`config.yaml`, `run.py`)
- `results/` — code-generated JSON only (never hand-edit)
- `paper/` — LaTeX + `verified.bib` (calibration) and `lonely_verified.bib`
- `LONELINESS.md` — lock file for the Ig Nobel track (does not replace `GOAL.md`)
- `STATE.md` — current phase (read this first in a new session)
- `GOAL.md` — dual-regime mission and gates
- `seminars/` — leftover-identification pockets (`/seminar`); no Notion
- `.cursor/skills/seminar*` — pocket, after-log, gated deep

## Integrity

Never edit files under `results/` by hand. Failed runs are persisted with
`"status": "failed"` rather than deleted.
