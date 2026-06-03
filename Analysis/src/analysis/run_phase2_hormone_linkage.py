"""CLI entrypoint for Phase 2 hormone linkage scan."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .config import default_paths
from .phase2_hormone_linkage import Phase2Artifacts, run_phase2_hormone_linkage


DEFAULT_CANDIDATE_FEATURES = [
    "prosody_egemaps_mfcc2_sma3_stddevNorm",
    "prosody_egemaps_logRelF0-H1-H2_sma3nz_amean",
    "prosody_egemaps_mfcc3_sma3_amean",
    "prosody_egemaps_F1bandwidth_sma3nz_stddevNorm",
    "prosody_egemaps_alphaRatioUV_sma3nz_amean",
]


def main() -> None:
    defaults = default_paths()
    parser = argparse.ArgumentParser(description="Run Phase 2 lagged hormone-feature linkage scan.")
    parser.add_argument(
        "--merged-input-path",
        type=Path,
        default=defaults.processed_dir / "analysis_first_pass_merged.parquet",
    )
    parser.add_argument(
        "--lag-scan-output-path",
        type=Path,
        default=defaults.outputs_dir / "phase2_hormone_lag_scan.csv",
    )
    parser.add_argument(
        "--summary-report-path",
        type=Path,
        default=defaults.outputs_dir / "phase2_hormone_linkage_report.md",
    )
    parser.add_argument(
        "--hormone-daily-levels-output-path",
        type=Path,
        default=defaults.processed_dir / "hormone_daily_levels.parquet",
    )
    parser.add_argument(
        "--hormone-daily-with-rate-output-path",
        type=Path,
        default=defaults.processed_dir / "hormone_daily_with_rate.parquet",
    )
    parser.add_argument(
        "--candidate-feature",
        action="append",
        dest="candidate_features",
        default=[],
        help="Candidate voice feature column (repeatable). Defaults to curated top features.",
    )
    parser.add_argument(
        "--hormone-column",
        action="append",
        dest="hormone_columns",
        default=[],
        help="Hormone column to scan (repeatable). Defaults to e3g and pdg.",
    )
    parser.add_argument(
        "--rolling-window",
        type=int,
        action="append",
        dest="rolling_windows",
        default=[],
        help="Rolling window in days (repeatable). Defaults to 3 and 5.",
    )
    parser.add_argument(
        "--lag-day",
        type=int,
        action="append",
        dest="lag_days",
        default=[],
        help="Lag in days where hormone leads feature (repeatable). Defaults to 0,1,2,3.",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default="2026-01-16",
        help="Include data on/after this date.",
    )
    args = parser.parse_args()

    candidate_features = args.candidate_features or DEFAULT_CANDIDATE_FEATURES
    hormone_columns = args.hormone_columns or ["e3g", "pdg"]
    rolling_windows = args.rolling_windows or [3, 5]
    lag_days = args.lag_days or [0, 1, 2, 3]
    start_date = pd.Timestamp(args.start_date)

    run_phase2_hormone_linkage(
        merged_input_path=args.merged_input_path,
        artifacts=Phase2Artifacts(
            lag_scan_output_path=args.lag_scan_output_path,
            summary_report_path=args.summary_report_path,
            hormone_daily_levels_output_path=args.hormone_daily_levels_output_path,
            hormone_daily_with_rate_output_path=args.hormone_daily_with_rate_output_path,
        ),
        candidate_features=candidate_features,
        hormone_columns=hormone_columns,
        rolling_windows=rolling_windows,
        lag_days=lag_days,
        start_date=start_date,
    )

    print(f"Wrote: {args.lag_scan_output_path}")
    print(f"Wrote: {args.summary_report_path}")
    print(f"Wrote: {args.hormone_daily_levels_output_path}")
    print(f"Wrote: {args.hormone_daily_with_rate_output_path}")


if __name__ == "__main__":
    main()
