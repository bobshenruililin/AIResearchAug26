# Decision log (append-only)

## 2026-08-26 — Topic lock (P0)

**Decision:** Study post-hoc probability calibration under covariate shift on
small tabular datasets with sklearn models (LogReg, RandomForest,
HistGradientBoosting). Calibrators: none / temperature scaling / isotonic /
histogram binning. Also measure split-conformal coverage as a secondary lens.

**Why:** Environment is 4×CPU, 16 GB RAM, no GPU, $0 API. LLM/RAG/GRPO topics
in the GOAL template are infeasible without fabricating scale. Calibration
under shift is a real literature gap for *classical tabular* models (most
evidence is ImageNet/deep nets). Negative results are acceptable and likely.

**Rejected alternatives:**
- GRPO reward hacking: needs GPU + RL training.
- RAG retrieval-noise: needs embeddings + reader LM.
- Jailbreak transfer: API cost and dual-use risk; not reproducible at $0.

**Integrity:** All numbers from `results/*.json`. No hand-edited results.

## 2026-08-26 — Engineer proposals (P0)

Fable and Sol both proposed sklearn + venv + experiment dirs. **Agreement:**
metrics, shift mechanisms, atomic JSON writer, no OpenML in tests.
**Disagreement:** Sol wanted `results/` gitignored. **Rejected** — GOAL.md
requires `results/*.json` as the paper's source of truth, so they are
committed. Package name: kept `calibshift` (fable). Pins: the versions that
actually installed and passed tests on this machine.

## 2026-08-26 — Literature merge (P1)

Sol delivered 27 S2-verified papers. Orchestrator arXiv pass added
title-matched IDs. Union after dedupe: **47 verified**. Fable lit agent had
not finished writing `/tmp/lit_fable/papers.json` at merge time; Sol +
orchestrator already exceeded the 20-paper floor with API evidence, so P1
was not blocked. Unverified classics (Platt 1999, Zadrozny 2001, Shimodaira
2000, beta-calibration arXiv mismatch) were **excluded** from `verified.bib`.
