from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

from .oura_appwrite import AppwriteOuraConfig, fetch_all_oura_documents


KEY_VOICE_FEATURES = [
    "egemaps_F0semitoneFrom27.5Hz_sma3nz_amean",
    "egemaps_jitterLocal_sma3nz_amean",
    "egemaps_shimmerLocaldB_sma3nz_amean",
    "egemaps_HNRdBACF_sma3nz_amean",
    "egemaps_F1frequency_sma3nz_amean",
    "egemaps_F2frequency_sma3nz_amean",
    "egemaps_F3frequency_sma3nz_amean",
]

VOICE_MIN_DURATION_SEC = 1.0
VOICE_MAX_DURATION_SEC = 120.0
F0_SEMITONE_COLUMN = "egemaps_F0semitoneFrom27.5Hz_sma3nz_amean"
VOICED_TASK_TYPES = {"vowel", "prosody"}


def _assert_columns(df: pd.DataFrame, required: Iterable[str], source_name: str) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"{source_name} is missing required columns: {missing}")


def _apply_voice_quality_filters(df: pd.DataFrame) -> pd.DataFrame:
    quality_mask = pd.Series(True, index=df.index)

    if "qc_audio_readable" in df.columns:
        quality_mask &= df["qc_audio_readable"] == True  # noqa: E712

    if "qc_clipping_detected" in df.columns:
        quality_mask &= df["qc_clipping_detected"] == False  # noqa: E712

    if "qc_duration_sec" in df.columns:
        df["qc_duration_sec"] = pd.to_numeric(df["qc_duration_sec"], errors="coerce")
        quality_mask &= df["qc_duration_sec"].between(VOICE_MIN_DURATION_SEC, VOICE_MAX_DURATION_SEC)

    if F0_SEMITONE_COLUMN in df.columns and "taskType" in df.columns:
        df[F0_SEMITONE_COLUMN] = pd.to_numeric(df[F0_SEMITONE_COLUMN], errors="coerce")
        zero_f0_on_voiced_task = df["taskType"].isin(VOICED_TASK_TYPES) & (df[F0_SEMITONE_COLUMN] == 0)
        quality_mask &= ~zero_f0_on_voiced_task

    return df[quality_mask].copy()


def _aggregate_voice_daily(df: pd.DataFrame) -> pd.DataFrame:
    feature_columns = [c for c in KEY_VOICE_FEATURES if c in df.columns]
    aggregate_spec: dict[str, tuple[str, str]] = {
        "voice_recording_count": ("date", "size"),
        "voice_task_count": ("taskType", "nunique"),
    }
    if "qc_duration_sec" in df.columns:
        aggregate_spec["voice_duration_sec_median"] = ("qc_duration_sec", "median")
    for feature in feature_columns:
        aggregate_spec[feature] = (feature, "median")

    daily = (
        df.groupby("date", as_index=False)
        .agg(**aggregate_spec)
        .sort_values("date")
        .reset_index(drop=True)
    )
    return daily


def load_voice_features(path: Path) -> pd.DataFrame:
    df = pd.read_parquet(path)
    _assert_columns(df, ["recordedDate", "taskType", "qc_opensmile_egemaps_success"], "voice features")

    df["date"] = pd.to_datetime(df["recordedDate"], errors="coerce").dt.normalize()
    df = df[df["date"].notna()].copy()
    df = df[df["qc_opensmile_egemaps_success"] == True].copy()  # noqa: E712
    df = _apply_voice_quality_filters(df)

    keep_cols = ["date", "taskType", "qc_duration_sec"] + [c for c in KEY_VOICE_FEATURES if c in df.columns]
    return _aggregate_voice_daily(df[keep_cols].copy())


def _normalize_oura(df: pd.DataFrame) -> pd.DataFrame:
    if "day" not in df.columns and "date" not in df.columns:
        raise ValueError("oura is missing required columns: ['day' or 'date']")

    date_source_col = "day" if "day" in df.columns else "date"
    df["date"] = pd.to_datetime(df[date_source_col], format="mixed", errors="coerce").dt.normalize()
    df = df[df["date"].notna()].copy()

    candidate_cols = [
        "date",
        "temperatureDeviation",
        "temperatureTrendDeviation",
        "averageHrv",
        "restingHeartRate",
        "sleepScore",
        "readinessScore",
        "activityScore",
        "tags",
    ]
    present_cols = [c for c in candidate_cols if c in df.columns]
    out = df[present_cols].copy()

    if "tags" in out.columns:
        out["tags"] = out["tags"].fillna("").astype(str)
    return out


def load_oura_from_appwrite(config: AppwriteOuraConfig, cache_path: Path | None = None) -> pd.DataFrame:
    documents = fetch_all_oura_documents(config)
    if not documents:
        raise ValueError("No Oura records returned from Appwrite")

    raw = pd.DataFrame.from_records(documents)
    normalized = _normalize_oura(raw)

    if cache_path is not None:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        normalized.to_parquet(cache_path, index=False)

    return normalized


def load_inito(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    _assert_columns(df, ["Date", "Cycle Day"], "inito")

    df["date"] = pd.to_datetime(df["Date"], format="mixed", errors="coerce").dt.normalize()
    df = df[df["date"].notna()].copy()

    rename_map = {
        "Cycle Day": "cycle_day",
        "E3G": "e3g",
        "PdG": "pdg",
        "FSH": "fsh",
        "LH": "lh",
    }
    df = df.rename(columns=rename_map)

    out_cols = ["date", "cycle_day", "e3g", "pdg", "fsh", "lh"]
    out = df[out_cols].copy()
    out = out.sort_values("date").drop_duplicates(subset=["date"], keep="last")
    return out

