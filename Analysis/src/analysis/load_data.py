"""Loads and normalizes voice, Oura, and Inito inputs for analysis."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd


VOICE_FEATURE_PREFIX = "egemaps_"

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
    feature_columns = [c for c in df.columns if c.startswith(VOICE_FEATURE_PREFIX)]
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

    keep_cols = ["date", "taskType", "qc_duration_sec"] + [
        c for c in df.columns if c.startswith(VOICE_FEATURE_PREFIX)
    ]
    return _aggregate_voice_daily(df[keep_cols].copy())


def load_voice_daily_handoff(path: Path, expected_user_id: str | None = None) -> pd.DataFrame:
    df = pd.read_parquet(path).copy()
    _assert_columns(df, ["userId", "dayUtc"], "voice v4 daily handoff")

    out = df.copy()
    out["date"] = pd.to_datetime(out["dayUtc"], format="mixed", errors="coerce").dt.normalize()
    out = out[out["date"].notna()].copy()
    out["userId"] = out["userId"].astype(str)
    out = out.sort_values(["userId", "date"]).reset_index(drop=True)

    unique_users = sorted(out["userId"].dropna().unique().tolist())
    if len(unique_users) != 1:
        raise ValueError(f"voice v4 daily handoff must contain exactly one userId; found {len(unique_users)}")

    if expected_user_id is not None and unique_users[0] != expected_user_id:
        raise ValueError(
            f"voice v4 daily handoff userId mismatch: expected {expected_user_id}, found {unique_users[0]}"
        )

    duplicate_rows = int(out.duplicated(subset=["userId", "date"], keep=False).sum())
    if duplicate_rows > 0:
        raise ValueError(f"voice v4 daily handoff has duplicate (userId, dayUtc) rows: {duplicate_rows}")

    return out


def _normalize_oura(df: pd.DataFrame) -> pd.DataFrame:
    if "day" not in df.columns and "date" not in df.columns:
        raise ValueError("oura is missing required columns: ['day' or 'date']")

    date_source_col = "day" if "day" in df.columns else "date"
    df["date"] = pd.to_datetime(df[date_source_col], format="mixed", errors="coerce").dt.normalize()
    df = df[df["date"].notna()].copy()

    out = df.copy()
    return out


def load_oura_from_parquet(path: Path) -> pd.DataFrame:
    raw = pd.read_parquet(path)
    normalized = _normalize_oura(raw)
    return normalized


def load_cycle_calendar(path: Path) -> pd.DataFrame:
    df = pd.read_parquet(path)
    _assert_columns(
        df,
        [
            "date",
            "cycle_start_date",
            "next_cycle_start_date",
            "cycle_day",
            "cycle_week",
            "phase_label",
            "days_to_next_start",
            "cycle_source",
        ],
        "cycle calendar",
    )

    out = df.copy()
    out["date"] = pd.to_datetime(out["date"], format="mixed", errors="coerce").dt.normalize()
    out["cycle_start_date"] = pd.to_datetime(out["cycle_start_date"], format="mixed", errors="coerce").dt.normalize()
    out["next_cycle_start_date"] = pd.to_datetime(
        out["next_cycle_start_date"], format="mixed", errors="coerce"
    ).dt.normalize()
    out["cycle_day"] = pd.to_numeric(out["cycle_day"], errors="coerce").astype("Int64")
    out["days_to_next_start"] = pd.to_numeric(out["days_to_next_start"], errors="coerce").astype("Int64")
    out["phase_label"] = out["phase_label"].astype("string")
    out["cycle_week"] = out["cycle_week"].astype("string")
    out["cycle_source"] = out["cycle_source"].astype("string")
    out = out[out["date"].notna()].sort_values("date").drop_duplicates(subset=["date"], keep="last")
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
