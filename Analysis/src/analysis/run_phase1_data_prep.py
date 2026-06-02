"""CLI entrypoint for Phase 1 data prep outputs."""

from __future__ import annotations

import argparse
from pathlib import Path

from .config import default_paths
from .phase1_data_prep import Phase1Artifacts, run_phase1_data_prep


EXPECTED_USER_ID = "6928d5ab0018cac7ae42"
DEFAULT_VOICE_DAILY_PATH = Path(
    "/Users/ivyhamilton/Decibelle/SpeechFeatureExtraction/data/processed/voice_features_v4_daily.parquet"
)
DEFAULT_VOICE_AUDIT_PATH = Path(
    "/Users/ivyhamilton/Decibelle/SpeechFeatureExtraction/data/processed/voice_features_v4_audit.parquet"
)
DEFAULT_VOICE_STAGING_PATH = Path(
    "/Users/ivyhamilton/Decibelle/SpeechFeatureExtraction/data/processed/voice_features_v4_recordings_staging.parquet"
)


def main() -> None:
    defaults = default_paths()
    parser = argparse.ArgumentParser(description="Run Phase 1 data prep and readiness reporting.")
    parser.add_argument("--voice-daily-path", type=Path, default=DEFAULT_VOICE_DAILY_PATH)
    parser.add_argument("--voice-audit-path", type=Path, default=DEFAULT_VOICE_AUDIT_PATH)
    parser.add_argument("--voice-staging-path", type=Path, default=DEFAULT_VOICE_STAGING_PATH)
    parser.add_argument("--oura-path", type=Path, default=defaults.oura_parquet)
    parser.add_argument("--inito-path", type=Path, default=defaults.inito_csv)
    parser.add_argument("--cycle-calendar-path", type=Path, default=defaults.cycle_calendar_parquet)
    parser.add_argument("--expected-user-id", type=str, default=EXPECTED_USER_ID)
    parser.add_argument(
        "--merged-output-path",
        type=Path,
        default=defaults.processed_dir / "analysis_first_pass_merged.parquet",
    )
    parser.add_argument(
        "--readiness-report-path",
        type=Path,
        default=defaults.outputs_dir / "phase1_readiness_report.md",
    )
    parser.add_argument(
        "--voice-validation-report-path",
        type=Path,
        default=defaults.outputs_dir / "voice_handoff_validation_report.md",
    )
    args = parser.parse_args()

    run_phase1_data_prep(
        voice_daily_path=args.voice_daily_path,
        voice_audit_path=args.voice_audit_path,
        voice_staging_path=args.voice_staging_path,
        oura_path=args.oura_path,
        inito_path=args.inito_path,
        cycle_calendar_path=args.cycle_calendar_path,
        expected_user_id=args.expected_user_id,
        artifacts=Phase1Artifacts(
            merged_output_path=args.merged_output_path,
            readiness_report_path=args.readiness_report_path,
            voice_validation_report_path=args.voice_validation_report_path,
        ),
    )

    print(f"Wrote: {args.voice_validation_report_path}")
    print(f"Wrote: {args.readiness_report_path}")
    print(f"Wrote: {args.merged_output_path}")


if __name__ == "__main__":
    main()
