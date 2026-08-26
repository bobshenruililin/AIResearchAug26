# STATE.md

**Phase:** P1 GATE ready to close; P2 pilots coded, not yet run
**Last completed step:** 47 verified papers; lit_review.md with H1/H2/H3; shared runner
**Next action:** Run exp01–exp03 pilots; pick one hypothesis; log kill decisions
**Updated:** 2026-08-26

## Locked topic

Post-hoc calibration under covariate shift on small tabular data (CPU, $0 API).

## Budget tracker

| Resource | Used | Cap | Freeze-at-80% |
|---|---|---|---|
| API USD | 0 | 0 | n/a |
| GPU-hours | 0 | 0 | n/a |
| Experiment CPU-minutes | 0 | 120 | 96 |
| Wall clock | just started | this agent run | n/a |

## Open risks

- No GPU; cannot study deep nets (accepted; topic locked around this).
- sklearn/LaTeX not preinstalled; must pin and bootstrap in-repo.
- Semantic Scholar rate limits may shrink the verified bibliography.
- OpenML downloads may fail; must have fully offline synthetic + sklearn datasets.
- Engineer and writer must not share a working directory later (P5).

## Subagents in flight

- lit fable: bc-208be551-b978-59e0-87b7-526c0da3b51e → /tmp/lit_fable
- lit sol: bc-ea8c22ae-e7f2-5404-9d14-38ee18999b63 → /tmp/lit_sol
- eng fable: bc-edfbf654-c900-537e-b39b-1f7a881e2b0c → /tmp/eng_fable
- eng sol: bc-14fa3032-3916-53f8-af6c-a01e5bb68966 → /tmp/eng_sol

## Hypothesis status

Not yet gated (P1). Draft H1/H2/H3 in GOAL.md.
