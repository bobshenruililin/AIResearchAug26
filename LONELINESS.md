# Loneliness track (LOCKED 2026-09-04)

Ig Nobel-shaped measurement, not a costume on the peg-in-hole stack.
The dual-regime paper in `GOAL.md` / `paper/main.tex` is unchanged.

## Identifying question

Holding invitation rate and per-person show-up probability fixed, does
**wanting a dyad** (one other person: a date, a catch-up) produce more
nights alone than **wanting a pub** (large \(k\)), because independent
Bernoulli flakes plus a hard quorum of two cancel small gatherings?

Loneliness here is a **Perlman–Peplau discrepancy proxy**, not a UCLA
survey: nights alone, desired \(k\) minus realized size, and a feed that
length-biases toward surviving large events. We do not claim we measured
the loneliness epidemic in humans. We claim a mechanical source of that
discrepancy under a cartoon DGP.

## Why this is not Feld 1991 / Jackson 2019 / blog-flake

- Feld: friends have more friends (degree inspection). We do not
  restatement-title that.
- Jackson: oversampling popular people inflates perceived engagement.
  Related to our feed, cited as such.
- Group-chat blogs: flakes kill small plans. True, not a paper. We add
  (i) a closed-form binomial identity, (ii) a \(q=1\) kill that isolates
  quorum, (iii) a quality-over-quantity comparative static (replace pubs
  with dyads, same person-slots), (iv) survivorship inspection of
  Saturday night, (v) logit-frailty correlation as robustness.

Laugh: the statistically honest cure is to triple-book the date or go to
the pub. Think: intimacy and flake-robustness are binomial-incompatible
under independent shows.

## Hypotheses

- **H1 (primary):** \(\Delta_{\mathrm{alone}}=P(\mathrm{alone}\mid k=2)-P(\mathrm{alone}\mid k=24)>0\)
  at quorum \(q=2\) and \(p\in(0,1)\). Exact: \(p(1-p)^{k-1}\) extra
  isolation above the own-flake floor \(1-p\).
- **H2:** Happening events, especially person-weighted, are larger than
  the proposed calendar (survivorship + inspection).
- **H3:** In a mixed dyad/pub world, an attendance-weighted feed overstates
  typical gathering size relative to the proposed mix.
- **Kill H1:** \(q=1\) (showing up alone counts) ⇒ \(\Delta_{\mathrm{alone}}=0\).
- **Kill H3:** A 100% dyad mix has no large-event feed illusion.
- **Policy:** converting pubs into dyads (same slots) **raises** population
  nights-alone. Over-inviting a dyad can approach the flake floor but
  destroys the dyad.
- **Robustness:** equicorrelated Gaussian copula (fixed marginal $p$).
  Logit shocks were rejected because they move $E[p]$.

## Honesty

Numpy people, not subjects. No ATUS/GSS in the headline (download/IRB).
CPU, $0 API. Numbers from `results/exp10_quorum_lonely.json` only.
Citations only from `paper/lonely_verified.bib` after live API verification.
