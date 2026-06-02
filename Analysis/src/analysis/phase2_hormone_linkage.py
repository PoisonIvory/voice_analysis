"""Phase 2 workflow: quantify lagged hormone-feature linkage for candidate voice features."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd


@dataclass(frozen=True)
class Phase2Artifacts:
    lag_scan_output_path: Path
    summary_report_path: Path


def _rolling_mean(series: pd.Series, window_days: int) -> pd.Series:
    min_periods = max(2, window_days // 2)
    return series.rolling(window=window_days, min_periods=min_periods, center=True).mean()


def _to_numeric(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    out = df.copy()
    for column in columns:
        if column in out.columns:
            out[column] = pd.to_numeric(out[column], errors="coerce")
    return out


def _spearman_rho(left: pd.Series, right: pd.Series) -> tuple[float, int]:
    aligned = pd.DataFrame({"left": left, "right": right}).dropna()
    n = len(aligned)
    if n < 3:
        return float("nan"), n
    rho = aligned["left"].corr(aligned["right"], method="spearman")
    return float(rho) if pd.notna(rho) else float("nan"), n


def build_lag_scan(
    merged: pd.DataFrame,
    candidate_features: list[str],
    *,
    hormone_columns: list[str],
    rolling_windows: list[int],
    lag_days: list[int],
    start_date: pd.Timestamp,
) -> pd.DataFrame:
    required_columns = ["date", *hormone_columns, *candidate_features]
    existing_columns = [column for column in required_columns if column in merged.columns]

    daily = (
        merged[existing_columns]
        .copy()
        .assign(date=lambda frame: pd.to_datetime(frame["date"], errors="coerce"))
        .dropna(subset=["date"])
        .groupby("date", as_index=False)
        .mean(numeric_only=True)
        .sort_values("date")
    )
    daily = daily[daily["date"] >= start_date].copy()
    daily = _to_numeric(daily, [*hormone_columns, *candidate_features])

    rows: list[dict[str, object]] = []
    for window in rolling_windows:
        work = daily.copy()
        for column in [*hormone_columns, *candidate_features]:
            if column in work.columns:
                work[f"{column}_roll_{window}"] = _rolling_mean(work[column], window_days=window)

        for feature in candidate_features:
            feature_column = f"{feature}_roll_{window}"
            if feature_column not in work.columns:
                continue

            for hormone in hormone_columns:
                hormone_column = f"{hormone}_roll_{window}"
                if hormone_column not in work.columns:
                    continue

                for lag in lag_days:
                    # Positive lag means hormone leads feature by N days.
                    rho, n_obs = _spearman_rho(
                        work[feature_column],
                        work[hormone_column].shift(lag),
                    )
                    rows.append(
                        {
                            "feature": feature,
                            "hormone": hormone,
                            "rolling_window_days": window,
                            "lag_days_hormone_leads": lag,
                            "spearman_rho": rho,
                            "abs_spearman_rho": abs(rho) if pd.notna(rho) else float("nan"),
                            "n_obs": n_obs,
                        }
                    )

    results = pd.DataFrame(rows)
    if results.empty:
        return results
    return results.sort_values(
        by=["abs_spearman_rho", "n_obs", "rolling_window_days", "lag_days_hormone_leads"],
        ascending=[False, False, True, True],
    ).reset_index(drop=True)


def _render_phase2_summary_report(
    lag_scan: pd.DataFrame,
    *,
    candidate_features: list[str],
    hormone_columns: list[str],
    rolling_windows: list[int],
    lag_days: list[int],
    start_date: pd.Timestamp,
) -> str:
    if lag_scan.empty:
        return (
            "# Phase 2 Hormone Linkage Report\n\n"
            "No lag-scan rows were generated. Check candidate feature names and merged dataset coverage.\n"
        )

    best = (
        lag_scan.sort_values(["feature", "hormone", "abs_spearman_rho"], ascending=[True, True, False])
        .groupby(["feature", "hormone"], as_index=False)
        .head(1)
        .sort_values("abs_spearman_rho", ascending=False)
        .reset_index(drop=True)
    )

    best_lines = []
    for row in best.itertuples(index=False):
        best_lines.append(
            "- "
            f"`{row.feature}` x `{row.hormone}`: "
            f"rho `{row.spearman_rho:.3f}` at lag `{row.lag_days_hormone_leads}` "
            f"(window `{row.rolling_window_days}` days, n `{row.n_obs}`)"
        )

    strong = best[best["abs_spearman_rho"] >= 0.45]
    strong_lines = [
        "- "
        f"`{row.feature}` x `{row.hormone}`: rho `{row.spearman_rho:.3f}` "
        f"(lag `{row.lag_days_hormone_leads}`, window `{row.rolling_window_days}`, n `{row.n_obs}`)"
        for row in strong.itertuples(index=False)
    ]

    return (
        "# Phase 2 Hormone Linkage Report\n\n"
        "## Scope\n\n"
        f"- Start date: `{start_date.date()}`\n"
        f"- Candidate features: `{len(candidate_features)}`\n"
        f"- Hormones: `{', '.join(hormone_columns)}`\n"
        f"- Rolling windows: `{rolling_windows}`\n"
        f"- Lag scan (hormone leads): `{lag_days}` days\n\n"
        "## Best Linkage Per Feature-Hormone Pair\n\n"
        + "\n".join(best_lines)
        + "\n\n## Strong Candidate Links (|rho| >= 0.45)\n\n"
        + ("\n".join(strong_lines) if strong_lines else "- None at current thresholds")
        + "\n\n## Interpretation Notes\n\n"
        "- This scan quantifies pattern strength and lag direction from the overlay plots.\n"
        "- This is still exploratory linkage, not causal inference.\n"
        "- Use as inputs for confirmatory repeated-measures modeling in the next pass.\n"
    )


def run_phase2_hormone_linkage(
    *,
    merged_input_path: Path,
    artifacts: Phase2Artifacts,
    candidate_features: list[str],
    hormone_columns: list[str],
    rolling_windows: list[int],
    lag_days: list[int],
    start_date: pd.Timestamp,
) -> None:
    merged = pd.read_parquet(merged_input_path)
    lag_scan = build_lag_scan(
        merged=merged,
        candidate_features=candidate_features,
        hormone_columns=hormone_columns,
        rolling_windows=rolling_windows,
        lag_days=lag_days,
        start_date=start_date,
    )

    artifacts.lag_scan_output_path.parent.mkdir(parents=True, exist_ok=True)
    artifacts.summary_report_path.parent.mkdir(parents=True, exist_ok=True)

    lag_scan.to_csv(artifacts.lag_scan_output_path, index=False)
    artifacts.summary_report_path.write_text(
        _render_phase2_summary_report(
            lag_scan=lag_scan,
            candidate_features=candidate_features,
            hormone_columns=hormone_columns,
            rolling_windows=rolling_windows,
            lag_days=lag_days,
            start_date=start_date,
        ),
        encoding="utf-8",
    )
