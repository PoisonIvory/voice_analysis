from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd


KEY_VOICE_FEATURES = [
    "egemaps_F0semitoneFrom27.5Hz_sma3nz_amean",
    "egemaps_jitterLocal_sma3nz_amean",
    "egemaps_shimmerLocaldB_sma3nz_amean",
    "egemaps_HNRdBACF_sma3nz_amean",
    "egemaps_F1frequency_sma3nz_amean",
    "egemaps_F2frequency_sma3nz_amean",
    "egemaps_F3frequency_sma3nz_amean",
]


def _assert_columns(df: pd.DataFrame, required: Iterable[str], source_name: str) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"{source_name} is missing required columns: {missing}")


def load_voice_features(path: Path) -> pd.DataFrame:
    df = pd.read_parquet(path)
    _assert_columns(df, ["recordedDate", "taskType", "qc_opensmile_egemaps_success"], "voice features")

    df["date"] = pd.to_datetime(df["recordedDate"], errors="coerce").dt.normalize()
    df = df[df["date"].notna()].copy()
    df = df[df["qc_opensmile_egemaps_success"] == True].copy()  # noqa: E712

    keep_cols = ["date", "taskType", "qc_duration_sec", "qc_clipping_detected"] + [
        c for c in KEY_VOICE_FEATURES if c in df.columns
    ]
    return df[keep_cols].copy()


def load_oura(path: Path) -> pd.DataFrame:
    df = pd.read_parquet(path)
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

