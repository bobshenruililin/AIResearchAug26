# exp00_smoke

Tiny end-to-end run used by `make fresh-clone-test`.

- Dataset: sklearn `breast_cancer` (offline)
- Model: logistic regression
- One seed
- All four calibrators
- Gaussian feature mean-shift on the test set

Does **not** count as a scientific result for the paper except as a
reproducibility smoke test. Paper numbers come from later `expNN_*` runs.
