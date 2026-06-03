"""CLI entrypoint for one presentation-ready chart."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .config import default_paths
from .phase2_presentation_chart import PresentationChartArtifacts, run_phase2_presentation_chart


def main() -> None:
    defaults = default_paths()
    parser = argparse.ArgumentParser(description="Generate one polished presentation chart.")
    parser.add_argument(
        "--merged-input-path",
        type=Path,
        default=defaults.processed_dir / "analysis_first_pass_merged.parquet",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=defaults.figures_dir / "presentation_prosody_7day_rate_change_single_feature.png",
    )
    parser.add_argument(
        "--feature-column",
        type=str,
        default="prosody_egemaps_F1bandwidth_sma3nz_stddevNorm",
        help="Single prosody feature column to visualize.",
    )
    parser.add_argument(
        "--hormone-column",
        action="append",
        dest="hormone_columns",
        default=[],
        help="Hormone level columns to convert into per-day rate-of-change overlays.",
    )
    parser.add_argument(
        "--smoothing-window-days",
        type=int,
        default=7,
        help="Centered smoothing window in days.",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default="2026-01-16",
        help="Include data on/after this date.",
    )
    parser.add_argument(
        "--signal-mode",
        type=str,
        choices=["rate_change", "level"],
        default="rate_change",
        help="Use hormone rate-of-change or raw hormone level signal.",
    )
    parser.add_argument(
        "--gap-aware",
        action="store_true",
        help="Show chart with explicit data gaps instead of continuity-focused interpolation.",
    )
    args = parser.parse_args()

    hormone_columns = args.hormone_columns or ["e3g", "pdg"]
    output_path = run_phase2_presentation_chart(
        merged_input_path=args.merged_input_path,
        artifacts=PresentationChartArtifacts(output_path=args.output_path),
        feature_column=args.feature_column,
        hormone_columns=hormone_columns,
        smoothing_window_days=args.smoothing_window_days,
        start_date=pd.Timestamp(args.start_date),
        signal_mode=args.signal_mode,
        gap_aware=args.gap_aware,
    )
    print(f"Wrote: {output_path}")


if __name__ == "__main__":
    main()
