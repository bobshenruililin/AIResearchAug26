"""Dataset loaders that work fully offline (sklearn built-ins + synthetic)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.datasets import load_breast_cancer, load_wine, make_classification


@dataclass
class TabularDataset:
    name: str
    X: np.ndarray
    y: np.ndarray
    n_classes: int
    source: str


def _clean(X: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    X = np.asarray(X, dtype=np.float64)
    y = np.asarray(y)
    _, y = np.unique(y, return_inverse=True)
    return X, y.astype(int)


def load_dataset(name: str, seed: int = 0) -> TabularDataset:
    name = name.lower()
    if name == "breast_cancer":
        bunch = load_breast_cancer()
        X, y = _clean(bunch.data, bunch.target)
        return TabularDataset(name, X, y, int(y.max() + 1), "sklearn")
    if name == "wine":
        bunch = load_wine()
        X, y = _clean(bunch.data, bunch.target)
        return TabularDataset(name, X, y, int(y.max() + 1), "sklearn")
    if name == "synthetic_shift":
        rng = np.random.default_rng(seed)
        X, y = make_classification(
            n_samples=2000,
            n_features=12,
            n_informative=5,
            n_redundant=2,
            n_classes=2,
            class_sep=1.2,
            flip_y=0.02,
            random_state=seed,
        )
        X = np.asarray(X, dtype=np.float64)
        # Make feature 0 mildly correlated with label so slicing it is a shift.
        X[:, 0] = X[:, 0] + 0.4 * (2 * y - 1) + rng.normal(0, 0.1, size=len(y))
        y = y.astype(int)
        return TabularDataset(name, X, y, 2, "sklearn.make_classification")
    if name == "synthetic_multiclass":
        X, y = make_classification(
            n_samples=1800,
            n_features=10,
            n_informative=6,
            n_redundant=1,
            n_classes=3,
            n_clusters_per_class=1,
            class_sep=1.4,
            random_state=seed,
        )
        return TabularDataset(name, np.asarray(X, dtype=np.float64), y.astype(int), 3, "sklearn.make_classification")
    raise ValueError(f"Unknown dataset: {name}")


DATASET_NAMES = ["breast_cancer", "wine", "synthetic_shift", "synthetic_multiclass"]
