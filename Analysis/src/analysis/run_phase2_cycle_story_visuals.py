"""CLI entrypoint for the professor-ready cycle story visual package."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .config import default_paths
from .phase2_cycle_story_visuals import CycleStoryArtifacts, run_phase2_cycle_story_visuals


def main() -> None:
    defaults = default_paths()
    parser = argparse.ArgumentParser(
        description="Generate cycle signal-vs-null visualizations and a presentation narrative."
    )
    parser.add_argument(
        "--merged-input-path",
        type=Path,
        default=defaults.processed_dir / "analysis_first_pass_merged.parquet",
    )
    parser.add_argument(
        "--stability-scan-path",
        type=Path,
        default=defaults.outputs_dir / "speech_feature_stability_periodicity_scan_cycle_relevant.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=defaults.outputs_dir / "professor_cycle_story",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default="2026-01-16",
        help="Include data on/after this date.",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default="2026-03-31",
        help="Include data on/before this date. Use empty string to disable.",
    )
    parser.add_argument(
        "--smoothing-window-days",
        type=int,
        default=7,
        help="Centered smoothing window for feature and hormone overlays.",
    )
    args = parser.parse_args()

    output_paths = run_phase2_cycle_story_visuals(
        merged_input_path=args.merged_input_path,
        stability_scan_path=args.stability_scan_path,
        artifacts=CycleStoryArtifacts(output_dir=args.output_dir),
        start_date=pd.Timestamp(args.start_date),
        end_date=pd.Timestamp(args.end_date) if args.end_date else None,
        smoothing_window_days=args.smoothing_window_days,
    )
    for output_path in output_paths:
        print(f"Wrote: {output_path}")


if __name__ == "__main__":
    main()
