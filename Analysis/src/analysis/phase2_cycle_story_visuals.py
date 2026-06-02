"""Build a presentation-ready cycle story with signal and null-feature contrasts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib import patches
import pandas as pd


HORMONE_COLUMNS = ["e3g", "pdg"]

CYCLING_SIGNAL_FEATURES = [
    "prosody_egemaps_logRelF0-H1-H2_sma3nz_amean",
    "prosody_egemaps_mfcc2_sma3_stddevNorm",
    "prosody_egemaps_mfcc3_sma3_amean",
    "prosody_egemaps_F1bandwidth_sma3nz_stddevNorm",
]

GEOMETRY_ANCHOR_FEATURES = [
    "prosody_egemaps_F1frequency_sma3nz_amean",
    "prosody_egemaps_F2frequency_sma3nz_amean",
    "prosody_egemaps_F3frequency_sma3nz_amean",
]

MECHANICS_ANCHOR_FEATURES = [
    "prosody_egemaps_F0semitoneFrom27.5Hz_sma3nz_amean",
    "prosody_egemaps_jitterLocal_sma3nz_amean",
    "prosody_egemaps_shimmerLocaldB_sma3nz_amean",
    "prosody_egemaps_loudness_sma3_amean",
]

PAIR_FORMANT_CONTRAST = [
    "prosody_egemaps_F1frequency_sma3nz_amean",
    "prosody_egemaps_F1bandwidth_sma3nz_stddevNorm",
]

PAIR_SOURCE_CONTRAST = [
    "prosody_egemaps_F0semitoneFrom27.5Hz_sma3nz_amean",
    "prosody_egemaps_logRelF0-H1-H2_sma3nz_amean",
]

FEATURE_LABELS = {
    "prosody_egemaps_logRelF0-H1-H2_sma3nz_amean": "H1-H2 (spectral balance)",
    "prosody_egemaps_mfcc2_sma3_stddevNorm": "MFCC2 variability",
    "prosody_egemaps_mfcc3_sma3_amean": "MFCC3 mean",
    "prosody_egemaps_F1bandwidth_sma3nz_stddevNorm": "F1 bandwidth variability",
    "prosody_egemaps_F1frequency_sma3nz_amean": "F1 center frequency",
    "prosody_egemaps_F2frequency_sma3nz_amean": "F2 center frequency",
    "prosody_egemaps_F3frequency_sma3nz_amean": "F3 center frequency",
    "prosody_egemaps_F0semitoneFrom27.5Hz_sma3nz_amean": "F0 mean (semitone)",
    "prosody_egemaps_jitterLocal_sma3nz_amean": "Jitter local",
    "prosody_egemaps_shimmerLocaldB_sma3nz_amean": "Shimmer local dB",
    "prosody_egemaps_loudness_sma3_amean": "Loudness mean",
}

FEATURE_SHORT_LABELS = {
    "prosody_egemaps_logRelF0-H1-H2_sma3nz_amean": "H1-H2",
    "prosody_egemaps_mfcc2_sma3_stddevNorm": "MFCC2 var",
    "prosody_egemaps_mfcc3_sma3_amean": "MFCC3 mean",
    "prosody_egemaps_F1bandwidth_sma3nz_stddevNorm": "F1 bw var",
    "prosody_egemaps_F1frequency_sma3nz_amean": "F1 freq",
    "prosody_egemaps_F2frequency_sma3nz_amean": "F2 freq",
    "prosody_egemaps_F3frequency_sma3nz_amean": "F3 freq",
    "prosody_egemaps_F0semitoneFrom27.5Hz_sma3nz_amean": "F0 mean",
    "prosody_egemaps_jitterLocal_sma3nz_amean": "Jitter",
    "prosody_egemaps_shimmerLocaldB_sma3nz_amean": "Shimmer",
    "prosody_egemaps_loudness_sma3_amean": "Loudness",
}


@dataclass(frozen=True)
class CycleStoryArtifacts:
    output_dir: Path


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


def _spearman_rho(left: pd.Series, right: pd.Series) -> tuple[float, int]:
    aligned = pd.DataFrame({"left": left, "right": right}).dropna()
    n_obs = len(aligned)
    if n_obs < 3:
        return float("nan"), n_obs
    rho = aligned["left"].corr(aligned["right"], method="spearman")
    return float(rho) if pd.notna(rho) else float("nan"), n_obs


def _robust_clip_for_plot(series: pd.Series) -> pd.Series:
    valid = series.dropna()
    if valid.empty:
        return series
    median = valid.median()
    mad = (valid - median).abs().median()
    if pd.isna(mad) or mad == 0:
        low = valid.quantile(0.01)
        high = valid.quantile(0.99)
    else:
        robust_sigma = 1.4826 * mad
        low = median - 6.0 * robust_sigma
        high = median + 6.0 * robust_sigma
    return series.clip(lower=low, upper=high)


def _feature_label(feature: str) -> str:
    return FEATURE_LABELS.get(feature, feature.replace("prosody_egemaps_", "").replace("_", " "))


def _feature_short_label(feature: str) -> str:
    return FEATURE_SHORT_LABELS.get(feature, _feature_label(feature))


def _build_daily_frame(
    merged: pd.DataFrame,
    *,
    feature_columns: list[str],
    hormone_columns: list[str],
    start_date: pd.Timestamp,
) -> pd.DataFrame:
    existing_features = [column for column in feature_columns if column in merged.columns]
    existing_hormones = [column for column in hormone_columns if column in merged.columns]
    keep_columns = ["date", *existing_features, *existing_hormones]
    daily = (
        merged[keep_columns]
        .copy()
        .assign(date=lambda frame: pd.to_datetime(frame["date"], errors="coerce"))
        .dropna(subset=["date"])
        .groupby("date", as_index=False)
        .mean(numeric_only=True)
        .sort_values("date")
    )
    daily = daily[daily["date"] >= start_date].copy()
    for column in [*existing_features, *existing_hormones]:
        daily[column] = pd.to_numeric(daily[column], errors="coerce")
    return daily


def _build_calendar(merged: pd.DataFrame, *, start_date: pd.Timestamp) -> pd.DataFrame:
    calendar_columns = [column for column in ["date", "cycle_day"] if column in merged.columns]
    if "date" not in calendar_columns:
        return pd.DataFrame(columns=["date", "cycle_day"])
    calendar = (
        merged[calendar_columns]
        .copy()
        .assign(date=lambda frame: pd.to_datetime(frame["date"], errors="coerce"))
        .dropna(subset=["date"])
        .sort_values("date")
        .drop_duplicates(subset=["date"], keep="last")
    )
    if "cycle_day" in calendar.columns:
        calendar["cycle_day"] = pd.to_numeric(calendar["cycle_day"], errors="coerce")
    return calendar[calendar["date"] >= start_date].copy()


def _plot_period_markers(
    ax: plt.Axes, calendar: pd.DataFrame, *, start: pd.Timestamp, end: pd.Timestamp
) -> tuple[bool, bool]:
    has_period_start = False
    has_period_days = False
    if calendar.empty or "cycle_day" not in calendar.columns:
        return has_period_start, has_period_days
    period_starts = calendar[
        (calendar["cycle_day"] == 1)
        & (calendar["date"] >= (start - pd.Timedelta(days=1)))
        & (calendar["date"] <= (end + pd.Timedelta(days=1)))
    ]["date"]
    for period_start in period_starts:
        ax.axvline(period_start, color="#ef4444", linewidth=1.4, alpha=0.85, zorder=5)
        has_period_start = True
    period_days = calendar[
        (calendar["cycle_day"].between(1, 5, inclusive="both"))
        & (calendar["date"] >= (start - pd.Timedelta(days=1)))
        & (calendar["date"] <= (end + pd.Timedelta(days=1)))
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
            zorder=4,
        )
        has_period_days = True
    return has_period_start, has_period_days


def _plot_feature_panel(
    *,
    daily: pd.DataFrame,
    calendar: pd.DataFrame,
    features: list[str],
    hormone_columns: list[str],
    smoothing_window_days: int,
    output_path: Path,
    title: str,
    subtitle: str,
    context_overlay_columns: list[str] | None = None,
) -> None:
    features_to_plot = [feature for feature in features if feature in daily.columns]
    hormones_to_plot = [hormone for hormone in hormone_columns if hormone in daily.columns]
    context_overlay_columns = context_overlay_columns or []
    context_to_plot = [column for column in context_overlay_columns if column in daily.columns]
    if not features_to_plot or not hormones_to_plot:
        return

    feature_present = daily[features_to_plot].notna().any(axis=1)
    hormone_present = daily[hormones_to_plot].notna().any(axis=1)
    context_present = daily[context_to_plot].notna().any(axis=1) if context_to_plot else pd.Series(False, index=daily.index)
    date_candidates = pd.concat(
        [
            daily.loc[feature_present, "date"],
            daily.loc[hormone_present, "date"],
            daily.loc[context_present, "date"],
        ],
        ignore_index=True,
    ).dropna()
    if date_candidates.empty:
        return

    plot_start = date_candidates.min().normalize()
    plot_end = date_candidates.max().normalize()
    full_dates = pd.DataFrame({"date": pd.date_range(plot_start, plot_end, freq="D")})
    chart = full_dates.merge(daily, on="date", how="left")

    for feature in features_to_plot:
        chart[feature] = pd.to_numeric(chart[feature], errors="coerce")
        chart[f"{feature}_clipped"] = _robust_clip_for_plot(chart[feature])
        chart[f"{feature}_interp"] = chart[f"{feature}_clipped"].interpolate(
            method="linear", limit_direction="forward"
        )
        chart[f"{feature}_smooth"] = _rolling_mean(chart[f"{feature}_interp"], smoothing_window_days)
    for hormone in hormones_to_plot:
        chart[hormone] = pd.to_numeric(chart[hormone], errors="coerce")
        chart[f"{hormone}_interp"] = chart[hormone].interpolate(method="linear", limit_direction="forward")
        chart[f"{hormone}_smooth"] = _rolling_mean(chart[f"{hormone}_interp"], smoothing_window_days)
        chart[f"{hormone}_norm_raw"] = _min_max_normalize(chart[f"{hormone}_interp"])
        chart[f"{hormone}_norm_smooth"] = _min_max_normalize(chart[f"{hormone}_smooth"])
    for context_column in context_to_plot:
        chart[context_column] = pd.to_numeric(chart[context_column], errors="coerce")
        chart[f"{context_column}_interp"] = chart[context_column].interpolate(
            method="linear", limit_direction="forward"
        )
        chart[f"{context_column}_smooth"] = _rolling_mean(chart[f"{context_column}_interp"], smoothing_window_days)
        chart[f"{context_column}_norm_raw"] = _min_max_normalize(chart[f"{context_column}_interp"])
        chart[f"{context_column}_norm_smooth"] = _min_max_normalize(chart[f"{context_column}_smooth"])

    fig, axes = plt.subplots(
        len(features_to_plot),
        1,
        figsize=(16, 3.9 * len(features_to_plot)),
        sharex=True,
    )
    if len(features_to_plot) == 1:
        axes = [axes]

    hormone_palette = {
        "e3g": ("#f79009", "#fddcab"),
        "pdg": ("#12b76a", "#b7f3cf"),
    }
    context_palette = {
        "time_in_bed_hours": ("#7f56d9", "#d9ccff"),
    }

    for index, feature in enumerate(features_to_plot):
        ax = axes[index]
        hormone_ax = ax.twinx()

        observed = _robust_clip_for_plot(pd.to_numeric(daily[feature], errors="coerce"))
        ax.scatter(
            daily["date"],
            observed,
            color="#c3c8d2",
            s=20,
            alpha=0.5,
            label="Observed daily feature",
            zorder=2,
        )
        ax.plot(
            chart["date"],
            chart[f"{feature}_smooth"],
            color="#155eef",
            linewidth=2.5,
            label=f"Feature ({smoothing_window_days}-day smoothed)",
            zorder=5,
        )

        axis_values = pd.concat(
            [chart[f"{feature}_clipped"], chart[f"{feature}_smooth"]], ignore_index=True
        ).dropna()
        if not axis_values.empty:
            y_min = float(axis_values.min())
            y_max = float(axis_values.max())
            y_span = y_max - y_min
            y_pad = max(0.005, y_span * 0.14)
            ax.set_ylim(y_min - y_pad, y_max + y_pad)

        for hormone in hormones_to_plot:
            strong, faint = hormone_palette.get(hormone, ("#087443", "#b4ead1"))
            hormone_ax.plot(
                chart["date"],
                chart[f"{hormone}_norm_raw"],
                color=faint,
                linewidth=1.0,
                alpha=0.45,
                label=f"{hormone.upper()} (normalized)",
                zorder=1,
            )
            hormone_ax.plot(
                chart["date"],
                chart[f"{hormone}_norm_smooth"],
                color=strong,
                linewidth=1.8,
                label=f"{hormone.upper()} ({smoothing_window_days}-day smoothed)",
                zorder=3,
            )
        for context_column in context_to_plot:
            strong, faint = context_palette.get(context_column, ("#6941c6", "#e9d7fe"))
            readable_label = "Hours in bed (Oura)" if context_column == "time_in_bed_hours" else context_column
            hormone_ax.plot(
                chart["date"],
                chart[f"{context_column}_norm_raw"],
                color=faint,
                linewidth=1.0,
                alpha=0.45,
                linestyle="-.",
                label=f"{readable_label} (normalized)",
                zorder=1,
            )
            hormone_ax.plot(
                chart["date"],
                chart[f"{context_column}_norm_smooth"],
                color=strong,
                linewidth=1.9,
                linestyle="-.",
                label=f"{readable_label} ({smoothing_window_days}-day smoothed)",
                zorder=3,
            )

        period_start_drawn, period_day_drawn = _plot_period_markers(
            ax,
            calendar,
            start=plot_start,
            end=plot_end,
        )

        ax.set_title(_feature_label(feature), fontsize=11, loc="left")
        ax.set_ylabel("Feature value")
        hormone_ax.set_ylabel("Hormone / sleep overlay (0-1)")
        hormone_ax.set_ylim(-0.05, 1.05)
        ax.grid(alpha=0.2)
        ax.set_xlim(plot_start - pd.Timedelta(days=1), plot_end + pd.Timedelta(days=1))
        ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))

        if index == 0:
            left_handles, left_labels = ax.get_legend_handles_labels()
            right_handles, right_labels = hormone_ax.get_legend_handles_labels()
            if period_start_drawn:
                left_handles.append(
                    plt.Line2D([0], [0], color="#ef4444", linewidth=1.4, label="Period start")
                )
                left_labels.append("Period start")
            if period_day_drawn:
                left_handles.append(
                    plt.Line2D([0], [0], color="#e11d48", linewidth=6, alpha=0.25, label="Period day (1-5)")
                )
                left_labels.append("Period day (1-5)")
            ax.legend(left_handles + right_handles, left_labels + right_labels, fontsize=8, loc="upper right")

    axes[-1].set_xlabel("Date (2026)")
    fig.suptitle(title, fontsize=15, y=0.99)
    fig.text(0.5, 0.965, subtitle, ha="center", va="top", fontsize=10, color="#4b5563")
    fig.text(
        0.01,
        0.01,
        "Hormones and sleep overlays are min-max normalized for shape comparison only. "
        "Feature lines use interpolation for continuity.",
        ha="left",
        va="bottom",
        fontsize=9.5,
        color="#4b5563",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    fig.savefig(output_path, dpi=220)
    plt.close(fig)


def _plot_feature_panel_weekly_mean(
    *,
    daily: pd.DataFrame,
    calendar: pd.DataFrame,
    features: list[str],
    hormone_columns: list[str],
    output_path: Path,
    title: str,
    subtitle: str,
    context_overlay_columns: list[str] | None = None,
    smoothing_window_weeks: int = 3,
) -> None:
    features_to_plot = [feature for feature in features if feature in daily.columns]
    hormones_to_plot = [hormone for hormone in hormone_columns if hormone in daily.columns]
    context_overlay_columns = context_overlay_columns or []
    context_to_plot = [column for column in context_overlay_columns if column in daily.columns]
    if not features_to_plot or not hormones_to_plot:
        return

    working = daily.copy()
    working["week_start"] = working["date"] - pd.to_timedelta(working["date"].dt.weekday, unit="D")
    keep_columns = ["week_start", *features_to_plot, *hormones_to_plot, *context_to_plot]
    weekly = (
        working[keep_columns]
        .groupby("week_start", as_index=False)
        .mean(numeric_only=True)
        .rename(columns={"week_start": "date"})
        .sort_values("date")
    )
    if weekly.empty:
        return

    for feature in features_to_plot:
        weekly[feature] = _robust_clip_for_plot(pd.to_numeric(weekly[feature], errors="coerce"))
    for hormone in hormones_to_plot:
        weekly[hormone] = pd.to_numeric(weekly[hormone], errors="coerce")
        weekly[f"{hormone}_norm"] = _min_max_normalize(weekly[hormone])
    for context_column in context_to_plot:
        weekly[context_column] = pd.to_numeric(weekly[context_column], errors="coerce")
        weekly[f"{context_column}_norm"] = _min_max_normalize(weekly[context_column])

    plot_start = weekly["date"].min().normalize()
    plot_end = weekly["date"].max().normalize()
    fig, axes = plt.subplots(
        len(features_to_plot),
        1,
        figsize=(16, 3.9 * len(features_to_plot)),
        sharex=True,
    )
    if len(features_to_plot) == 1:
        axes = [axes]

    hormone_palette = {
        "e3g": ("#f79009", "#fddcab"),
        "pdg": ("#12b76a", "#b7f3cf"),
    }
    context_palette = {
        "time_in_bed_hours": ("#7f56d9", "#d9ccff"),
    }

    for index, feature in enumerate(features_to_plot):
        ax = axes[index]
        hormone_ax = ax.twinx()

        feature_series = pd.to_numeric(weekly[feature], errors="coerce")
        feature_smooth = _rolling_mean(feature_series, smoothing_window_weeks)
        ax.scatter(
            weekly["date"],
            feature_series,
            color="#a4bcfd",
            s=46,
            alpha=0.95,
            label="Weekly mean (raw)",
            zorder=3,
        )
        ax.plot(
            weekly["date"],
            feature_smooth,
            color="#155eef",
            linewidth=2.3,
            label=f"Weekly mean trend ({smoothing_window_weeks}-week centered)",
            zorder=4,
        )

        for hormone in hormones_to_plot:
            strong, _ = hormone_palette.get(hormone, ("#087443", "#b4ead1"))
            hormone_smooth = _rolling_mean(pd.to_numeric(weekly[hormone], errors="coerce"), smoothing_window_weeks)
            hormone_norm_raw = weekly[f"{hormone}_norm"]
            hormone_norm_smooth = _min_max_normalize(hormone_smooth)
            hormone_ax.plot(
                weekly["date"],
                hormone_norm_raw,
                color=strong,
                linewidth=1.0,
                alpha=0.35,
                linestyle="--",
                label=f"{hormone.upper()} weekly mean (raw, normalized)",
                zorder=1,
            )
            hormone_ax.plot(
                weekly["date"],
                hormone_norm_smooth,
                color=strong,
                linewidth=1.9,
                label=f"{hormone.upper()} weekly mean ({smoothing_window_weeks}-week smoothed)",
                zorder=2,
            )
        for context_column in context_to_plot:
            strong, _ = context_palette.get(context_column, ("#6941c6", "#e9d7fe"))
            readable_label = "Hours in bed (Oura)" if context_column == "time_in_bed_hours" else context_column
            context_smooth = _rolling_mean(
                pd.to_numeric(weekly[context_column], errors="coerce"), smoothing_window_weeks
            )
            context_norm_raw = weekly[f"{context_column}_norm"]
            context_norm_smooth = _min_max_normalize(context_smooth)
            hormone_ax.plot(
                weekly["date"],
                context_norm_raw,
                color=strong,
                linewidth=1.0,
                alpha=0.35,
                linestyle="--",
                label=f"{readable_label} weekly mean (raw, normalized)",
                zorder=1,
            )
            hormone_ax.plot(
                weekly["date"],
                context_norm_smooth,
                color=strong,
                linewidth=2.1,
                linestyle="-.",
                label=f"{readable_label} weekly mean ({smoothing_window_weeks}-week smoothed)",
                zorder=2,
            )

        period_starts = calendar[
            (calendar.get("cycle_day", pd.Series(dtype="float64")) == 1)
            & (calendar["date"] >= (plot_start - pd.Timedelta(days=2)))
            & (calendar["date"] <= (plot_end + pd.Timedelta(days=2)))
        ]["date"]
        for period_start in period_starts:
            ax.axvline(period_start, color="#ef4444", linewidth=1.2, alpha=0.55, zorder=1)

        axis_values = pd.concat([feature_series, feature_smooth], ignore_index=True).dropna()
        if not axis_values.empty:
            y_min = float(axis_values.min())
            y_max = float(axis_values.max())
            y_span = y_max - y_min
            y_pad = max(0.005, y_span * 0.18)
            ax.set_ylim(y_min - y_pad, y_max + y_pad)

        ax.set_title(_feature_label(feature), fontsize=11, loc="left")
        ax.set_ylabel("Feature value")
        hormone_ax.set_ylabel("Hormone / sleep overlay (0-1)")
        hormone_ax.set_ylim(-0.05, 1.05)
        ax.grid(alpha=0.2)
        ax.set_xlim(plot_start - pd.Timedelta(days=2), plot_end + pd.Timedelta(days=2))
        ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))

        if index == 0:
            left_handles, left_labels = ax.get_legend_handles_labels()
            right_handles, right_labels = hormone_ax.get_legend_handles_labels()
            if not period_starts.empty:
                left_handles.append(
                    plt.Line2D([0], [0], color="#ef4444", linewidth=1.2, alpha=0.55, label="Period start")
                )
                left_labels.append("Period start")
            ax.legend(left_handles + right_handles, left_labels + right_labels, fontsize=8, loc="upper right")

    axes[-1].set_xlabel("Date (week start)")
    fig.suptitle(title, fontsize=15, y=0.99)
    fig.text(0.5, 0.965, subtitle, ha="center", va="top", fontsize=10, color="#4b5563")
    fig.text(
        0.01,
        0.01,
        f"Each point is a week-over-week mean (week starts Monday). Lines use {smoothing_window_weeks}-week centered smoothing. "
        "Hormones and sleep overlays are normalized 0-1.",
        ha="left",
        va="bottom",
        fontsize=9.5,
        color="#4b5563",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    fig.savefig(output_path, dpi=220)
    plt.close(fig)


def _compute_lag_scan(
    *,
    daily: pd.DataFrame,
    features: list[str],
    hormone_columns: list[str],
    rolling_windows: list[int],
    lag_days: list[int],
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for signal_mode in ["level", "rate_change"]:
        work = daily.copy()
        mode_hormones = hormone_columns
        if signal_mode == "rate_change":
            for hormone in hormone_columns:
                observed = work[hormone].notna()
                prev_value = work[hormone].where(observed).ffill().shift(1)
                prev_date = work["date"].where(observed).ffill().shift(1)
                days_delta = (work["date"] - prev_date).dt.days
                work[f"{hormone}_rate_change_per_day"] = (work[hormone] - prev_value) / days_delta
            mode_hormones = [f"{hormone}_rate_change_per_day" for hormone in hormone_columns]

        for window in rolling_windows:
            window_frame = work.copy()
            for feature in features:
                if feature in window_frame.columns:
                    window_frame[f"{feature}_roll_{window}"] = _rolling_mean(window_frame[feature], window)
            for hormone in mode_hormones:
                if hormone in window_frame.columns:
                    window_frame[f"{hormone}_roll_{window}"] = _rolling_mean(window_frame[hormone], window)

            for feature in features:
                feature_column = f"{feature}_roll_{window}"
                if feature_column not in window_frame.columns:
                    continue
                for hormone in mode_hormones:
                    hormone_column = f"{hormone}_roll_{window}"
                    if hormone_column not in window_frame.columns:
                        continue
                    for lag in lag_days:
                        rho, n_obs = _spearman_rho(
                            window_frame[feature_column], window_frame[hormone_column].shift(lag)
                        )
                        rows.append(
                            {
                                "feature": feature,
                                "signal_mode": signal_mode,
                                "hormone": hormone.replace("_rate_change_per_day", ""),
                                "rolling_window_days": window,
                                "lag_days_hormone_leads": lag,
                                "spearman_rho": rho,
                                "abs_spearman_rho": abs(rho) if pd.notna(rho) else float("nan"),
                                "n_obs": n_obs,
                            }
                        )
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(
        by=["feature", "signal_mode", "abs_spearman_rho"],
        ascending=[True, True, False],
    )


def _build_evidence_table(
    *,
    stability_scan: pd.DataFrame,
    lag_scan: pd.DataFrame,
    features: list[str],
) -> pd.DataFrame:
    evidence_rows: list[dict[str, object]] = []
    for feature in features:
        stability_row = stability_scan[stability_scan["feature"] == feature].head(1)
        feature_links = lag_scan[lag_scan["feature"] == feature]
        best_any = feature_links.sort_values("abs_spearman_rho", ascending=False).head(1)
        best_level = feature_links[feature_links["signal_mode"] == "level"].sort_values(
            "abs_spearman_rho", ascending=False
        ).head(1)
        best_rate = feature_links[feature_links["signal_mode"] == "rate_change"].sort_values(
            "abs_spearman_rho", ascending=False
        ).head(1)

        story_group = "mechanics_anchor"
        if feature in CYCLING_SIGNAL_FEATURES:
            story_group = "cycling_signal"
        elif feature in GEOMETRY_ANCHOR_FEATURES:
            story_group = "geometry_anchor"

        row = {
            "feature": feature,
            "feature_label": _feature_label(feature),
            "feature_short_label": _feature_short_label(feature),
            "story_group": story_group,
            "flatness_score": float(stability_row["flatness_score"].iloc[0]) if not stability_row.empty else float("nan"),
            "variation_score": float(stability_row["variation_score"].iloc[0]) if not stability_row.empty else float("nan"),
            "period_lag_days_cycle_relevant": int(stability_row["period_lag_days_cycle_relevant"].iloc[0])
            if not stability_row.empty and pd.notna(stability_row["period_lag_days_cycle_relevant"].iloc[0])
            else pd.NA,
            "period_strength_abs_acf_cycle_relevant": float(stability_row["period_strength_abs_acf_cycle_relevant"].iloc[0])
            if not stability_row.empty
            else float("nan"),
            "robust_cv": float(stability_row["robust_cv"].iloc[0]) if not stability_row.empty else float("nan"),
            "best_any_abs_rho": float(best_any["abs_spearman_rho"].iloc[0]) if not best_any.empty else float("nan"),
            "best_any_hormone": best_any["hormone"].iloc[0] if not best_any.empty else "",
            "best_any_signal_mode": best_any["signal_mode"].iloc[0] if not best_any.empty else "",
            "best_any_lag_days": int(best_any["lag_days_hormone_leads"].iloc[0]) if not best_any.empty else pd.NA,
            "best_level_abs_rho": float(best_level["abs_spearman_rho"].iloc[0]) if not best_level.empty else float("nan"),
            "best_level_hormone": best_level["hormone"].iloc[0] if not best_level.empty else "",
            "best_rate_abs_rho": float(best_rate["abs_spearman_rho"].iloc[0]) if not best_rate.empty else float("nan"),
        }
        evidence_rows.append(row)

    evidence = pd.DataFrame(evidence_rows)
    return evidence.sort_values(["story_group", "best_any_abs_rho"], ascending=[True, False]).reset_index(drop=True)


def _plot_cycle_lag_strength(evidence: pd.DataFrame, output_path: Path) -> None:
    if evidence.empty:
        return
    plot_df = evidence.copy().sort_values("period_strength_abs_acf_cycle_relevant", ascending=False)
    color_map = {
        "cycling_signal": "#155eef",
        "geometry_anchor": "#12b76a",
        "mechanics_anchor": "#7f56d9",
    }
    bar_colors = [color_map.get(group, "#98a2b3") for group in plot_df["story_group"]]

    fig, ax = plt.subplots(figsize=(14.5, 7))
    bars = ax.barh(
        plot_df["feature_short_label"],
        plot_df["period_strength_abs_acf_cycle_relevant"],
        color=bar_colors,
        alpha=0.9,
    )
    ax.invert_yaxis()
    ax.set_xlabel("Cycle-relevant periodicity strength (abs ACF, lag 7-20 days)")
    ax.set_ylabel("Feature")
    ax.set_title("Do features show cycle-like periodic lags?")
    ax.grid(axis="x", alpha=0.22)

    for bar, lag in zip(bars, plot_df["period_lag_days_cycle_relevant"]):
        if pd.notna(lag):
            ax.text(
                bar.get_width() + 0.01,
                bar.get_y() + bar.get_height() / 2,
                f"lag {int(lag)}d",
                va="center",
                fontsize=9,
                color="#344054",
            )

    legend_handles = [
        plt.Line2D([0], [0], color=color_map["cycling_signal"], linewidth=8, label="Cycling signal features"),
        plt.Line2D([0], [0], color=color_map["geometry_anchor"], linewidth=8, label="Geometry anchor features"),
        plt.Line2D([0], [0], color=color_map["mechanics_anchor"], linewidth=8, label="Mechanics anchor features"),
    ]
    ax.legend(handles=legend_handles, loc="lower right")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_path, dpi=220)
    plt.close(fig)


def _plot_null_vs_signal_map(evidence: pd.DataFrame, output_path: Path) -> None:
    if evidence.empty:
        return
    color_map = {
        "cycling_signal": "#155eef",
        "geometry_anchor": "#12b76a",
        "mechanics_anchor": "#7f56d9",
    }
    fig, ax = plt.subplots(figsize=(11.5, 7))
    for group, frame in evidence.groupby("story_group"):
        ax.scatter(
            frame["best_level_abs_rho"],
            frame["flatness_score"],
            s=95,
            alpha=0.9,
            color=color_map.get(group, "#98a2b3"),
            label=group.replace("_", " "),
        )
        for row in frame.itertuples(index=False):
            ax.annotate(
                row.feature_short_label,
                (row.best_level_abs_rho, row.flatness_score),
                textcoords="offset points",
                xytext=(5, 4),
                fontsize=8.5,
                color="#344054",
            )
    ax.axvline(0.30, color="#98a2b3", linestyle="--", linewidth=1.1, alpha=0.9)
    ax.axhline(0.60, color="#98a2b3", linestyle="--", linewidth=1.1, alpha=0.9)
    ax.set_xlabel("Best hormone linkage (max abs Spearman rho, level signal)")
    ax.set_ylabel("Flatness score (higher means more stable)")
    ax.set_title("Null-check map: stability against hormone coupling")
    ax.grid(alpha=0.22)
    ax.legend(loc="lower left")
    ax.set_xlim(left=0)
    ax.set_ylim(0, 1.02)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_path, dpi=220)
    plt.close(fig)


def _plot_mechanism_diagram(output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    def add_box(x: float, y: float, w: float, h: float, text: str, color: str) -> patches.FancyBboxPatch:
        patch = patches.FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.02,rounding_size=0.02",
            linewidth=1.2,
            edgecolor="#1d2939",
            facecolor=color,
        )
        ax.add_patch(patch)
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=11, color="#101828")
        return patch

    left_top = add_box(0.05, 0.73, 0.24, 0.16, "Hormone cycle shifts\n(E3G and PdG)", "#fff3db")
    center_top = add_box(
        0.38,
        0.73,
        0.24,
        0.16,
        "Surface-layer damping /\nhydration changes",
        "#d1fadf",
    )
    right_top = add_box(
        0.71,
        0.73,
        0.24,
        0.16,
        "Cycling acoustic features\nH1-H2, MFCC2, MFCC3,\nF1 bandwidth",
        "#dbe8ff",
    )

    left_bottom = add_box(
        0.05,
        0.31,
        0.24,
        0.16,
        "No major movement in\ntract geometry or deep\nvocal-fold mechanics",
        "#f2f4f7",
    )
    center_bottom = add_box(
        0.38,
        0.31,
        0.24,
        0.16,
        "Stable anchors\nF1/F2/F3 freq, F0 mean,\njitter, shimmer, loudness",
        "#f2f4f7",
    )
    right_bottom = add_box(
        0.71,
        0.31,
        0.24,
        0.16,
        "Null checks constrain\nbulk-mass or tension-only\nmechanisms",
        "#fef3f2",
    )

    final_box = add_box(
        0.31,
        0.05,
        0.38,
        0.16,
        "Current best hypothesis:\nhormone-linked surface modulation\nwith mixed null-anchor evidence",
        "#ecfdf3",
    )

    arrow_style = dict(arrowstyle="-|>", color="#344054", linewidth=1.4)
    ax.annotate("", xy=(0.38, 0.81), xytext=(0.29, 0.81), arrowprops=arrow_style)
    ax.annotate("", xy=(0.71, 0.81), xytext=(0.62, 0.81), arrowprops=arrow_style)
    ax.annotate("", xy=(0.38, 0.39), xytext=(0.29, 0.39), arrowprops=arrow_style)
    ax.annotate("", xy=(0.71, 0.39), xytext=(0.62, 0.39), arrowprops=arrow_style)
    ax.annotate("", xy=(0.50, 0.21), xytext=(0.83, 0.31), arrowprops=arrow_style)
    ax.annotate("", xy=(0.50, 0.21), xytext=(0.83, 0.73), arrowprops=arrow_style)
    ax.annotate("", xy=(0.50, 0.21), xytext=(0.50, 0.31), arrowprops=arrow_style)

    ax.set_title("Candidate mechanism from positive + null-check evidence", fontsize=15, pad=16)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_path, dpi=220)
    plt.close(fig)


def _build_story_markdown(
    *,
    evidence: pd.DataFrame,
    output_dir: Path,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
) -> str:
    cycling = evidence[evidence["story_group"] == "cycling_signal"].sort_values("best_level_abs_rho", ascending=False)
    geometry = evidence[evidence["story_group"] == "geometry_anchor"].sort_values("best_level_abs_rho")
    mechanics = evidence[evidence["story_group"] == "mechanics_anchor"].sort_values("best_level_abs_rho")

    def bullet_line(row: pd.Series) -> str:
        lag_value = row["period_lag_days_cycle_relevant"]
        lag_text = f"{int(lag_value)}d" if pd.notna(lag_value) else "NA"
        return (
            f"- **{row['feature_short_label']}**: flatness `{row['flatness_score']:.3f}`, "
            f"cycle lag `{lag_text}` (ACF `{row['period_strength_abs_acf_cycle_relevant']:.3f}`), "
            f"best level linkage `{row['best_level_abs_rho']:.3f}`"
        )

    cycling_lines = "\n".join([bullet_line(row) for _, row in cycling.iterrows()]) or "- No rows"
    geometry_lines = "\n".join([bullet_line(row) for _, row in geometry.iterrows()]) or "- No rows"
    mechanics_lines = "\n".join([bullet_line(row) for _, row in mechanics.iterrows()]) or "- No rows"

    return (
        "# Professor Presentation Story: Signal + Null Feature Contrast\n\n"
        f"Time window: `{start_date.date()}` to `{end_date.date()}`\n\n"
        "This package is designed as a direct slide narrative where null results are used as mechanism filters, "
        "not as missing findings.\n\n"
        "## Files in this folder (recommended slide order)\n\n"
        "1. `01_signal_exists_cycling_features.png`\n"
        "1b. `01b_signal_exists_cycling_features_weekly_mean.png`\n"
        "2. `02_geometry_is_stable_formant_frequencies.png`\n"
        "3. `03_gross_mechanics_are_stable.png`\n"
        "4. `04_pair_f1_frequency_vs_f1_bandwidth.png`\n"
        "5. `05_pair_f0_mean_vs_h1_h2.png`\n"
        "6. `06_cycle_lag_strength_comparison.png`\n"
        "7. `07_null_vs_signal_evidence_map.png`\n"
        "8. `08_mechanism_concept_diagram.png`\n"
        "9. `feature_evidence_table.csv`\n\n"
        "## Section 1 - The signal exists\n\n"
        "Use `01_signal_exists_cycling_features.png` to open with features already known to move with cycle-related hormone dynamics.\n"
        "Use `01b_signal_exists_cycling_features_weekly_mean.png` as the week-over-week simplification of the same panel.\n\n"
        f"{cycling_lines}\n\n"
        "## Section 2 - Geometry anchor check\n\n"
        "Use `02_geometry_is_stable_formant_frequencies.png`. The formant center frequencies are treated as tract geometry anchors.\n\n"
        f"{geometry_lines}\n\n"
        "Interpretation line: these features are comparatively range-stable by flatness and robust CV, "
        "but linkage strength is not zero; treat this as a partial null check rather than a hard null.\n\n"
        "## Section 3 - Gross mechanics anchor check\n\n"
        "Use `03_gross_mechanics_are_stable.png` for F0 mean, jitter, shimmer, and loudness.\n\n"
        f"{mechanics_lines}\n\n"
        "Interpretation line: F0 and jitter look closer to null anchors, while shimmer and loudness show more coupling than expected. "
        "This narrows the mechanism argument but does not fully close alternatives.\n\n"
        "## Section 4 - Pairwise contrasts isolate where change happens\n\n"
        "- `04_pair_f1_frequency_vs_f1_bandwidth.png`: same formant family, center frequency mostly stable while bandwidth dynamics carry the cycle-linked pattern.\n"
        "- `05_pair_f0_mean_vs_h1_h2.png`: fundamental rate mostly stable while source spectral balance carries stronger cycle-linked movement.\n\n"
        "## Section 5 - Mechanism synthesis\n\n"
        "- `06_cycle_lag_strength_comparison.png` shows cycle-lag periodicity values and lags for each selected feature.\n"
        "- `07_null_vs_signal_evidence_map.png` places each feature on stability vs hormone-linkage axes as a direct null-check diagnostic.\n"
        "- `08_mechanism_concept_diagram.png` is the conceptual close: surface-layer modulation remains plausible, "
        "with explicit acknowledgement that null-anchor evidence is mixed.\n\n"
        "## Suggested spoken talk track (short)\n\n"
        "1. We first confirm that selected acoustic features do track cycle-associated hormone dynamics.\n"
        "2. We then run null checks on geometry and gross mechanics anchors instead of assuming they are flat.\n"
        "3. Some anchors are comparatively stable, but a few still show moderate linkage, so the null evidence is mixed.\n"
        "4. The clearest selective movement remains in spectral texture and damping-linked features.\n"
        "5. Therefore surface-layer modulation is a plausible leading hypothesis, still exploratory and hypothesis-generating.\n\n"
        "## Caution for claims\n\n"
        "- Keep all wording exploratory, not causal.\n"
        "- Treat exact lag values as dataset-specific.\n"
        "- Emphasize that null results are evidence constraints, not absence of analysis.\n"
    )


def run_phase2_cycle_story_visuals(
    *,
    merged_input_path: Path,
    stability_scan_path: Path,
    artifacts: CycleStoryArtifacts,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp | None,
    smoothing_window_days: int,
) -> list[Path]:
    merged = pd.read_parquet(merged_input_path)
    merged["date"] = pd.to_datetime(merged["date"], errors="coerce")
    merged = merged.dropna(subset=["date"]).copy()
    merged = merged[merged["date"] >= start_date].copy()
    if end_date is not None:
        merged = merged[merged["date"] <= end_date].copy()

    selected_features = [
        *CYCLING_SIGNAL_FEATURES,
        *GEOMETRY_ANCHOR_FEATURES,
        *MECHANICS_ANCHOR_FEATURES,
    ]
    selected_features = list(dict.fromkeys(selected_features))
    existing_features = [feature for feature in selected_features if feature in merged.columns]

    daily = _build_daily_frame(
        merged=merged,
        feature_columns=existing_features,
        hormone_columns=HORMONE_COLUMNS,
        start_date=start_date,
    )
    if "timeInBed" in merged.columns:
        oura_bed = (
            merged[["date", "timeInBed"]]
            .copy()
            .dropna(subset=["date"])
            .groupby("date", as_index=False)
            .mean(numeric_only=True)
            .sort_values("date")
        )
        oura_bed["time_in_bed_hours"] = pd.to_numeric(oura_bed["timeInBed"], errors="coerce") / 3600.0
        daily = daily.merge(oura_bed[["date", "time_in_bed_hours"]], on="date", how="left")

    calendar = _build_calendar(merged=merged, start_date=start_date)
    lag_scan = _compute_lag_scan(
        daily=daily,
        features=existing_features,
        hormone_columns=[hormone for hormone in HORMONE_COLUMNS if hormone in daily.columns],
        rolling_windows=[3, 5],
        lag_days=[0, 1, 2, 3],
    )

    stability_scan = pd.read_csv(stability_scan_path)
    evidence = _build_evidence_table(stability_scan=stability_scan, lag_scan=lag_scan, features=existing_features)

    output_dir = artifacts.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    written_paths: list[Path] = []
    panel_specs = [
        (
            CYCLING_SIGNAL_FEATURES,
            output_dir / "01_signal_exists_cycling_features.png",
            "Section 1: Cycling signal features",
            "Signal panel with hormone overlays and period markers",
            ["time_in_bed_hours"],
        ),
        (
            GEOMETRY_ANCHOR_FEATURES,
            output_dir / "02_geometry_is_stable_formant_frequencies.png",
            "Section 2: Geometry anchors (formant center frequencies)",
            "If these remain steady while hormones shift, major tract-shape movement is less likely",
            [],
        ),
        (
            MECHANICS_ANCHOR_FEATURES,
            output_dir / "03_gross_mechanics_are_stable.png",
            "Section 3: Gross mechanics anchors",
            "F0 mean, jitter, shimmer, and loudness as broad-mechanics checks",
            [],
        ),
        (
            PAIR_FORMANT_CONTRAST,
            output_dir / "04_pair_f1_frequency_vs_f1_bandwidth.png",
            "Section 4A: Paired contrast - same formant family",
            "F1 center frequency vs F1 bandwidth variability",
            [],
        ),
        (
            PAIR_SOURCE_CONTRAST,
            output_dir / "05_pair_f0_mean_vs_h1_h2.png",
            "Section 4B: Paired contrast - source rate vs source shape",
            "F0 mean vs H1-H2",
            [],
        ),
    ]

    for features, output_path, title, subtitle, context_columns in panel_specs:
        _plot_feature_panel(
            daily=daily,
            calendar=calendar,
            features=features,
            hormone_columns=HORMONE_COLUMNS,
            smoothing_window_days=smoothing_window_days,
            output_path=output_path,
            title=title,
            subtitle=subtitle,
            context_overlay_columns=context_columns,
        )
        if output_path.exists():
            written_paths.append(output_path)

    weekly_section1_path = output_dir / "01b_signal_exists_cycling_features_weekly_mean.png"
    _plot_feature_panel_weekly_mean(
        daily=daily,
        calendar=calendar,
        features=CYCLING_SIGNAL_FEATURES,
        hormone_columns=HORMONE_COLUMNS,
        output_path=weekly_section1_path,
        title="Section 1: Cycling signal features (weekly mean)",
        subtitle="Week-over-week feature means with 3-week smoothing and the same hormone/sleep overlays",
        context_overlay_columns=["time_in_bed_hours"],
        smoothing_window_weeks=3,
    )
    if weekly_section1_path.exists():
        written_paths.append(weekly_section1_path)

    cycle_lag_path = output_dir / "06_cycle_lag_strength_comparison.png"
    _plot_cycle_lag_strength(evidence, cycle_lag_path)
    if cycle_lag_path.exists():
        written_paths.append(cycle_lag_path)

    map_path = output_dir / "07_null_vs_signal_evidence_map.png"
    _plot_null_vs_signal_map(evidence, map_path)
    if map_path.exists():
        written_paths.append(map_path)

    mechanism_path = output_dir / "08_mechanism_concept_diagram.png"
    _plot_mechanism_diagram(mechanism_path)
    if mechanism_path.exists():
        written_paths.append(mechanism_path)

    evidence_path = output_dir / "feature_evidence_table.csv"
    evidence.to_csv(evidence_path, index=False)
    written_paths.append(evidence_path)

    story_path = output_dir / "story_summary.md"
    narrative_end_date = daily["date"].max() if not daily.empty else start_date
    if end_date is not None and pd.notna(narrative_end_date):
        narrative_end_date = min(narrative_end_date, end_date)
    story_path.write_text(
        _build_story_markdown(
            evidence=evidence,
            output_dir=output_dir,
            start_date=start_date,
            end_date=narrative_end_date,
        ),
        encoding="utf-8",
    )
    written_paths.append(story_path)
    return written_paths
