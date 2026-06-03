"""CLI entrypoint for Phase 2 hormone rate-of-change overlay plots."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .config import default_paths
from .phase2_hormone_rate_plots import Phase2RatePlotArtifacts, run_phase2_hormone_rate_plots


DEFAULT_CANDIDATE_FEATURES = [
    "prosody_egemaps_mfcc2_sma3_stddevNorm",
    "prosody_egemaps_logRelF0-H1-H2_sma3nz_amean",
    "prosody_egemaps_mfcc3_sma3_amean",
    "prosody_egemaps_F1bandwidth_sma3nz_stddevNorm",
    "prosody_egemaps_alphaRatioUV_sma3nz_amean",
]


def main() -> None:
    defaults = default_paths()
    parser = argparse.ArgumentParser(description="Generate hormone rate-of-change vs prosody overlay figures.")
    parser.add_argument(
        "--merged-input-path",
        type=Path,
        default=defaults.processed_dir / "analysis_first_pass_merged.parquet",
    )
    parser.add_argument(
        "--figures-output-dir",
        type=Path,
        default=defaults.figures_dir,
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
        help="Hormone column for rate-of-change overlays (repeatable). Defaults to e3g and pdg.",
    )
    parser.add_argument(
        "--rolling-window",
        type=int,
        action="append",
        dest="rolling_windows",
        default=[],
        help="Smoothing window in days (repeatable). Defaults to 3, 5, and 7.",
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
    rolling_windows = args.rolling_windows or [3, 5, 7]
    start_date = pd.Timestamp(args.start_date)

    output_paths = run_phase2_hormone_rate_plots(
        merged_input_path=args.merged_input_path,
        artifacts=Phase2RatePlotArtifacts(figures_output_dir=args.figures_output_dir),
        candidate_features=candidate_features,
        hormone_columns=hormone_columns,
        rolling_windows=rolling_windows,
        start_date=start_date,
    )

    for output_path in output_paths:
        print(f"Wrote: {output_path}")


if __name__ == "__main__":
    main()
