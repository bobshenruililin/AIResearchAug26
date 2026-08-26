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
