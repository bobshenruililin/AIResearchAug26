---
name: seminar
description: >-
  Pre-seminar leftover identification. Trigger on /seminar or "brief this
  seminar". Dump slides, notes, DOI, or a listing. Write one pocket markdown
  file under seminars/. Not an AI-idea generator. Never Notion.
---

# /seminar

Write **one** hallway pocket for a talk the user is about to sit. The product is the **leftover scientific question** plus **one decision**. AI is licensed only after leftover is structured signal.

## Invoke

User dumps mixed materials (PDF, notes, URL, DOI, paste) and optionally speaker/lab.

Output path: `seminars/YYYY-MM-DD-speaker-slug.md` (talk date if known, else today). **One file.** Do not create `INDEX.md`, `LEDGER.md`, a second after-file, or anything in Notion.

## Dual-use (gate 0)

Refuse directions and recipes for: pathogen enhancement, reverse genetics, synthesis/genome design, sequence-to-function for toxins/select agents. If the talk is dual-use-adjacent: leftover/questions that do **not** transfer capability; no method; `decision: SKIP` unless they only need control questions. When uncertain, refuse the direction.

## Do not

- Invent n, organism, modality, accession, or quotes.
- Literature survey. No “have you tried $MODEL.”
- 3–5 scored AI directions. No method shopping.
- Print the word `DGP` on the card.
- Map every talk onto calibshift / peg-in-hole.
- Call leftover `structured` unless the three identification sentences are printed **and** organism + modality are in the materials (not UNKNOWN).

## Pocket (≤400 words, body)

Frontmatter, four keys only:

```yaml
---
date: YYYY-MM-DD
leftover: noise | cannot-tell | structured
decision: ASK | SKIP | COLLAB | INDEPENDENT
asked: ""
---
```

Body, in this order, plain English:

1. **Claim** — quote + slide# or listing URL. Else `unverified`.
2. **What they ran** — unit; intervention vs selection vs observation. One line. UNKNOWN if missing.
3. **What that buys** — contrast the design actually identifies. One line.
4. **What it doesn’t** — contrast they imply but do not have. One line.
5. **Leftover** — `structured` / `noise` / `cannot tell`.
6. **Decision** — label of leftover, not a second product.
7. **Ask** — omit entirely if SKIP. Else exactly two questions about leftover/controls.
8. **Do** — omit unless leftover is `structured` (see table).
9. **Invalid** — one line if a fashionable method is illegal given this design.

`leftover: structured` is **illegal** unless items 2–4 are printed for *this* experiment and the card is not thin.

## Routing

| Leftover | Decision | Do |
|---|---|---|
| Thin card (no organism **or** no modality) or noise | SKIP | None |
| cannot tell | ASK | None (the two questions are the move) |
| structured + identified | ASK, COLLAB, or INDEPENDENT | Artifact-bearing only |

Invalid Dos: writeup, outline, “flesh an appendix,” “try a foundation model.”

Default when unsure: **cannot-tell → ASK**, or **SKIP** if there is no experiment at all.

COLLAB before the talk requires `/seminar-deep` first (rare). INDEPENDENT is **not** chosen in `/seminar` unless leftover is structured; the run still waits for `/seminar-after` then `/seminar-deep`.

## Done when

File exists, ≤400 words in the body, frontmatter valid, no idea menu, SKIP/cannot-tell used when the dump is thin. Count skip rate later with grep on `decision:` / `leftover:` — not a dashboard.
