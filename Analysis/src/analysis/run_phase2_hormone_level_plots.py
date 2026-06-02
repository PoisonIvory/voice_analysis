"""CLI entrypoint for Phase 2 hormone level overlay plots."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .config import default_paths
from .phase2_hormone_level_plots import (
    LevelPlotSpec,
    Phase2LevelPlotArtifacts,
    run_phase2_hormone_level_plots,
)


DEFAULT_CANDIDATE_FEATURES = [
    "prosody_egemaps_mfcc2_sma3_stddevNorm",
    "prosody_egemaps_logRelF0-H1-H2_sma3nz_amean",
    "prosody_egemaps_mfcc3_sma3_amean",
    "prosody_egemaps_F1bandwidth_sma3nz_stddevNorm",
    "prosody_egemaps_alphaRatioUV_sma3nz_amean",
]

DEFAULT_PLOT_SPECS = [
    LevelPlotSpec(
        hormone_columns=["e3g"],
        rolling_window_days=3,
        output_filename="prosody_3day_rolling_with_e3g_smoothed.png",
    ),
    LevelPlotSpec(
        hormone_columns=["e3g"],
        rolling_window_days=5,
        output_filename="prosody_5day_rolling_with_estrogen_smoothed.png",
    ),
    LevelPlotSpec(
        hormone_columns=["pdg"],
        rolling_window_days=3,
        output_filename="prosody_3day_rolling_with_pdg_smoothed.png",
    ),
    LevelPlotSpec(
        hormone_columns=["pdg"],
        rolling_window_days=5,
        output_filename="prosody_5day_rolling_with_pdg_smoothed.png",
    ),
    LevelPlotSpec(
        hormone_columns=["pdg", "e3g"],
        rolling_window_days=5,
        output_filename="prosody_5day_rolling_with_pdg_e3g_smoothed.png",
    ),
]


def main() -> None:
    defaults = default_paths()
    parser = argparse.ArgumentParser(description="Generate hormone level vs prosody overlay figures.")
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
        "--start-date",
        type=str,
        default="2026-01-16",
        help="Include data on/after this date.",
    )
    args = parser.parse_args()

    candidate_features = args.candidate_features or DEFAULT_CANDIDATE_FEATURES
    start_date = pd.Timestamp(args.start_date)

    output_paths = run_phase2_hormone_level_plots(
        merged_input_path=args.merged_input_path,
        artifacts=Phase2LevelPlotArtifacts(figures_output_dir=args.figures_output_dir),
        candidate_features=candidate_features,
        plot_specs=DEFAULT_PLOT_SPECS,
        start_date=start_date,
    )

    for output_path in output_paths:
        print(f"Wrote: {output_path}")


if __name__ == "__main__":
    main()
