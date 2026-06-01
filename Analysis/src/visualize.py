from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


sns.set_theme(style="whitegrid")


def _save(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def plot_time_series(df: pd.DataFrame, out_path: Path) -> None:
    feature = "egemaps_F0semitoneFrom27.5Hz_sma3nz_amean_median"
    if feature not in df.columns:
        return

    plot_df = df.sort_values("date").copy()
    fig, ax1 = plt.subplots(figsize=(11, 4.5))

    ax1.plot(plot_df["date"], plot_df[feature], color="#1f77b4", label="Voice F0 (median)")
    ax1.set_ylabel("F0 (semitones)", color="#1f77b4")
    ax1.tick_params(axis="y", labelcolor="#1f77b4")
    ax1.set_xlabel("Date")
    ax1.set_title("Voice F0 and Hormone Trends")

    ax2 = ax1.twinx()
    if "lh" in plot_df.columns:
        ax2.plot(plot_df["date"], plot_df["lh"], color="#d62728", alpha=0.7, label="LH")
    if "pdg" in plot_df.columns:
        ax2.plot(plot_df["date"], plot_df["pdg"], color="#2ca02c", alpha=0.7, label="PdG")
    ax2.set_ylabel("Hormones")

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    if lines1 or lines2:
        ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

    _save(fig, out_path)


def plot_phase_boxplots(df: pd.DataFrame, out_path: Path) -> None:
    features = [
        "egemaps_F0semitoneFrom27.5Hz_sma3nz_amean_median",
        "egemaps_jitterLocal_sma3nz_amean_median",
        "egemaps_shimmerLocaldB_sma3nz_amean_median",
        "egemaps_HNRdBACF_sma3nz_amean_median",
    ]
    feature = next((f for f in features if f in df.columns), None)
    if feature is None:
        return

    plot_df = df[["cycle_phase", feature]].dropna()
    if plot_df.empty:
        return

    fig, ax = plt.subplots(figsize=(8, 4.5))
    sns.boxplot(data=plot_df, x="cycle_phase", y=feature, ax=ax)
    sns.stripplot(data=plot_df, x="cycle_phase", y=feature, color="black", alpha=0.45, size=4, ax=ax)
    ax.set_title(f"{feature} by Cycle Phase")
    ax.set_xlabel("Cycle phase")
    ax.set_ylabel("Value")
    _save(fig, out_path)


def plot_hormone_voice_heatmap(df: pd.DataFrame, out_path: Path) -> None:
    cols = [
        "egemaps_F0semitoneFrom27.5Hz_sma3nz_amean_median",
        "egemaps_jitterLocal_sma3nz_amean_median",
        "egemaps_shimmerLocaldB_sma3nz_amean_median",
        "egemaps_HNRdBACF_sma3nz_amean_median",
        "lh",
        "pdg",
        "e3g",
        "fsh",
    ]
    present = [c for c in cols if c in df.columns]
    corr_df = df[present].dropna(how="all")
    if corr_df.empty or len(present) < 3:
        return

    corr = corr_df.corr(method="spearman", numeric_only=True)
    fig, ax = plt.subplots(figsize=(8.5, 6.5))
    sns.heatmap(corr, cmap="coolwarm", center=0, annot=False, square=True, ax=ax)
    ax.set_title("Spearman Correlation: Voice Features vs Hormones")
    _save(fig, out_path)

