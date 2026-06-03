"""Phase 2 plotting workflow: voice features vs hormone rate-of-change overlays."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd


@dataclass(frozen=True)
class Phase2RatePlotArtifacts:
    figures_output_dir: Path


def _rolling_mean(series: pd.Series, window_days: int) -> pd.Series:
    min_periods = max(2, window_days // 2)
    return series.rolling(window=window_days, min_periods=min_periods, center=True).mean()


def _min_max_normalize(series: pd.Series) -> pd.Series:
    valid = series.dropna()
    if valid.empty:
        return series * float("nan")
    low = valid.min()
    high = valid.max()
    if pd.isna(low) or pd.isna(high) or low == high:
        return pd.Series(0.5, index=series.index, dtype="float64")
    return (series - low) / (high - low)


def _build_daily_feature_frame(
    merged: pd.DataFrame,
    *,
    candidate_features: list[str],
    start_date: pd.Timestamp,
) -> pd.DataFrame:
    existing_feature_columns = [column for column in candidate_features if column in merged.columns]
    daily = (
        merged[["date", *existing_feature_columns]]
        .copy()
        .assign(date=lambda frame: pd.to_datetime(frame["date"], errors="coerce"))
        .dropna(subset=["date"])
        .groupby("date", as_index=False)
        .mean(numeric_only=True)
        .sort_values("date")
    )
    return daily[daily["date"] >= start_date].copy()


def _build_daily_hormone_rate_frame(
    merged: pd.DataFrame,
    *,
    hormone_columns: list[str],
    start_date: pd.Timestamp,
) -> pd.DataFrame:
    daily = (
        merged[["date", *[column for column in hormone_columns if column in merged.columns]]]
        .copy()
        .assign(date=lambda frame: pd.to_datetime(frame["date"], errors="coerce"))
        .dropna(subset=["date"])
        .groupby("date", as_index=False)
        .mean(numeric_only=True)
        .sort_values("date")
    )
    daily = daily[daily["date"] >= start_date].copy()

    for hormone in hormone_columns:
        if hormone not in daily.columns:
            continue
        value = pd.to_numeric(daily[hormone], errors="coerce")
        date = daily["date"]
        observed = value.notna()
        prev_observed_value = value.where(observed).ffill().shift(1)
        prev_observed_date = date.where(observed).ffill().shift(1)
        days_since_prev_observed = (date - prev_observed_date).dt.days
        delta = value - prev_observed_value
        daily[f"{hormone}_rate_change_per_day"] = delta / days_since_prev_observed

    return daily


def _build_period_calendar_frame(merged: pd.DataFrame, *, start_date: pd.Timestamp) -> pd.DataFrame:
    fields = [column for column in ["date", "cycle_day"] if column in merged.columns]
    if "date" not in fields:
        return pd.DataFrame(columns=["date", "cycle_day"])
    daily = (
        merged[fields]
        .copy()
        .assign(date=lambda frame: pd.to_datetime(frame["date"], errors="coerce"))
        .dropna(subset=["date"])
        .sort_values("date")
        .drop_duplicates(subset=["date"], keep="last")
    )
    if "cycle_day" in daily.columns:
        daily["cycle_day"] = pd.to_numeric(daily["cycle_day"], errors="coerce")
    return daily[daily["date"] >= start_date].copy()


def _plot_period_day_bar(ax: plt.Axes, calendar: pd.DataFrame) -> None:
    if calendar.empty or "cycle_day" not in calendar.columns:
        return
    period_days = calendar[calendar["cycle_day"].between(1, 5, inclusive="both")]["date"]
    for day in period_days:
        ax.axvspan(
            day - pd.Timedelta(hours=12),
            day + pd.Timedelta(hours=12),
            ymin=0.0,
            ymax=0.04,
            color="crimson",
            alpha=0.28,
            linewidth=0.0,
            zorder=3,
        )


def _plot_window_figure(
    *,
    daily_features: pd.DataFrame,
    daily_hormones: pd.DataFrame,
    calendar: pd.DataFrame,
    candidate_features: list[str],
    hormone_columns: list[str],
    window_days: int,
    output_path: Path,
) -> None:
    features_to_plot = [column for column in candidate_features if column in daily_features.columns]
    hormones_to_plot = [f"{column}_rate_change_per_day" for column in hormone_columns if f"{column}_rate_change_per_day" in daily_hormones.columns]
    if not features_to_plot or not hormones_to_plot:
        return

    feature_has_value = daily_features[features_to_plot].notna().any(axis=1)
    hormone_has_value = daily_hormones[hormones_to_plot].notna().any(axis=1)
    date_candidates = pd.concat(
        [
            daily_features.loc[feature_has_value, "date"],
            daily_hormones.loc[hormone_has_value, "date"],
        ],
        ignore_index=True,
    ).dropna()
    if date_candidates.empty:
        return
    plot_start = date_candidates.min() - pd.Timedelta(days=1)
    plot_end = date_candidates.max() + pd.Timedelta(days=1)

    hormone_palette = {
        "e3g_rate_change_per_day": ("#ff8c00", "#ffb869"),
        "pdg_rate_change_per_day": ("#00a878", "#8ce6cf"),
    }

    fig, axes = plt.subplots(len(features_to_plot), 1, figsize=(16, 3.6 * len(features_to_plot)), sharex=True)
    if len(features_to_plot) == 1:
        axes = [axes]

    for idx, feature in enumerate(features_to_plot):
        ax = axes[idx]
        hormone_ax = ax.twinx()

        feature_series = pd.to_numeric(daily_features[feature], errors="coerce")
        feature_roll = _rolling_mean(feature_series, window_days=window_days)

        ax.scatter(
            daily_features["date"],
            feature_series,
            color="lightgray",
            s=12,
            alpha=0.35,
            label="Daily feature",
            zorder=1,
        )
        ax.plot(
            daily_features["date"],
            feature_roll,
            color="#1f65ff",
            linewidth=2.0,
            label=f"Feature {window_days}-day rolling",
            zorder=4,
        )

        for hormone_rate in hormones_to_plot:
            hormone_raw = pd.to_numeric(daily_hormones[hormone_rate], errors="coerce")
            hormone_roll = _rolling_mean(hormone_raw, window_days=window_days)
            hormone_norm = _min_max_normalize(hormone_roll)

            strong_color, faint_color = hormone_palette.get(hormone_rate, ("#0f766e", "#9fd9d4"))
            hormone_ax.plot(
                daily_hormones["date"],
                _min_max_normalize(hormone_raw),
                color=faint_color,
                linewidth=0.8,
                alpha=0.45,
                label=f"{hormone_rate} (norm)",
                zorder=1,
            )
            hormone_ax.plot(
                daily_hormones["date"],
                hormone_norm,
                color=strong_color,
                linewidth=1.5,
                label=f"{hormone_rate} {window_days}-day rolling (norm)",
                zorder=2,
            )

        period_starts = calendar[calendar["cycle_day"] == 1]["date"] if "cycle_day" in calendar.columns else pd.Series(dtype="datetime64[ns]")
        for period_start in period_starts:
            ax.axvline(period_start, color="red", linewidth=1.1, alpha=0.85, zorder=5)
        _plot_period_day_bar(ax, calendar)

        ax.set_title(feature.replace("prosody_egemaps_", "").replace("_", " "))
        ax.set_ylabel("Feature value")
        hormone_ax.set_ylabel("Hormone rate normalized")
        hormone_ax.set_ylim(-0.05, 1.05)
        ax.grid(alpha=0.22, linewidth=0.8)
        ax.set_xlim(plot_start, plot_end)
        ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))

        if idx == 0:
            left_handles, left_labels = ax.get_legend_handles_labels()
            right_handles, right_labels = hormone_ax.get_legend_handles_labels()
            if period_starts.shape[0] > 0:
                period_handle = plt.Line2D([0], [0], color="red", linewidth=1.2, label="Period start")
                left_handles.append(period_handle)
                left_labels.append("Period start")
            period_bar_handle = plt.Line2D([0], [0], color="crimson", linewidth=6, alpha=0.35, label="Period day (1-5)")
            left_handles.append(period_bar_handle)
            left_labels.append("Period day (1-5)")
            ax.legend(left_handles + right_handles, left_labels + right_labels, loc="upper right", fontsize=8)

    axes[-1].set_xlabel("Date (2026)")
    fig.suptitle(f"Prosody Features with Smoothed Hormone Rate Overlay ({window_days}-day)", fontsize=13, y=0.995)
    fig.autofmt_xdate(rotation=0)
    fig.tight_layout(rect=(0, 0, 1, 0.985))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def run_phase2_hormone_rate_plots(
    *,
    merged_input_path: Path,
    artifacts: Phase2RatePlotArtifacts,
    candidate_features: list[str],
    hormone_columns: list[str],
    rolling_windows: list[int],
    start_date: pd.Timestamp,
) -> list[Path]:
    merged = pd.read_parquet(merged_input_path)
    daily_features = _build_daily_feature_frame(
        merged=merged,
        candidate_features=candidate_features,
        start_date=start_date,
    )
    daily_hormones = _build_daily_hormone_rate_frame(
        merged=merged,
        hormone_columns=hormone_columns,
        start_date=start_date,
    )
    calendar = _build_period_calendar_frame(merged=merged, start_date=start_date)

    written: list[Path] = []
    for window_days in rolling_windows:
        hormone_label = "_".join(hormone_columns)
        output_path = artifacts.figures_output_dir / (
            f"prosody_{window_days}day_rolling_with_{hormone_label}_rate_change_smoothed.png"
        )
        _plot_window_figure(
            daily_features=daily_features,
            daily_hormones=daily_hormones,
            calendar=calendar,
            candidate_features=candidate_features,
            hormone_columns=hormone_columns,
            window_days=window_days,
            output_path=output_path,
        )
        written.append(output_path)

    return written
