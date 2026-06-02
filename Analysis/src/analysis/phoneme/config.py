"""Filesystem paths for the phoneme-prosody study (kept isolated under outputs/phoneme)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PhonemePaths:
    root: Path
    phoneme_parquet: Path
    cycle_calendar_parquet: Path
    hormone_levels_parquet: Path
    hormone_change_parquet: Path
    whole_recording_daily_parquet: Path
    figures_dir: Path
    tables_dir: Path


def default_paths() -> PhonemePaths:
    root = Path(__file__).resolve().parents[3]
    speech_repo = Path("/Users/ivyhamilton/Decibelle/SpeechFeatureExtraction")
    return PhonemePaths(
        root=root,
        phoneme_parquet=speech_repo
        / "data/experimental/phoneme_prosody/prosody_phoneme_features.parquet",
        cycle_calendar_parquet=root / "data/processed/cycle_calendar_daily.parquet",
        hormone_levels_parquet=root / "data/processed/hormone_daily_levels.parquet",
        hormone_change_parquet=root / "data/processed/hormone_daily_rate_of_change.parquet",
        whole_recording_daily_parquet=root / "data/processed/analysis_daily.parquet",
        figures_dir=root / "outputs/phoneme/figures",
        tables_dir=root / "outputs/phoneme/tables",
    )
