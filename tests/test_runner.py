from calibshift.runner import run_one_cell


def test_runner_one_cell_smoke():
    payload = run_one_cell(
        {
            "dataset": "synthetic_shift",
            "model": "logreg",
            "seed": 0,
            "calibrators": ["none", "temperature"],
            "shift": {"kind": "gaussian_feature_shift", "strength": 1.0, "n_features": 2},
            "n_cal": 80,
            "alpha": 0.1,
            "ece_bins": 10,
        }
    )
    assert payload["status"] == "ok"
    assert len(payload["rows"]) == 2
    assert "delta_ece" in payload["rows"][0]
    assert "coverage_shifted_weighted" in payload["rows"][0]["conformal"]
