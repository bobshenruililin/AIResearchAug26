"""Unit tests that must pass on a fresh clone after `make setup`."""

from __future__ import annotations

import json
import numpy as np
import pytest

from calibshift.calibrators import get_calibrator
from calibshift.conformal import conformal_coverage, split_conformal_quantile
from calibshift.data import load_dataset
from calibshift.io import write_result
from calibshift.metrics import brier_score, expected_calibration_error, negative_log_likelihood
from calibshift.models import get_model
from calibshift.shift import gaussian_feature_shift
from calibshift.split import three_way_split


def test_ece_perfectly_calibrated_binary():
    rng = np.random.default_rng(0)
    p1 = rng.uniform(0.1, 0.9, size=8000)
    y = (rng.uniform(size=8000) < p1).astype(int)
    p = np.column_stack([1 - p1, p1])
    ece = expected_calibration_error(y, p, n_bins=10)
    assert ece < 0.03


def test_ece_overconfident():
    rng = np.random.default_rng(1)
    p1 = np.full(4000, 0.95)
    y = rng.binomial(1, 0.55, size=4000)
    ece = expected_calibration_error(y, p1, n_bins=10)
    assert ece > 0.3


def test_brier_range():
    y = np.array([0, 1, 1, 0])
    p = np.array([0.1, 0.9, 0.8, 0.2])
    b = brier_score(y, p)
    assert 0 <= b <= 2


def test_temperature_increases_entropy_when_overconfident():
    rng = np.random.default_rng(2)
    logits = rng.normal(3.0, 0.5, size=(400, 2))
    e = np.exp(logits - logits.max(axis=1, keepdims=True))
    p = e / e.sum(axis=1, keepdims=True)
    y = rng.integers(0, 2, size=400)
    cal = get_calibrator("temperature").fit(p, y)
    p2 = cal.transform(p)
    assert negative_log_likelihood(y, p2) <= negative_log_likelihood(y, p) + 1e-9
    assert cal.T > 0


def test_isotonic_binary_monotonic():
    rng = np.random.default_rng(3)
    x = np.linspace(0, 1, 300)
    y = (x + rng.normal(0, 0.05, size=300) > 0.5).astype(int)
    p = np.column_stack([1 - x, x])
    cal = get_calibrator("isotonic").fit(p, y)
    out = cal.transform(p)
    assert np.all(np.diff(out[:, 1]) >= -1e-8)


def test_conformal_iid_coverage_ballpark():
    rng = np.random.default_rng(4)
    p1 = rng.uniform(0.2, 0.8, size=2000)
    y = (rng.uniform(size=2000) < p1).astype(int)
    p = np.column_stack([1 - p1, p1])
    q = split_conformal_quantile(y[:1000], p[:1000], alpha=0.1)
    cov = conformal_coverage(y[1000:], p[1000:], q)
    assert 0.85 <= cov <= 0.98


def test_split_and_shift_shapes():
    ds = load_dataset("breast_cancer")
    parts = three_way_split(ds.X, ds.y, seed=0)
    rng = np.random.default_rng(0)
    Xs, ys, meta = gaussian_feature_shift(parts["X_test"], parts["y_test"], rng, strength=1.0, n_features=3)
    assert Xs.shape == parts["X_test"].shape
    assert ys.shape == parts["y_test"].shape
    assert meta["kind"] == "gaussian_feature_shift"


def test_model_predict_proba():
    ds = load_dataset("synthetic_shift", seed=0)
    parts = three_way_split(ds.X, ds.y, seed=0)
    model = get_model("logreg", seed=0)
    model.fit(parts["X_train"], parts["y_train"])
    p = model.predict_proba(parts["X_test"])
    assert p.shape == (len(parts["y_test"]), 2)
    np.testing.assert_allclose(p.sum(axis=1), 1.0, atol=1e-6)


def test_write_result_roundtrip(tmp_path):
    path = tmp_path / "foo.json"
    write_result(path, {"status": "ok", "ece": 0.1})
    data = json.loads(path.read_text())
    assert data["schema"] == "calibshift.result.v1"
    assert data["payload"]["ece"] == 0.1


@pytest.mark.parametrize("name", ["breast_cancer", "wine", "synthetic_shift", "synthetic_multiclass"])
def test_datasets_load(name):
    ds = load_dataset(name, seed=0)
    assert ds.X.ndim == 2
    assert len(ds.y) == len(ds.X)
    assert ds.n_classes >= 2
