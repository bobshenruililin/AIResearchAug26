"""Train/cal/test split helper."""

from __future__ import annotations

import numpy as np
from sklearn.model_selection import train_test_split


def three_way_split(
    X: np.ndarray,
    y: np.ndarray,
    seed: int,
    train_frac: float = 0.5,
    cal_frac_of_rest: float = 0.5,
) -> dict[str, np.ndarray]:
    X_train, X_rest, y_train, y_rest = train_test_split(
        X, y, train_size=train_frac, random_state=seed, stratify=y
    )
    X_cal, X_test, y_cal, y_test = train_test_split(
        X_rest, y_rest, train_size=cal_frac_of_rest, random_state=seed + 1, stratify=y_rest
    )
    return {
        "X_train": X_train,
        "y_train": y_train,
        "X_cal": X_cal,
        "y_cal": y_cal,
        "X_test": X_test,
        "y_test": y_test,
    }
