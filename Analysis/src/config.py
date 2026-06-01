from dataclasses import dataclass
import os
from pathlib import Path

from .oura_appwrite import AppwriteOuraConfig


@dataclass(frozen=True)
class Paths:
    root: Path
    voice_parquet: Path
    oura_cache_parquet: Path
    inito_csv: Path
    raw_dir: Path
    processed_dir: Path
    outputs_dir: Path
    figures_dir: Path


def default_paths() -> Paths:
    root = Path(__file__).resolve().parents[1]
    return Paths(
        root=root,
        voice_parquet=Path("/Users/ivyhamilton/Decibelle/SpeechFeatureExtraction/data/processed/voice_features_v3_recordings.parquet"),
        oura_cache_parquet=root / "data" / "raw" / "oura_daily_summaries.parquet",
        inito_csv=Path("/Users/ivyhamilton/Downloads/Hormone Tracking - hormones_data.csv"),
        raw_dir=root / "data" / "raw",
        processed_dir=root / "data" / "processed",
        outputs_dir=root / "outputs",
        figures_dir=root / "outputs" / "figures",
    )


def appwrite_oura_config_from_env() -> AppwriteOuraConfig:
    api_key = os.getenv("APPWRITE_API_KEY")
    if not api_key:
        raise ValueError("APPWRITE_API_KEY is required to fetch Oura data from Appwrite")

    user_id = os.getenv("APPWRITE_USER_ID", "6928d5ab0018cac7ae42")
    return AppwriteOuraConfig(
        endpoint=os.getenv("APPWRITE_ENDPOINT", "https://sfo.cloud.appwrite.io/v1"),
        project_id=os.getenv("APPWRITE_PROJECT_ID", "68ca57d1000cb6324eca"),
        database_id=os.getenv("APPWRITE_DATABASE_ID", "period_tracker_db"),
        collection_id=os.getenv("APPWRITE_OURA_COLLECTION_ID", "oura_daily_summaries"),
        user_id=user_id,
        api_key=api_key,
    )
