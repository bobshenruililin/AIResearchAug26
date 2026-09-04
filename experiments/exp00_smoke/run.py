"""Smoke experiment: one seed, one dataset, one model, tiny runtime.

Writes results/exp00_smoke.json. Used by the fresh-clone test.
"""

from __future__ import annotations

import argparse
import sys
import time
import traceback
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from calibshift.calibrators import get_calibrator
from calibshift.data import load_dataset
from calibshift.eval import conformal_pack, score_pack
from calibshift.io import mark_failed_run, write_result
from calibshift.models import get_model
from calibshift.shift import gaussian_feature_shift
from calibshift.split import three_way_split


def run(config: dict) -> dict:
    t0 = time.time()
    ds = load_dataset(config["dataset"], seed=config["seed"])
    parts = three_way_split(ds.X, ds.y, seed=config["seed"])
    model = get_model(config["model"], seed=config["seed"])
    model.fit(parts["X_train"], parts["y_train"])
    p_cal = model.predict_proba(parts["X_cal"])
    p_iid = model.predict_proba(parts["X_test"])
    rng = np.random.default_rng(config["seed"] + 99)
    X_shift, y_shift, shift_meta = gaussian_feature_shift(
        parts["X_test"],
        parts["y_test"],
        rng,
        strength=config["shift_strength"],
        n_features=config.get("n_shift_features"),
    )
    p_shift = model.predict_proba(X_shift)

    rows = []
    for cal_name in config["calibrators"]:
        cal = get_calibrator(cal_name)
        cal.fit(p_cal, parts["y_cal"])
        p_iid_c = cal.transform(p_iid)
        p_sh_c = cal.transform(p_shift)
        p_cal_c = cal.transform(p_cal)
        row = {
            "calibrator": cal_name,
            "temperature_T": getattr(cal, "T", None),
            "iid": score_pack(parts["y_test"], p_iid_c),
            "shifted": score_pack(y_shift, p_sh_c),
            "conformal_iid": conformal_pack(
                parts["y_cal"], p_cal_c, parts["y_test"], p_iid_c, alpha=config["alpha"]
            ),
            "conformal_shifted": conformal_pack(
                parts["y_cal"], p_cal_c, y_shift, p_sh_c, alpha=config["alpha"]
            ),
        }
        rows.append(row)

    return {
        "status": "ok",
        "experiment": "exp00_smoke",
        "config": config,
        "n_train": int(len(parts["y_train"])),
        "n_cal": int(len(parts["y_cal"])),
        "n_test": int(len(parts["y_test"])),
        "n_classes": int(ds.n_classes),
        "shift": shift_meta,
        "seconds": time.time() - t0,
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(Path(__file__).with_name("config.yaml")))
    parser.add_argument("--out", default=str(ROOT / "results" / "exp00_smoke.json"))
    args = parser.parse_args()
    config = yaml.safe_load(Path(args.config).read_text())
    try:
        payload = run(config)
        write_result(args.out, payload)
        print(f"wrote {args.out}")
    except Exception as exc:  # noqa: BLE001 — we persist failures, never hide them
        mark_failed_run(args.out, str(exc), traceback.format_exc())
        raise


if __name__ == "__main__":
    main()
