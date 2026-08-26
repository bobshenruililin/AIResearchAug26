"""P3 ablation: selection shifts that keep (X, y) pairs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from calibshift.io import mark_failed_run, write_result
from calibshift.runner import run_grid


def cells_from(cfg: dict) -> list[dict]:
    out = []
    for ds in cfg["dataset_list"]:
        for model in cfg["model_list"]:
            for seed in cfg["seeds"]:
                for shift in cfg["shifts"]:
                    out.append(
                        {
                            "dataset": ds,
                            "model": model,
                            "seed": seed,
                            "calibrators": cfg["calibrators"],
                            "shift": shift,
                            "alpha": cfg["alpha"],
                            "ece_bins": cfg["ece_bins"],
                        }
                    )
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--config", default=str(Path(__file__).with_name("config.yaml")))
    p.add_argument("--out", default=str(ROOT / "results" / "exp05_ablate_shift_family.json"))
    args = p.parse_args()
    cfg = yaml.safe_load(Path(args.config).read_text())
    try:
        payload = run_grid(cells_from(cfg))
        payload["experiment"] = "exp05_ablate_shift_family"
        payload["hypothesis"] = cfg.get("hypothesis")
        payload["config"] = cfg
        write_result(args.out, payload)
        print(f"wrote {args.out} status={payload['status']} n_ok={payload['n_ok']} n_failed={payload['n_failed']}")
    except Exception as exc:  # noqa: BLE001
        import traceback

        mark_failed_run(args.out, str(exc), traceback.format_exc())
        raise


if __name__ == "__main__":
    main()
