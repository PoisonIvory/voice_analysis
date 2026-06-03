"""Generate one presentation-ready hormone-rate overlay chart."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd


@dataclass(frozen=True)
class PresentationChartArtifacts:
    output_path: Path


def _rolling_mean(series: pd.Series, window_days: int) -> pd.Series:
    min_periods = max(3, window_days // 2)
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


def _daily_hormone_rates(daily: pd.DataFrame, hormone_columns: list[str]) -> pd.DataFrame:
    out = daily.copy()
    for hormone in hormone_columns:
        if hormone not in out.columns:
            continue
        value = pd.to_numeric(out[hormone], errors="coerce")
        date = out["date"]
        observed = value.notna()
        prev_observed_value = value.where(observed).ffill().shift(1)
        prev_observed_date = date.where(observed).ffill().shift(1)
        days_since_prev_observed = (date - prev_observed_date).dt.days
        out[f"{hormone}_rate_change_per_day"] = (value - prev_observed_value) / days_since_prev_observed
    return out


def run_phase2_presentation_chart(
    *,
    merged_input_path: Path,
    artifacts: PresentationChartArtifacts,
    feature_column: str,
    hormone_columns: list[str],
    smoothing_window_days: int,
    start_date: pd.Timestamp,
    signal_mode: str,
    gap_aware: bool = False,
) -> Path:
    merged = pd.read_parquet(merged_input_path)
    merged["date"] = pd.to_datetime(merged["date"], errors="coerce")
    merged = merged.dropna(subset=["date"]).copy()
    calendar = (
        merged[[column for column in ["date", "cycle_day", "cycle_start_date"] if column in merged.columns]]
        .copy()
        .dropna(subset=["date"])
        .sort_values("date")
        .drop_duplicates(subset=["date"], keep="last")
    )
    if "cycle_day" in calendar.columns:
        calendar["cycle_day"] = pd.to_numeric(calendar["cycle_day"], errors="coerce")
    if "cycle_start_date" in calendar.columns:
        calendar["cycle_start_date"] = pd.to_datetime(calendar["cycle_start_date"], errors="coerce")

    keep_columns = ["date", feature_column, *[h for h in hormone_columns if h in merged.columns], "cycle_day"]
    keep_columns = [c for c in keep_columns if c in merged.columns]
    daily = (
        merged[keep_columns]
        .groupby("date", as_index=False)
        .mean(numeric_only=True)
        .sort_values("date")
    )
    daily = daily[daily["date"] >= start_date].copy()
    daily = _daily_hormone_rates(daily, hormone_columns=hormone_columns)

    if signal_mode == "rate_change":
        hormone_signal_columns = [
            f"{h}_rate_change_per_day" for h in hormone_columns if f"{h}_rate_change_per_day" in daily.columns
        ]
        hormone_label = (
            hormone_columns[0].upper()
            if len(hormone_columns) == 1
            else "+".join([h.upper() for h in hormone_columns])
        )
        title_signal = f"{hormone_label} Rate of Change"
        right_axis_label = f"{hormone_label} rate-of-change (normalized, unitless 0-1)"
        raw_label_template = "{signal} (normalized)"
        smooth_label_template = "{signal} ({window}-day smoothed)"
    elif signal_mode == "level":
        hormone_signal_columns = [h for h in hormone_columns if h in daily.columns]
        hormone_label = (
            hormone_columns[0].upper()
            if len(hormone_columns) == 1
            else "+".join([h.upper() for h in hormone_columns])
        )
        title_signal = f"{hormone_label} Level"
        right_axis_label = f"{hormone_label} level (normalized, unitless 0-1)"
        raw_label_template = "{signal} (normalized)"
        smooth_label_template = "{signal} ({window}-day smoothed)"
    else:
        raise ValueError("signal_mode must be 'rate_change' or 'level'")

    if not hormone_signal_columns or feature_column not in daily.columns:
        raise ValueError("Missing feature or hormone rate columns for presentation chart.")

    feature_series = pd.to_numeric(daily[feature_column], errors="coerce")
    hormone_present = daily[hormone_signal_columns].notna().any(axis=1)
    feature_present = feature_series.notna()
    date_candidates = pd.concat([daily.loc[hormone_present, "date"], daily.loc[feature_present, "date"]], ignore_index=True)
    if date_candidates.dropna().empty:
        raise ValueError("No data available for requested date range.")

    plot_start = date_candidates.min().normalize()
    plot_end = date_candidates.max().normalize()
    if "cycle_day" in calendar.columns:
        nearby_period_days = calendar[
            (calendar["cycle_day"].between(1, 5, inclusive="both"))
            & (calendar["date"] >= (plot_start - pd.Timedelta(days=14)))
            & (calendar["date"] <= plot_end)
        ]["date"]
        if not nearby_period_days.empty:
            plot_start = min(plot_start, nearby_period_days.min().normalize())
    full_dates = pd.DataFrame({"date": pd.date_range(plot_start, plot_end, freq="D")})
    chart = full_dates.merge(daily, on="date", how="left")

    chart[feature_column] = pd.to_numeric(chart[feature_column], errors="coerce")
    chart[f"{feature_column}_interp"] = chart[feature_column].interpolate(method="linear", limit_direction="forward")
    feature_smooth_source = chart[feature_column] if gap_aware else chart[f"{feature_column}_interp"]
    chart[f"{feature_column}_smooth"] = _rolling_mean(feature_smooth_source, smoothing_window_days)

    for hormone_signal in hormone_signal_columns:
        chart[hormone_signal] = pd.to_numeric(chart[hormone_signal], errors="coerce")
        chart[f"{hormone_signal}_interp"] = chart[hormone_signal].interpolate(
            method="linear", limit_direction="forward"
        )
        hormone_smooth_source = chart[hormone_signal] if gap_aware else chart[f"{hormone_signal}_interp"]
        chart[f"{hormone_signal}_smooth"] = _rolling_mean(hormone_smooth_source, smoothing_window_days)
        hormone_norm_raw_source = chart[hormone_signal] if gap_aware else chart[f"{hormone_signal}_interp"]
        chart[f"{hormone_signal}_norm_raw"] = _min_max_normalize(hormone_norm_raw_source)
        chart[f"{hormone_signal}_norm_smooth"] = _min_max_normalize(chart[f"{hormone_signal}_smooth"])

    fig, ax = plt.subplots(figsize=(16, 8))
    hormone_ax = ax.twinx()

    ax.scatter(
        daily["date"],
        feature_series,
        color="#b9bec8",
        s=28,
        alpha=0.5,
        label="Observed daily feature",
        zorder=2,
    )
    ax.plot(
        chart["date"],
        chart[f"{feature_column}_smooth"],
        color="#155eef",
        linewidth=3.0,
        label=(
            f"Feature ({smoothing_window_days}-day smoothed, gap-aware)"
            if gap_aware
            else f"Feature ({smoothing_window_days}-day smoothed, continuous)"
        ),
        zorder=5,
    )

    feature_axis_values = pd.concat(
        [
            chart[feature_column],
            chart[f"{feature_column}_smooth"],
        ],
        ignore_index=True,
    ).dropna()
    if not feature_axis_values.empty:
        y_min = float(feature_axis_values.min())
        y_max = float(feature_axis_values.max())
        y_span = y_max - y_min
        # Keep academic-style readability without clipping: use full feature range with modest padding.
        y_pad = max(0.005, y_span * 0.12)
        ax.set_ylim(y_min - y_pad, y_max + y_pad)

    palette = {
        "e3g_rate_change_per_day": ("#f79009", "#fddcab"),
        "pdg_rate_change_per_day": ("#12b76a", "#b7f3cf"),
        "e3g": ("#f79009", "#fddcab"),
        "pdg": ("#12b76a", "#b7f3cf"),
    }
    for hormone_signal in hormone_signal_columns:
        strong, faint = palette.get(hormone_signal, ("#087443", "#b4ead1"))
        hormone_ax.plot(
            chart["date"],
            chart[f"{hormone_signal}_norm_raw"],
            color=faint,
            linewidth=1.0,
            alpha=0.5,
            label=raw_label_template.format(signal=hormone_signal),
            zorder=1,
        )
        hormone_ax.plot(
            chart["date"],
            chart[f"{hormone_signal}_norm_smooth"],
            color=strong,
            linewidth=2.2,
            label=smooth_label_template.format(signal=hormone_signal, window=smoothing_window_days),
            zorder=3,
        )

    period_starts = (
        calendar[
            (calendar.get("cycle_day", pd.Series(dtype="float64")) == 1)
            & (calendar["date"] >= (plot_start - pd.Timedelta(days=1)))
            & (calendar["date"] <= (plot_end + pd.Timedelta(days=1)))
        ]["date"]
        if "cycle_day" in calendar.columns
        else pd.Series(dtype="datetime64[ns]")
    )
    for period_start in period_starts:
        ax.axvline(period_start, color="#ef4444", linewidth=1.5, alpha=0.85, zorder=4)

    if "cycle_day" in calendar.columns:
        period_days = calendar[
            (calendar["cycle_day"].between(1, 5, inclusive="both"))
            & (calendar["date"] >= (plot_start - pd.Timedelta(days=1)))
            & (calendar["date"] <= (plot_end + pd.Timedelta(days=1)))
        ]["date"]
        for day in period_days:
            ax.axvspan(
                day - pd.Timedelta(hours=12),
                day + pd.Timedelta(hours=12),
                ymin=0.0,
                ymax=0.045,
                color="#e11d48",
                alpha=0.22,
                linewidth=0.0,
                zorder=3,
            )

    ax.set_xlim(plot_start - pd.Timedelta(days=1), plot_end + pd.Timedelta(days=1))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax.grid(alpha=0.2)

    feature_name = feature_column.replace("prosody_egemaps_", "").replace("_", " ")
    ax.set_title(
        f"Prosody Task: Voice Feature vs {title_signal}\n"
        f"{feature_name} | {smoothing_window_days}-Day Smoothing | Jan-Mar 2026",
        fontsize=17,
        pad=18,
    )
    fig.text(
        0.01,
        0.01,
        "Source task: Prosody voice recordings (daily aggregated feature values). "
        + (
            "Line breaks indicate dates with missing voice-feature observations."
            if gap_aware
            else "Continuous line uses linear interpolation for visual continuity only."
        ),
        ha="left",
        va="bottom",
        fontsize=10,
        color="#4b5563",
    )

    ax.set_xlabel("Date (2026)", fontsize=12)
    ax.set_ylabel("Voice feature value (a.u.)", fontsize=12)
    hormone_ax.set_ylabel(right_axis_label, fontsize=12)
    hormone_ax.set_ylim(-0.05, 1.05)

    left_handles, left_labels = ax.get_legend_handles_labels()
    right_handles, right_labels = hormone_ax.get_legend_handles_labels()
    period_start_handle = plt.Line2D([0], [0], color="#ef4444", linewidth=1.5, label="Period start")
    period_day_handle = plt.Line2D([0], [0], color="#e11d48", linewidth=6, alpha=0.25, label="Period day (1-5)")
    handles = left_handles + [period_start_handle, period_day_handle] + right_handles
    labels = left_labels + ["Period start", "Period day (1-5)"] + right_labels
    ax.legend(handles, labels, loc="upper right", fontsize=10, framealpha=0.95)

    artifacts.output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(artifacts.output_path, dpi=220)
    plt.close(fig)
    return artifacts.output_path
