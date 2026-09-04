# Loneliness track (exp10)

All numbers below are from `results/summary_lonely.json` /
`results/exp10_quorum_lonely.json` (code-generated). Paper macros in
`paper/lonely_numbers.tex`.

## What the evidence supports

1. **H1, exact.** At $p=0.7$, $q=2$: $P(\mathrm{alone}\mid k=2)=0.510$,
   $k=4$ dinner $0.319$, $k=24$ pub $0.300$. $\Delta$ dyad−pub $=0.210$.
   Extra isolation above $1-p=0.300$ is $0.210$ vs $0.000$.
2. **MC matches.** 5 seeds, 2400 people, 30 nights: $\Delta=0.212\pm0.003$.
   Dyad cancel rate $0.511$; pub $0.000$.
3. **Kill $q=1$.** Exact $\Delta=0$. MC $-0.001\pm0.001$.
4. **Quality shift.** Pubs→dyads raises alone by $0.210$ exact,
   $0.209\pm0.001$ MC.
5. **Feed.** Mixed 50/50: proposed event mean $3.7$, happening events $4.143$,
   attendance feed $10.865$, inspection ratio $2.943$. Pub people are $0.500$
   of heads and $0.587$ of nights out.
6. **Overinvite.** Smallest $n$ matching the pub within $0.005$ is $6$
   (no longer a dyad).
7. **Copula $\rho=0.5$.** Dyad alone $0.445$ vs $0.510$ independent;
   $\Delta$ shrinks to $0.140\pm0.004$, still positive.

## What it does not support

- Any UCLA / Hughes score, ATUS time-alone, or the claim that the loneliness
  epidemic *is* this mechanism.
- Strategic threshold dynamics (Granovetter is related work, not the DGP).
- Friendship-paradox degree bias as the headline (Feld/Jackson/Bollen are
  cited as cousins).

## Kill criteria

- $q=1$ $\Delta\approx 0$: **held**.
- All-dyad feed inspection vs event mean would be $\approx 1$ (no large-event
  illusion): implied by homogeneous $k=2$ calendars; mixed-world H3 needs
  heterogeneous $k$.
