"""sklearn model factory. All models expose predict_proba."""

from __future__ import annotations

from sklearn.base import BaseEstimator
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def get_model(name: str, seed: int) -> BaseEstimator:
    name = name.lower()
    if name in {"logreg", "logistic"}:
        return Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "clf",
                    LogisticRegression(
                        max_iter=1000,
                        random_state=seed,
                        solver="lbfgs",
                    ),
                ),
            ]
        )
    if name in {"rf", "random_forest"}:
        return RandomForestClassifier(
            n_estimators=100,
            min_samples_leaf=2,
            random_state=seed,
            n_jobs=1,
        )
    if name in {"hgb", "hist_gbdt"}:
        return HistGradientBoostingClassifier(
            max_depth=6,
            learning_rate=0.08,
            max_iter=120,
            random_state=seed,
        )
    raise ValueError(f"Unknown model: {name}")


MODEL_NAMES = ["logreg", "rf", "hgb"]
