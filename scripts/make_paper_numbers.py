#!/usr/bin/env python3
"""Write paper/numbers.tex macros from results/summary_main.json and stats_tests.json."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fmt(x: float, nd: int = 3) -> str:
    return f"{x:.{nd}f}"


def pfmt(p: float) -> str:
    if p < 1e-3:
        return f"{p:.1e}"
    if p < 0.1:
        s = f"{p:.4f}".rstrip("0")
        return s if not s.endswith(".") else s + "0"
    return f"{p:.3f}"


def main() -> None:
    s = json.loads((ROOT / "results" / "summary_main.json").read_text())["payload"]
    st = json.loads((ROOT / "results" / "stats_tests.json").read_text())["payload"]
    exp04 = json.loads((ROOT / "results" / "exp04_main_h1.json").read_text())["payload"]
    cfg = exp04["config"]
    p = s["pooled_delta_ece_s1.5"]
    tests = {t["name"]: t for t in st["tests"]}
    iid = s["iid_sanity_s0_none"]
    C = s["cells"]
    help_ = s["ece_shifted_minus_none_s1.5"]

    def cell(*parts):
        return C["|".join(str(x) for x in parts)]

    macros = {
        "ExpFourN": str(s["exp04_n_ok"]),
        "ExpFourFailed": str(s["exp04_n_failed"]),
        "ExpFourSeconds": fmt(s["exp04_seconds"], 1),
        "NoneDeltaMean": fmt(p["none"]["delta_ece"]["mean"]),
        "NoneDeltaStd": fmt(p["none"]["delta_ece"]["std"]),
        "NoneNPos": str(p["none"]["n_pos"]),
        "NoneNNeg": str(p["none"]["n_neg"]),
        "NoneN": str(p["none"]["n"]),
        "TempDeltaMean": fmt(p["temperature"]["delta_ece"]["mean"]),
        "TempDeltaStd": fmt(p["temperature"]["delta_ece"]["std"]),
        "IsoDeltaMean": fmt(p["isotonic"]["delta_ece"]["mean"]),
        "IsoDeltaStd": fmt(p["isotonic"]["delta_ece"]["std"]),
        "HistDeltaMean": fmt(p["histogram"]["delta_ece"]["mean"]),
        "HistDeltaStd": fmt(p["histogram"]["delta_ece"]["std"]),
        "NonePooledP": pfmt(tests["wilcoxon_delta_ece_gt0_s1.5_none_pooled"]["p_greater"]),
        "TempPooledP": pfmt(tests["wilcoxon_delta_ece_gt0_s1.5_temperature_pooled"]["p_greater"]),
        "IsoPooledP": pfmt(tests["wilcoxon_delta_ece_gt0_s1.5_isotonic_pooled"]["p_greater"]),
        "HistPooledP": pfmt(tests["wilcoxon_delta_ece_gt0_s1.5_histogram_pooled"]["p_greater"]),
        "BcLogregAcc": fmt(iid["breast_cancer|logreg|none"]["acc"]["mean"]),
        "BcLogregEce": fmt(iid["breast_cancer|logreg|none"]["ece"]["mean"]),
        "BcLogregEceStd": fmt(iid["breast_cancer|logreg|none"]["ece"]["std"]),
        "WineRfEceIid": fmt(iid["wine|rf|none"]["ece"]["mean"]),
        "WineRfEceIidStd": fmt(iid["wine|rf|none"]["ece"]["std"]),
        "WineLogregAcc": fmt(iid["wine|logreg|none"]["acc"]["mean"]),
        "BcHgbDelta": fmt(cell("breast_cancer", "hgb", "s1.5", "none")["delta_ece"]["mean"]),
        "BcHgbDeltaStd": fmt(cell("breast_cancer", "hgb", "s1.5", "none")["delta_ece"]["std"]),
        "SynthLogregDelta": fmt(cell("synthetic_shift", "logreg", "s1.5", "none")["delta_ece"]["mean"]),
        "SynthLogregDeltaStd": fmt(cell("synthetic_shift", "logreg", "s1.5", "none")["delta_ece"]["std"]),
        "BcLogregCovSZero": fmt(cell("breast_cancer", "logreg", "s0.0", "none")["coverage_shifted"]["mean"]),
        "BcLogregCovSOneFive": fmt(cell("breast_cancer", "logreg", "s1.5", "none")["coverage_shifted"]["mean"]),
        "BcLogregCovSTwoFive": fmt(cell("breast_cancer", "logreg", "s2.5", "none")["coverage_shifted"]["mean"]),
        "SynthLogregCovSOneFive": fmt(cell("synthetic_shift", "logreg", "s1.5", "none")["coverage_shifted"]["mean"]),
        "WineRfIsoHelp": fmt(help_["wine|rf|isotonic"]["mean"]),
        "BcLogregIsoHelp": fmt(help_["breast_cancer|logreg|isotonic"]["mean"]),
        "WineRfTempSh": fmt(cell("wine", "rf", "s1.5", "temperature")["ece_shifted"]["mean"]),
        "WineRfNoneSh": fmt(cell("wine", "rf", "s1.5", "none")["ece_shifted"]["mean"]),
        "TempNPos": str(p["temperature"]["n_pos"]),
        "TempNNeg": str(p["temperature"]["n_neg"]),
        "IsoNPos": str(p["isotonic"]["n_pos"]),
        "IsoNNeg": str(p["isotonic"]["n_neg"]),
        "HistNPos": str(p["histogram"]["n_pos"]),
        "HistNNeg": str(p["histogram"]["n_neg"]),
        "NoiseSynthRf": fmt(s["exp07_noise_feature_delta_ece"]["synthetic_shift|rf|none"]["mean"]),
        "PredSynthRf": fmt(cell("synthetic_shift", "rf", "s1.5", "none")["delta_ece"]["mean"]),
        "NSeeds": str(len(cfg["seeds"])),
        "Alpha": str(cfg["alpha"]),
        "EceBins": str(cfg["ece_bins"]),
        "NTests": str(len(st["tests"])),
        "TwelveMeanP": pfmt(tests["wilcoxon_delta_ece_gt0_s1.5_none_dataset_model_means"]["p_greater"]),
        "TwelveMeanNPos": str(tests["wilcoxon_delta_ece_gt0_s1.5_none_dataset_model_means"]["n_pos"]),
        "TwelveMeanN": str(tests["wilcoxon_delta_ece_gt0_s1.5_none_dataset_model_means"]["n"]),
        "QuantileSliceDeltaMean": fmt(s["exp05_none_quantile_slice_cellmean_delta_ece"]["mean"]),
        "QuantileSliceDeltaStd": fmt(s["exp05_none_quantile_slice_cellmean_delta_ece"]["std"]),
        "ImpResampleDeltaMean": fmt(s["exp05_none_importance_resample_cellmean_delta_ece"]["mean"]),
        "ImpResampleDeltaStd": fmt(s["exp05_none_importance_resample_cellmean_delta_ece"]["std"]),
        "SynthLogregAccIid": fmt(cell("synthetic_shift", "logreg", "s0.0", "none")["acc_iid"]["mean"]),
        "SynthLogregAccShifted": fmt(cell("synthetic_shift", "logreg", "s1.5", "none")["acc_shifted"]["mean"]),
        "SklearnDeltaMean": fmt(s["pooled_none_s1.5_by_corpus"]["sklearn"]["delta_ece"]["mean"]),
        "SklearnDeltaStd": fmt(s["pooled_none_s1.5_by_corpus"]["sklearn"]["delta_ece"]["std"]),
        "SklearnNPos": str(s["pooled_none_s1.5_by_corpus"]["sklearn"]["n_pos"]),
        "SklearnNNeg": str(s["pooled_none_s1.5_by_corpus"]["sklearn"]["n_neg"]),
        "SklearnN": str(s["pooled_none_s1.5_by_corpus"]["sklearn"]["n"]),
        "SynthDeltaMean": fmt(s["pooled_none_s1.5_by_corpus"]["synthetic"]["delta_ece"]["mean"]),
        "SynthDeltaStd": fmt(s["pooled_none_s1.5_by_corpus"]["synthetic"]["delta_ece"]["std"]),
        "SynthNPos": str(s["pooled_none_s1.5_by_corpus"]["synthetic"]["n_pos"]),
        "SynthNNeg": str(s["pooled_none_s1.5_by_corpus"]["synthetic"]["n_neg"]),
        "SynthN": str(s["pooled_none_s1.5_by_corpus"]["synthetic"]["n"]),
        "NoneDeltaAccMean": fmt(s["pooled_none_s1.5_other_metrics"]["delta_acc"]["mean"]),
        "NoneDeltaBrierMean": fmt(s["pooled_none_s1.5_other_metrics"]["delta_brier"]["mean"]),
        "NoneDeltaNllMean": fmt(s["pooled_none_s1.5_other_metrics"]["delta_nll"]["mean"]),
        "WineRfIsoSh": fmt(cell("wine", "rf", "s1.5", "isotonic")["ece_shifted"]["mean"]),
        "ExpFiveN": str(s["exp05_n_dataset_model"]),
        "ExpFiveNDs": str(len(s["exp05_datasets"])),
        "MatchedGaussDeltaMean": fmt(s["exp05_matched_gaussian_none_cellmean_delta_ece"]["mean"]),
        "MatchedGaussDeltaStd": fmt(s["exp05_matched_gaussian_none_cellmean_delta_ece"]["std"]),
        "QuantileDeltaAccMean": fmt(s["exp05_quantile_slice_none_cellmean_delta_acc"]["mean"]),
        "MatchedGaussDeltaAccMean": fmt(s["exp05_matched_gaussian_none_cellmean_delta_acc"]["mean"]),
        "WineNTest": str(s["exp04_split_sizes"]["wine"]["n_test"]),
        "WineNCal": str(s["exp04_split_sizes"]["wine"]["n_cal"]),
        "BcLogregCovSZeroStd": fmt(cell("breast_cancer", "logreg", "s0.0", "none")["coverage_shifted"]["std"]),
        "BcLogregCovSOneFiveStd": fmt(cell("breast_cancer", "logreg", "s1.5", "none")["coverage_shifted"]["std"]),
        "SynthLogregCovSOneFiveStd": fmt(cell("synthetic_shift", "logreg", "s1.5", "none")["coverage_shifted"]["std"]),
        "DatasetSignP": pfmt(tests["sign_delta_ece_gt0_s1.5_none_dataset_means"]["p_greater"]),
        "DatasetSignN": str(tests["sign_delta_ece_gt0_s1.5_none_dataset_means"]["n"]),
    }
    lines = [
        "% Auto-generated by scripts/make_paper_numbers.py from results/*.json.",
        "% Do not edit by hand.",
    ]
    for k, v in macros.items():
        lines.append(rf"\newcommand{{\Num{k}}}{{{v}}}")
    path = ROOT / "paper" / "numbers.tex"
    path.write_text("\n".join(lines) + "\n")
    print("wrote", path, "n_macros", len(macros))


if __name__ == "__main__":
    main()
