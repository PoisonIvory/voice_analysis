"""Filesystem paths for the HuBERT phonological-subspace study.

Kept isolated under outputs/hubert, mirroring src/analysis/phoneme/config.py.
The per-recording d-prime tables live in the sibling SpeechFeatureExtraction
repo (one per frozen SSL backbone, all computed over the same MFA boundaries).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# The HuBERT-base table is the primary analysis; the other two backbones are an
# architecture-robustness check (same 768-d, English LS960, different SSL
# objective). Insertion order is the reporting order.
PRIMARY_BACKBONE = "hubert-base"


@dataclass(frozen=True)
class HubertPaths:
    root: Path
    dprime_parquets: dict[str, Path]
    cycle_calendar_parquet: Path
    hormone_levels_parquet: Path
    hormone_change_parquet: Path
    figures_dir: Path
    tables_dir: Path


def default_paths() -> HubertPaths:
    root = Path(__file__).resolve().parents[3]
    speech_repo = Path("/Users/ivyhamilton/Decibelle/SpeechFeatureExtraction")
    dprime_dir = speech_repo / "data/experimental/phoneme_prosody"
    return HubertPaths(
        root=root,
        dprime_parquets={
            PRIMARY_BACKBONE: dprime_dir / "hubert_dprime_by_recording.parquet",
            "wavlm-base": dprime_dir / "hubert_dprime__wavlm-base.parquet",
            "wav2vec2-base": dprime_dir / "hubert_dprime__wav2vec2-base.parquet",
        },
        cycle_calendar_parquet=root / "data/processed/cycle_calendar_daily.parquet",
        hormone_levels_parquet=root / "data/processed/hormone_daily_levels.parquet",
        hormone_change_parquet=root / "data/processed/hormone_daily_rate_of_change.parquet",
        figures_dir=root / "outputs/hubert/figures",
        tables_dir=root / "outputs/hubert/tables",
    )
