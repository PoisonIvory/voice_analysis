from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Paths:
    root: Path
    voice_parquet: Path
    oura_parquet: Path
    inito_csv: Path
    processed_dir: Path
    outputs_dir: Path
    figures_dir: Path


def default_paths() -> Paths:
    root = Path(__file__).resolve().parents[1]
    return Paths(
        root=root,
        voice_parquet=Path("/Users/ivyhamilton/Decibelle/SpeechFeatureExtraction/data/processed/voice_features_v3_recordings.parquet"),
        oura_parquet=root / "data" / "raw" / "oura_daily_summaries.parquet",
        inito_csv=Path("/Users/ivyhamilton/Downloads/Hormone Tracking - hormones_data.csv"),
        processed_dir=root / "data" / "processed",
        outputs_dir=root / "outputs",
        figures_dir=root / "outputs" / "figures",
    )
