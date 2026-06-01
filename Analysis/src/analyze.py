from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import kruskal, spearmanr


PRIMARY_FEATURES = [
    "egemaps_F0semitoneFrom27.5Hz_sma3nz_amean_median",
    "egemaps_jitterLocal_sma3nz_amean_median",
    "egemaps_shimmerLocaldB_sma3nz_amean_median",
    "egemaps_HNRdBACF_sma3nz_amean_median",
    "egemaps_F1frequency_sma3nz_amean_median",
    "egemaps_F2frequency_sma3nz_amean_median",
    "egemaps_F3frequency_sma3nz_amean_median",
]

HORMONE_COLS = ["lh", "pdg", "e3g", "fsh"]


def phase_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for feature in PRIMARY_FEATURES:
        if feature not in df.columns:
            continue

        feature_df = df[["cycle_phase", feature]].dropna()
        if feature_df.empty:
            continue

        grouped = feature_df.groupby("cycle_phase")[feature]
        phase_stats = grouped.agg(["count", "mean", "std", "median"]).reset_index()
        phase_stats["feature"] = feature
        rows.append(phase_stats)

    if not rows:
        return pd.DataFrame(columns=["cycle_phase", "count", "mean", "std", "median", "feature"])
    return pd.concat(rows, ignore_index=True)


def kruskal_by_phase(df: pd.DataFrame) -> pd.DataFrame:
    out_rows = []
    for feature in PRIMARY_FEATURES:
        if feature not in df.columns:
            continue

        groups = []
        for _, g in df.groupby("cycle_phase", observed=True):
            vals = g[feature].dropna().values
            if len(vals) >= 2:
                groups.append(vals)

        if len(groups) < 2:
            continue

        stat, p_val = kruskal(*groups)
        k = len(groups)
        n = int(sum(len(g) for g in groups))
        eta_sq = max((stat - k + 1) / (n - k), 0.0) if n > k else np.nan

        out_rows.append(
            {
                "feature": feature,
                "kruskal_h": float(stat),
                "p_value": float(p_val),
                "eta_squared": float(eta_sq),
            }
        )

    return pd.DataFrame(out_rows).sort_values("p_value", na_position="last")


def hormone_correlations(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for feature in PRIMARY_FEATURES:
        if feature not in df.columns:
            continue
        for hormone in HORMONE_COLS:
            if hormone not in df.columns:
                continue
            pair = df[[feature, hormone]].dropna()
            if len(pair) < 6:
                continue
            rho, p_val = spearmanr(pair[feature], pair[hormone])
            rows.append(
                {
                    "feature": feature,
                    "hormone": hormone,
                    "spearman_rho": float(rho),
                    "p_value": float(p_val),
                    "n": int(len(pair)),
                }
            )
    return pd.DataFrame(rows).sort_values(["hormone", "p_value"], na_position="last")


def write_analysis_outputs(df: pd.DataFrame, output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    phase_stats = phase_summary(df)
    kruskal_stats = kruskal_by_phase(df)
    corr_stats = hormone_correlations(df)

    phase_path = output_dir / "phase_summary.csv"
    kruskal_path = output_dir / "phase_kruskal.csv"
    corr_path = output_dir / "hormone_correlations.csv"

    phase_stats.to_csv(phase_path, index=False)
    kruskal_stats.to_csv(kruskal_path, index=False)
    corr_stats.to_csv(corr_path, index=False)

    return {
        "phase_summary": phase_path,
        "phase_kruskal": kruskal_path,
        "hormone_correlations": corr_path,
    }

